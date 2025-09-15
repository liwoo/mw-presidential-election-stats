#!/usr/bin/env python3
"""
Robust 2019 Parliamentary Vote Extractor
Handles complex PDF extraction patterns and generates all district files
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

class Parliamentary2019RobustExtractor:
    """Robust extractor for 2019 parliamentary data"""
    
    def __init__(self, metadata_validator):
        self.validator = metadata_validator
        self.constituency_data = defaultdict(lambda: defaultdict(int))
        self.constituency_info = {}
        self.current_context = {}
        
    def extract_from_text(self, text_content: str) -> Dict[str, any]:
        """Extract 2019 parliamentary data from text content"""
        lines = [line.strip() for line in text_content.split('\n')]
        
        print(f"Processing {len(lines)} lines of data...")
        
        i = 0
        processed_contexts = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines and headers
            if not line or 'Region Name' in line or 'Candidate Names' in line:
                i += 1
                continue
            
            # Look for embedded context in various line formats
            context_result = self._extract_context_from_line(line)
            if context_result:
                self.current_context = context_result
                processed_contexts += 1
                if processed_contexts % 50 == 0:
                    print(f"Processed {processed_contexts} contexts...")
            
            # Parse candidate data if we have context
            if self.current_context:
                candidate = self._parse_candidate_line(line)
                if candidate:
                    self._process_candidate(candidate)
            
            i += 1
        
        print(f"Found {len(self.constituency_data)} constituencies")
        print(f"Processing into districts...")
        
        return self._aggregate_to_districts()
    
    def _extract_context_from_line(self, line: str) -> Optional[Dict]:
        """Extract context from various line formats"""
        
        # Pattern 1: Embedded in total votes line
        # "Total No. of Votes  594Chitipa Central 003 Yamba 0006 Chimwemwe School"
        total_votes_pattern = r'Total No. of Votes\s+\d+([A-Za-z\s]+)\s+(\d{3})\s+([A-Za-z\s]+)\s+(\d{4})'
        match = re.search(total_votes_pattern, line)
        if match:
            constituency_name = match.group(1).strip()
            constituency_code = match.group(2)
            ward_name = match.group(3).strip()
            ward_code = match.group(4)
            
            # Extract district from constituency name
            district_name = self._extract_district_from_constituency(constituency_name)
            
            return {
                'constituency': constituency_name,
                'constituency_code': constituency_code,
                'district': district_name,
                'ward': ward_name,
                'region': self._infer_region(district_name)
            }
        
        # Pattern 2: Standard context line format
        # "Region 1Chitipa 01 Chitipa East 001 Iponjola 0001"
        standard_pattern = r'Region\s+\d+\s*([A-Za-z]+)\s+(\d+)\s+([A-Za-z\s]+)\s+(\d{3})'
        match = re.search(standard_pattern, line)
        if match:
            district_name = match.group(1)
            district_num = match.group(2)
            constituency_name = match.group(3).strip()
            constituency_code = match.group(4)
            
            return {
                'constituency': constituency_name,
                'constituency_code': constituency_code,
                'district': district_name,
                'region': self._infer_region(district_name)
            }
        
        # Pattern 3: Direct constituency pattern
        # "Chitipa Central 003 Yamba 0006"
        direct_pattern = r'^([A-Za-z\s]+)\s+(\d{3})\s+([A-Za-z\s]+)\s+(\d{4})'
        match = re.search(direct_pattern, line)
        if match:
            constituency_name = match.group(1).strip()
            constituency_code = match.group(2)
            ward_name = match.group(3).strip()
            ward_code = match.group(4)
            
            district_name = self._extract_district_from_constituency(constituency_name)
            
            return {
                'constituency': constituency_name,
                'constituency_code': constituency_code,
                'district': district_name,
                'ward': ward_name,
                'region': self._infer_region(district_name)
            }
        
        return None
    
    def _extract_district_from_constituency(self, constituency_name: str) -> str:
        """Extract district name from constituency name"""
        # Common patterns: "Chitipa Central", "Karonga North", "Lilongwe City Centre"
        words = constituency_name.split()
        if words:
            # Usually the first word is the district
            return words[0]
        return "Unknown"
    
    def _infer_region(self, district_name: str) -> str:
        """Infer region from district name"""
        district_lower = district_name.lower()
        
        northern_districts = {'chitipa', 'karonga', 'rumphi', 'mzimba', 'nkhatabay', 'nkhata bay', 'likoma', 'mzuzu'}
        central_districts = {'nkhotakota', 'kasungu', 'ntchisi', 'dowa', 'mchinji', 'salima', 'lilongwe', 'dedza'}
        southern_districts = {'ntcheu', 'mangochi', 'machinga', 'balaka', 'zomba', 'neno', 'blantyre', 'mwanza', 'phalombe', 'chiradzulu', 'mulanje', 'nsanje', 'thyolo', 'chikwawa'}
        
        if district_lower in northern_districts:
            return 'Northern'
        elif district_lower in central_districts:
            return 'Central'
        elif district_lower in southern_districts:
            return 'Southern'
        else:
            return 'Unknown'
    
    def _parse_candidate_line(self, line: str) -> Optional[Candidate]:
        """Parse a single candidate line"""
        # Skip noise lines
        if (line.startswith(('Station', 'School', 'Total No.', 'Number of', 'Voter Turnout')) or 
            re.match(r'^\d+Station\s*\d*$', line) or
            'Parliamentary Elections Results' in line or
            'Region Name' in line or
            len(line) < 10):
            return None
        
        # Pattern: NAME [MIDDLE NAMES] SURNAME PARTY VOTES
        parts = line.split()
        
        if len(parts) >= 3:
            # Find the vote number (last numeric part that's reasonable)
            votes_str = None
            party = None
            name_end_idx = -1
            
            for i in range(len(parts) - 1, -1, -1):
                if re.match(r'^\d{1,6}$', parts[i]) and int(parts[i]) > 0:  # Found votes
                    votes_str = parts[i]
                    if i > 0:  # Party should be before votes
                        party = parts[i - 1]
                        name_end_idx = i - 1
                        break
            
            if votes_str and party and name_end_idx > 0:
                name = ' '.join(parts[:name_end_idx])
                
                try:
                    votes = int(votes_str)
                    
                    # Clean up party code
                    if party in ['INDEPENDENT', 'INDEP']:
                        party = 'IND'
                    
                    # Validate name and party
                    if (re.search(r'[A-Za-z]', name) and 
                        len(name.strip()) > 2 and 
                        len(party) <= 10 and
                        votes >= 0 and
                        not re.match(r'^\d+', name)):  # Name shouldn't start with number
                        
                        return Candidate(
                            name=name.strip(),
                            affiliation=party,
                            votes=votes
                        )
                except ValueError:
                    pass
        
        return None
    
    def _process_candidate(self, candidate: Candidate):
        """Process a single candidate for current context"""
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
        candidate_key = f"{candidate.name}|{candidate.affiliation}"
        self.constituency_data[const_name][candidate_key] += candidate.votes
    
    def _aggregate_to_districts(self) -> Dict[str, any]:
        """Aggregate data to district level following the 2020 structure"""
        from parliamentary_extractor import District, Constituency, Candidate as ExtractorCandidate
        
        districts = {}
        processed_constituencies = 0
        
        for const_name, candidates_data in self.constituency_data.items():
            if not candidates_data:  # Skip empty constituencies
                continue
                
            processed_constituencies += 1
            if processed_constituencies % 20 == 0:
                print(f"Processing constituency {processed_constituencies}/{len(self.constituency_data)}")
                
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
                
                # Filter out obvious parsing errors
                if (len(affiliation) > 15 or 
                    'Station' in affiliation or
                    'School' in affiliation or
                    affiliation.isdigit()):
                    continue
                
                candidate_code = self._generate_candidate_code(name)
                
                candidates.append(ExtractorCandidate(
                    name=name,
                    candidate_code=candidate_code,
                    party_code=affiliation,
                    votes=votes
                ))
            
            # Only add constituency if it has valid candidates
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
        
        # Mapping for common variations
        name_mappings = {
            'chitipa': 'CT', 'karonga': 'KR', 'rumphi': 'RU', 'mzimba': 'MZ',
            'nkhatabay': 'NB', 'nkhata bay': 'NB', 'likoma': 'LK', 'nkhotakota': 'NK',
            'kasungu': 'KS', 'ntchisi': 'NI', 'dowa': 'DO', 'mchinji': 'MC',
            'salima': 'SA', 'lilongwe': 'LI', 'dedza': 'DE', 'ntcheu': 'NU',
            'mangochi': 'MG', 'machinga': 'MH', 'balaka': 'BA', 'zomba': 'ZO',
            'neno': 'NE', 'blantyre': 'BL', 'mwanza': 'MW', 'phalombe': 'PH',
            'chiradzulu': 'CR', 'mulanje': 'MU', 'nsanje': 'NS', 'thyolo': 'TH',
            'chikwawa': 'CK', 'mzuzu': 'ZU'
        }
        
        return name_mappings.get(district_name_clean)
    
    def _find_constituency_code(self, constituency_name: str) -> Optional[str]:
        """Find constituency code from constituency name"""
        const_name_clean = constituency_name.strip().lower()
        
        # Direct match
        for code, const_info in self.validator.constituency_lookup.items():
            if const_info['name'].lower() == const_name_clean:
                return code
        
        # Partial matching with better scoring
        best_match = None
        best_score = 0
        
        for code, const_info in self.validator.constituency_lookup.items():
            const_meta_name = const_info['name'].lower()
            
            # Calculate similarity score
            score = self._calculate_name_similarity(const_name_clean, const_meta_name)
            if score > best_score and score > 0.6:  # Threshold for acceptable match
                best_score = score
                best_match = code
        
        return best_match
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two constituency names"""
        # Remove common words
        common_words = {'constituency', 'north', 'south', 'east', 'west', 'central', 'city'}
        
        words1 = {w for w in name1.split() if w not in common_words and len(w) > 2}
        words2 = {w for w in name2.split() if w not in common_words and len(w) > 2}
        
        if not words1 or not words2:
            return 0
        
        # Calculate overlap score
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def _generate_candidate_code(self, name: str) -> str:
        """Generate a candidate code from the candidate name"""
        parts = name.split()
        if len(parts) > 1:
            surname = parts[-1].upper()[:6]
        else:
            surname = name.upper()[:6]
        
        return surname.ljust(6, 'X')

def main():
    """Main function for robust 2019 extraction"""
    from parliamentary_extractor import MetadataValidator, JSONGenerator, TestFramework
    
    base_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats")
    metadata_path = base_path / "metadata"
    data_path = base_path / "data"
    
    # Initialize components
    print("🚀 Starting robust 2019 parliamentary extraction...")
    validator = MetadataValidator(str(metadata_path))
    extractor = Parliamentary2019RobustExtractor(validator)
    json_generator = JSONGenerator(validator)
    test_framework = TestFramework(validator)
    
    # Process 2019 data
    text_file = data_path / "2019-Parliamentary-results.pdf.txt"
    
    if text_file.exists():
        print(f"📄 Processing 2019 parliamentary data from {text_file.name}...")
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("⚙️ Extracting and aggregating polling station data...")
        extracted_data = extractor.extract_from_text(content)
        
        if extracted_data:
            # Show detailed statistics
            total_constituencies = sum(len(d.constituencies) for d in extracted_data.values())
            total_candidates = sum(len(c.candidates) for d in extracted_data.values() for c in d.constituencies)
            total_votes = sum(candidate.votes for d in extracted_data.values() for c in d.constituencies for candidate in c.candidates)
            
            print(f"\n✅ 2019 Parliamentary Extraction Results:")
            print(f"   📍 Districts: {len(extracted_data)}")
            print(f"   🏛️  Constituencies: {total_constituencies}")
            print(f"   👥 Candidates: {total_candidates}")
            print(f"   🗳️  Total Votes: {total_votes:,}")
            
            # List districts
            print(f"\n📋 Districts processed:")
            for district_code, district in extracted_data.items():
                print(f"   - {district_code}: {district.name} ({len(district.constituencies)} constituencies)")
            
            # Run validation tests
            print(f"\n🔍 Running validation tests...")
            test_framework.test_data_integrity(extracted_data)
            test_framework.print_test_results()
            
            # Generate JSON files
            print(f"\n📁 Generating JSON files...")
            output_dir = base_path / "2019" / "results" / "parliamentary"
            
            for district in extracted_data.values():
                json_generator.generate_district_json(district, str(output_dir))
            
            print(f"\n🎉 2019 Parliamentary extraction completed successfully!")
            print(f"📦 Generated {len(extracted_data)} district files in: {output_dir}")
            
        else:
            print("❌ No data extracted from 2019 file")
    else:
        print(f"❌ 2019 data file not found: {text_file}")

if __name__ == "__main__":
    main()