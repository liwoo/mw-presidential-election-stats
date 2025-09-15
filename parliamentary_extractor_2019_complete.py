#!/usr/bin/env python3
"""
Complete 2019 Parliamentary Vote Extractor
Extracts parliamentary voting data from polling station level data
and aggregates to constituency level following the 2020 structure format.
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

@dataclass
class Candidate:
    """Represents a candidate with votes"""
    name: str
    affiliation: str
    votes: int

class Parliamentary2019CompleteExtractor:
    """Complete extractor for 2019 parliamentary data"""
    
    def __init__(self, metadata_validator):
        self.validator = metadata_validator
        self.constituency_data = defaultdict(lambda: defaultdict(int))
        self.constituency_info = {}
        self.current_context = {}
        
    def extract_from_text(self, text_content: str) -> Dict[str, any]:
        """Extract 2019 parliamentary data from text content"""
        lines = [line.strip() for line in text_content.split('\n')]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines and headers
            if not line or line in ['Region Name District Name Constituency Name Ward Name Centre Name Station', 'Number Candidate Names Affiliation Votes']:
                i += 1
                continue
            
            # Check for context reconstruction
            context_result = self._try_reconstruct_context(lines, i)
            if context_result:
                self.current_context, i = context_result
                continue
            
            # Parse candidate data if we have context
            if self.current_context:
                candidate_result = self._parse_candidate_data(lines, i)
                if candidate_result:
                    candidates, i = candidate_result
                    self._process_candidates(candidates)
                    continue
            
            i += 1
        
        return self._aggregate_to_districts()
    
    def _try_reconstruct_context(self, lines: List[str], start_idx: int) -> Optional[Tuple[Dict, int]]:
        """Try to reconstruct context from multiple lines"""
        
        # Look for regional context patterns
        region_patterns = [
            (r'(Northern|Central|Southern)\s*$', 'region'),
            (r'Region\s+(\d+)\s*([A-Za-z]+)\s+(\d+)', 'district_info'),
            (r'([A-Za-z\s]+)\s+(\d{3})', 'constituency_info')
        ]
        
        # Try to find region
        if start_idx < len(lines):
            current_line = lines[start_idx]
            
            # Check for region line
            region_match = re.match(r'(Northern|Central|Southern)\s*$', current_line)
            if region_match and start_idx + 1 < len(lines):
                region = region_match.group(1)
                next_line = lines[start_idx + 1]
                
                # Parse next line for district and constituency info
                # Format: "Region 1Chitipa 01 Chitipa East 001 Iponjola 0001 Chanya School 01010 Station 1"
                district_match = re.search(r'Region\s+\d+\s*([A-Za-z]+)\s+(\d+)\s+([A-Za-z\s]+)\s+(\d{3})', next_line)
                if district_match:
                    district_name = district_match.group(1)
                    district_num = district_match.group(2)
                    constituency_name = district_match.group(3).strip()
                    constituency_code = district_match.group(4)
                    
                    context = {
                        'region': region,
                        'district': district_name,
                        'constituency': constituency_name,
                        'constituency_code': constituency_code
                    }
                    
                    return context, start_idx + 2
        
        return None
    
    def _parse_candidate_data(self, lines: List[str], start_idx: int) -> Optional[Tuple[List[Candidate], int]]:
        """Parse candidate data block"""
        candidates = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop at context change or totals
            if (not line or 
                re.match(r'(Northern|Central|Southern)', line) or
                line.startswith('Total No. of Valid Votes') or
                line.startswith('Total No. of Null and Void') or
                line.startswith('Total No. of Votes') or
                line.startswith('Number of Registered') or
                line.startswith('Voter Turnout') or
                'Region' in line):
                break
            
            # Try to parse as candidate line
            candidate = self._parse_candidate_line(line)
            if candidate:
                candidates.append(candidate)
            
            i += 1
        
        return (candidates, i) if candidates else None
    
    def _parse_candidate_line(self, line: str) -> Optional[Candidate]:
        """Parse a single candidate line"""
        # Remove common noise
        if (line.startswith(('Station', 'School')) or 
            re.match(r'^\d+Station\s*\d*$', line) or
            'Parliamentary Elections Results' in line):
            return None
        
        # Pattern: NAME AFFILIATION VOTES
        # Handle variations like "CHIZAMSOKA OLIVER MULWAFU DPP 127"
        parts = line.split()
        
        if len(parts) >= 3:
            # Try to find the vote number (should be last numeric part)
            votes_str = None
            party = None
            
            for i in range(len(parts) - 1, -1, -1):
                if re.match(r'^\d{1,6}$', parts[i]):  # Found votes
                    votes_str = parts[i]
                    if i > 0:  # Party should be before votes
                        party = parts[i - 1]
                        name = ' '.join(parts[:i-1]) if i > 1 else parts[0]
                        break
            
            if votes_str and party and len(name.strip()) > 0:
                try:
                    votes = int(votes_str)
                    
                    # Clean up party code
                    if party in ['INDEPENDENT', 'INDEP']:
                        party = 'IND'
                    
                    # Validate name (should have letters)
                    if re.search(r'[A-Za-z]', name) and votes >= 0:
                        return Candidate(
                            name=name.strip(),
                            affiliation=party,
                            votes=votes
                        )
                except ValueError:
                    pass
        
        return None
    
    def _process_candidates(self, candidates: List[Candidate]):
        """Process candidates for current context"""
        if not self.current_context:
            return
        
        const_name = self.current_context.get('constituency', 'Unknown')
        district_name = self.current_context.get('district', 'Unknown')
        region = self.current_context.get('region', 'Unknown')
        
        # Store constituency info
        if const_name not in self.constituency_info:
            self.constituency_info[const_name] = {
                'district': district_name,
                'region': region
            }
        
        # Aggregate candidate votes
        for candidate in candidates:
            candidate_key = f"{candidate.name}|{candidate.affiliation}"
            self.constituency_data[const_name][candidate_key] += candidate.votes
    
    def _aggregate_to_districts(self) -> Dict[str, any]:
        """Aggregate data to district level following the 2020 structure"""
        from parliamentary_extractor import District, Constituency, Candidate as ExtractorCandidate
        
        districts = {}
        
        for const_name, candidates_data in self.constituency_data.items():
            if not candidates_data:  # Skip empty constituencies
                continue
                
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
                district_info = self.validator.district_lookup.get(district_code, {})
                districts[district_code] = District(
                    code=district_code,
                    name=district_info.get('name', district_name),
                    region=const_info.get('region', 'Unknown'),
                    constituencies=[]
                )
            
            # Create candidates list
            candidates = []
            for candidate_key, votes in candidates_data.items():
                if '|' not in candidate_key:
                    continue
                    
                name, affiliation = candidate_key.split('|', 1)
                candidate_code = self._generate_candidate_code(name)
                
                candidates.append(ExtractorCandidate(
                    name=name,
                    candidate_code=candidate_code,
                    party_code=affiliation,
                    votes=votes
                ))
            
            # Only add constituency if it has candidates
            if candidates:
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
        
        # Direct match
        for code, district_info in self.validator.district_lookup.items():
            if district_info['name'].lower() == district_name_clean:
                return code
        
        # Partial matching for common variations
        name_mappings = {
            'chitipa': 'CT',
            'karonga': 'KR', 
            'rumphi': 'RU',
            'mzimba': 'MZ',
            'nkhatabay': 'NB',
            'nkhata bay': 'NB',
            'likoma': 'LK',
            'nkhotakota': 'NK',
            'kasungu': 'KS',
            'ntchisi': 'NI',
            'dowa': 'DO',
            'mchinji': 'MC',
            'salima': 'SA',
            'lilongwe': 'LI',
            'dedza': 'DE',
            'ntcheu': 'NU',
            'mangochi': 'MG',
            'machinga': 'MH',
            'balaka': 'BA',
            'zomba': 'ZO',
            'neno': 'NE',
            'blantyre': 'BL',
            'mwanza': 'MW',
            'phalombe': 'PH',
            'chiradzulu': 'CR',
            'mulanje': 'MU',
            'nsanje': 'NS',
            'thyolo': 'TH',
            'chikwawa': 'CK',
            'mzuzu': 'ZU'
        }
        
        return name_mappings.get(district_name_clean)
    
    def _find_constituency_code(self, constituency_name: str) -> Optional[str]:
        """Find constituency code from constituency name"""
        const_name_clean = constituency_name.strip().lower()
        
        # Direct match
        for code, const_info in self.validator.constituency_lookup.items():
            if const_info['name'].lower() == const_name_clean:
                return code
        
        # Partial matching
        for code, const_info in self.validator.constituency_lookup.items():
            const_meta_name = const_info['name'].lower()
            # Check if either name contains the other
            if (const_name_clean in const_meta_name or 
                const_meta_name in const_name_clean or
                self._names_similar(const_name_clean, const_meta_name)):
                return code
        
        return None
    
    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two constituency names are similar"""
        # Remove common words and compare core parts
        common_words = {'constituency', 'north', 'south', 'east', 'west', 'central'}
        
        words1 = {w for w in name1.split() if w not in common_words}
        words2 = {w for w in name2.split() if w not in common_words}
        
        # Check for significant overlap
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        return overlap >= min(len(words1), len(words2)) * 0.6
    
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
    """Main function for 2019 extraction"""
    from parliamentary_extractor import MetadataValidator, JSONGenerator, TestFramework
    
    base_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats")
    metadata_path = base_path / "metadata"
    data_path = base_path / "data"
    
    # Initialize components
    print("Initializing complete 2019 parliamentary extractor...")
    validator = MetadataValidator(str(metadata_path))
    extractor = Parliamentary2019CompleteExtractor(validator)
    json_generator = JSONGenerator(validator)
    test_framework = TestFramework(validator)
    
    # Process 2019 data
    text_file = data_path / "2019-Parliamentary-results.pdf.txt"
    
    if text_file.exists():
        print(f"Processing 2019 parliamentary data from {text_file.name}...")
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Extracting and aggregating polling station data...")
        extracted_data = extractor.extract_from_text(content)
        
        if extracted_data:
            print(f"✅ Extracted 2019 data for {len(extracted_data)} districts")
            
            # Show constituency breakdown
            total_constituencies = sum(len(d.constituencies) for d in extracted_data.values())
            total_candidates = sum(len(c.candidates) for d in extracted_data.values() for c in d.constituencies)
            total_votes = sum(candidate.votes for d in extracted_data.values() for c in d.constituencies for candidate in c.candidates)
            
            print(f"📊 Statistics:")
            print(f"   - Districts: {len(extracted_data)}")
            print(f"   - Constituencies: {total_constituencies}")
            print(f"   - Candidates: {total_candidates}")
            print(f"   - Total Votes: {total_votes:,}")
            
            # Run tests
            print("\n🔍 Running validation tests...")
            test_framework.test_data_integrity(extracted_data)
            test_framework.print_test_results()
            
            # Generate JSON files
            print(f"\n📁 Generating JSON files...")
            output_dir = base_path / "2019" / "results" / "parliamentary"
            for district in extracted_data.values():
                json_generator.generate_district_json(district, str(output_dir))
                
            print(f"\n🎉 2019 Parliamentary extraction completed successfully!")
            print(f"Generated {len(extracted_data)} district files in: {output_dir}")
        else:
            print("❌ No data extracted from 2019 file")
    else:
        print(f"❌ 2019 data file not found: {text_file}")

if __name__ == "__main__":
    main()