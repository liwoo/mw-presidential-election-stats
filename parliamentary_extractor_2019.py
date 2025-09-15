#!/usr/bin/env python3
"""
2019 Parliamentary Vote Extractor
Extracts parliamentary voting data from polling station level data
and aggregates to constituency level following the 2020 structure format.
"""

import json
import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

@dataclass
class PollingStation:
    """Represents a polling station with its context"""
    region: str
    district: str
    constituency: str
    ward: str
    centre: str
    station: str
    candidates: List['Candidate'] = None
    
    def __post_init__(self):
        if self.candidates is None:
            self.candidates = []

@dataclass
class Candidate:
    """Represents a candidate with votes"""
    name: str
    affiliation: str
    votes: int

class Parliamentary2019Extractor:
    """Extracts 2019 parliamentary data from polling station format"""
    
    def __init__(self, metadata_validator):
        self.validator = metadata_validator
        self.polling_stations = []
        self.constituency_data = defaultdict(lambda: defaultdict(int))
        self.constituency_info = {}
        
    def extract_from_text(self, text_content: str) -> Dict[str, any]:
        """Extract 2019 parliamentary data from text content"""
        lines = text_content.split('\n')
        
        current_context = {}
        current_candidates = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this is a header with context information
            if self._is_context_line(line):
                context_info = self._parse_context_line(line, lines, i)
                if context_info:
                    current_context = context_info[0]
                    i = context_info[1]
                else:
                    i += 1
                continue
            
            # Check if this is a candidate line
            candidate_info = self._parse_candidate_line(line)
            if candidate_info and current_context:
                current_candidates.append(candidate_info)
                i += 1
                continue
            
            # Check if this is a totals line (end of polling station)
            if line.startswith('Total No. of Valid Votes') and current_context and current_candidates:
                # Process this polling station
                polling_station = PollingStation(
                    region=current_context.get('region', ''),
                    district=current_context.get('district', ''),
                    constituency=current_context.get('constituency', ''),
                    ward=current_context.get('ward', ''),
                    centre=current_context.get('centre', ''),
                    station=current_context.get('station', ''),
                    candidates=current_candidates
                )
                
                self._process_polling_station(polling_station)
                current_candidates = []
                i += 1
                continue
            
            i += 1
        
        return self._aggregate_to_districts()
    
    def _is_context_line(self, line: str) -> bool:
        """Check if line contains context information"""
        # Skip header lines
        if 'Region Name' in line or 'Candidate Names' in line:
            return False
            
        # Look for actual context lines with region, district, constituency pattern
        context_patterns = [
            r'(Northern|Central|Southern)\s+Region.*\d+\s+[A-Za-z\s]+\d+\s+[A-Za-z\s]+\d+',
            r'(Northern|Central|Southern).*\d+[A-Za-z\s]+\d+.*\d+'
        ]
        
        return any(re.search(pattern, line) for pattern in context_patterns)
    
    def _parse_context_line(self, line: str, lines: List[str], index: int) -> Optional[tuple]:
        """Parse context information from header lines"""
        # Skip the header line
        if 'Region Name' in line or 'Candidate Names' in line:
            return None
        
        # Parse context lines like: "Northern Region 1Chitipa 01 Chitipa East 001 Iponjola 0001"
        # Pattern: Region + numbers/district name + constituency code + constituency name + ward
        
        # Extract using regex patterns
        region_match = re.search(r'(Northern|Central|Southern)', line)
        if not region_match:
            return None
        
        region = region_match.group(1)
        
        # Look for district code and name pattern
        district_match = re.search(r'\d+\s*([A-Za-z]+)\s+(\d+)', line)
        if district_match:
            district_name = district_match.group(1)
            district_num = district_match.group(2)
        else:
            return None
        
        # Look for constituency pattern
        const_match = re.search(r'([A-Za-z\s]+)\s+(\d{3})\s+([A-Za-z\s]+)\s+(\d{4})', line)
        if const_match:
            const_name = const_match.group(1).strip()
            const_code = const_match.group(2)
            ward_name = const_match.group(3).strip()
            ward_code = const_match.group(4)
        else:
            # Try simpler pattern
            simple_match = re.search(r'([A-Za-z\s]+)\s+(\d{3})', line)
            if simple_match:
                const_name = simple_match.group(1).strip()
                const_code = simple_match.group(2)
                ward_name = ''
                ward_code = ''
            else:
                return None
        
        context = {
            'region': region,
            'district': district_name,
            'constituency': const_name,
            'ward': ward_name,
            'centre': '',
            'station': ''
        }
        
        return context, index + 1
    
    def _parse_candidate_line(self, line: str) -> Optional[Candidate]:
        """Parse candidate information from a line"""
        # Try to match candidate line pattern
        # Format: NAME AFFILIATION VOTES
        parts = line.strip().split()
        
        if len(parts) >= 3:
            try:
                votes = int(parts[-1])
                affiliation = parts[-2]
                name = ' '.join(parts[:-2])
                
                # Clean up affiliation
                if affiliation in ['INDEPENDENT', 'INDEP']:
                    affiliation = 'IND'
                
                return Candidate(name=name, affiliation=affiliation, votes=votes)
            except ValueError:
                pass
        
        return None
    
    def _process_polling_station(self, station: PollingStation):
        """Process a polling station and add to aggregated data"""
        const_key = station.constituency.strip()
        district_key = station.district.strip()
        
        # Store constituency info
        if const_key not in self.constituency_info:
            self.constituency_info[const_key] = {
                'district': district_key,
                'region': station.region
            }
        
        # Aggregate candidate votes by constituency
        for candidate in station.candidates:
            candidate_key = f"{candidate.name}|{candidate.affiliation}"
            self.constituency_data[const_key][candidate_key] += candidate.votes
    
    def _aggregate_to_districts(self) -> Dict[str, any]:
        """Aggregate data to district level following the 2020 structure"""
        from parliamentary_extractor import District, Constituency, Candidate as ExtractorCandidate
        
        districts = {}
        
        for const_name, candidates_data in self.constituency_data.items():
            const_info = self.constituency_info.get(const_name, {})
            district_name = const_info.get('district', 'Unknown')
            
            # Find district code
            district_code = self._find_district_code(district_name)
            if not district_code:
                print(f"Warning: Could not find district code for {district_name}")
                continue
            
            # Find constituency code
            constituency_code = self._find_constituency_code(const_name)
            if not constituency_code:
                print(f"Warning: Could not find constituency code for {const_name}")
                continue
            
            # Create district if not exists
            if district_code not in districts:
                districts[district_code] = District(
                    code=district_code,
                    name=district_name,
                    region=const_info.get('region', 'Unknown'),
                    constituencies=[]
                )
            
            # Create candidates list
            candidates = []
            for candidate_key, votes in candidates_data.items():
                name, affiliation = candidate_key.split('|')
                candidate_code = self._generate_candidate_code(name)
                
                candidates.append(ExtractorCandidate(
                    name=name,
                    candidate_code=candidate_code,
                    party_code=affiliation,
                    votes=votes
                ))
            
            # Create constituency
            constituency = Constituency(
                code=constituency_code,
                name=const_name,
                candidates=candidates
            )
            
            districts[district_code].constituencies.append(constituency)
        
        return districts
    
    def _find_district_code(self, district_name: str) -> Optional[str]:
        """Find district code from district name"""
        district_name_clean = district_name.strip().lower()
        
        for code, district_info in self.validator.district_lookup.items():
            if district_info['name'].lower() == district_name_clean:
                return code
        
        # Try partial matching
        for code, district_info in self.validator.district_lookup.items():
            if district_name_clean in district_info['name'].lower() or district_info['name'].lower() in district_name_clean:
                return code
        
        return None
    
    def _find_constituency_code(self, constituency_name: str) -> Optional[str]:
        """Find constituency code from constituency name"""
        const_name_clean = constituency_name.strip().lower()
        
        for code, const_info in self.validator.constituency_lookup.items():
            if const_info['name'].lower() == const_name_clean:
                return code
        
        # Try partial matching
        for code, const_info in self.validator.constituency_lookup.items():
            if const_name_clean in const_info['name'].lower() or const_info['name'].lower() in const_name_clean:
                return code
        
        return None
    
    def _generate_candidate_code(self, name: str) -> str:
        """Generate a candidate code from the candidate name"""
        # Take first 6 characters of surname (last word) in uppercase
        parts = name.split()
        if len(parts) > 1:
            surname = parts[-1].upper()[:6]
        else:
            surname = name.upper()[:6]
        
        return surname.ljust(6, 'X')  # Pad with X if needed

def main():
    """Main function to test 2019 extraction"""
    from parliamentary_extractor import MetadataValidator, JSONGenerator, TestFramework
    
    base_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats")
    metadata_path = base_path / "metadata"
    data_path = base_path / "data"
    
    # Initialize components
    print("Initializing 2019 parliamentary extractor...")
    validator = MetadataValidator(str(metadata_path))
    extractor = Parliamentary2019Extractor(validator)
    json_generator = JSONGenerator(validator)
    test_framework = TestFramework(validator)
    
    # Process 2019 data
    text_file = data_path / "2019-Parliamentary-results.pdf.txt"
    
    if text_file.exists():
        print(f"Processing 2019 parliamentary data from {text_file.name}...")
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extracted_data = extractor.extract_from_text(content)
        
        if extracted_data:
            print(f"Extracted 2019 data for {len(extracted_data)} districts")
            
            # Run tests
            test_framework.test_data_integrity(extracted_data)
            test_framework.print_test_results()
            
            # Generate JSON files
            output_dir = base_path / "2019" / "results" / "parliamentary"
            for district in extracted_data.values():
                json_generator.generate_district_json(district, str(output_dir))
        else:
            print("No data extracted from 2019 file")
    else:
        print(f"2019 data file not found: {text_file}")

if __name__ == "__main__":
    main()