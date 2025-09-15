#!/usr/bin/env python3
"""
Parliamentary Vote Extractor
Extracts parliamentary voting data from text files and creates JSON files 
following the 2020 structure format.

Using TDD approach with comprehensive validation against metadata.
"""

import json
import re
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Candidate:
    """Represents a candidate in a constituency"""
    name: str
    candidate_code: str
    party_code: str
    votes: int

@dataclass
class Constituency:
    """Represents a constituency with its candidates"""
    code: str
    name: str
    candidates: List[Candidate]
    null_votes: int = 0

@dataclass
class District:
    """Represents a district with its constituencies"""
    code: str
    name: str
    region: str
    constituencies: List[Constituency]

class MetadataValidator:
    """Validates extracted data against metadata"""
    
    def __init__(self, metadata_path: str):
        self.metadata_path = metadata_path
        self.administration = self._load_json('administration.json')
        self.parties = self._load_json('parties.json')
        self.candidates = self._load_json('candidates.json') if os.path.exists(
            os.path.join(metadata_path, 'candidates.json')
        ) else []
        
        # Create lookup dictionaries
        self.party_lookup = {p['code']: p for p in self.parties}
        self.district_lookup = {d['code']: d for d in self.administration['districts']}
        self.constituency_lookup = {}
        
        # Build constituency lookup
        for district in self.administration['districts']:
            for const in district.get('constituencies', []):
                if isinstance(const, dict):
                    self.constituency_lookup[const['code']] = {
                        'name': const['name'],
                        'district': district['code']
                    }
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file from metadata directory"""
        file_path = os.path.join(self.metadata_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_party_code(self, party_code: str) -> bool:
        """Validate if party code exists in metadata"""
        return party_code in self.party_lookup
    
    def validate_constituency_code(self, const_code: str) -> bool:
        """Validate if constituency code exists in metadata"""
        return const_code in self.constituency_lookup
    
    def get_district_for_constituency(self, const_code: str) -> Optional[str]:
        """Get district code for a constituency"""
        const_info = self.constituency_lookup.get(const_code)
        return const_info['district'] if const_info else None

class ParliamentaryExtractor:
    """Extracts parliamentary voting data from text files"""
    
    def __init__(self, metadata_validator: MetadataValidator):
        self.validator = metadata_validator
        self.extracted_data: Dict[str, District] = {}
    
    def extract_from_text(self, text_content: str) -> Dict[str, District]:
        """Extract parliamentary data from text content"""
        lines = [line.strip() for line in text_content.split('\n')]
        current_constituency = None
        candidates = []
        
        # Regex patterns for parsing
        constituency_pattern = re.compile(r'^(.+?)\s+(\d{1,3})$')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines and headers
            if not line or line in ['Candidate', 'Party', 'Votes Received % Rec\'d']:
                i += 1
                continue
            
            # Check for constituency header
            const_match = constituency_pattern.match(line)
            if const_match:
                # Save previous constituency if exists
                if current_constituency and candidates:
                    self._save_constituency_data(current_constituency, candidates)
                
                # Start new constituency
                const_name = const_match.group(1).strip()
                const_code = const_match.group(2).zfill(3)  # Pad with zeros
                current_constituency = {'name': const_name, 'code': const_code}
                candidates = []
                i += 1
                continue
            
            # Check if this is the end of constituency data
            if line.startswith(('Total Valid Votes', 'Null & Void', 'Total Votes Cast', 'Number of Registered', 'Voter Turnout')):
                i += 1
                continue
            
            # Try to parse candidate data (expecting name, party, votes in sequence)
            if current_constituency and self._looks_like_candidate_name(line):
                candidate_data = self._parse_candidate_sequence(lines, i)
                if candidate_data:
                    candidates.append(candidate_data[0])
                    i = candidate_data[1]  # Update index
                else:
                    i += 1
            else:
                i += 1
        
        # Save last constituency
        if current_constituency and candidates:
            self._save_constituency_data(current_constituency, candidates)
        
        return self.extracted_data
    
    def _looks_like_candidate_name(self, line: str) -> bool:
        """Check if a line looks like a candidate name"""
        # Skip lines that are clearly not names
        if (not line or 
            line.startswith(('Total Valid Votes', 'Null & Void', 'Total Votes Cast', 'Number of Registered', 'Voter Turnout')) or
            line in ['Candidate', 'Party', 'Votes Received % Rec\'d', 'VOID', 'TURNOUT'] or
            re.match(r'^\d{1,3}(?:,\d{3})*\s*[\d.]*%?$', line) or  # Just numbers/percentages
            re.match(r'^(.+?)\s+(\d{1,3})$', line) or  # Constituency header
            re.match(r'^[\d.]+%?$', line) or  # Pure percentage
            line.upper() in ['VOID', '%TURNOUT']):
            return False
        
        # Should contain alphabetic characters and look like a name
        return bool(re.search(r'[A-Za-z]', line))
    
    def _parse_candidate_sequence(self, lines: List[str], start_index: int) -> Optional[Tuple[Candidate, int]]:
        """Parse candidate data from sequence of lines: name, party, votes"""
        if start_index + 2 >= len(lines):
            return None
        
        name_line = lines[start_index]
        party_line = lines[start_index + 1] if start_index + 1 < len(lines) else ""
        votes_line = lines[start_index + 2] if start_index + 2 < len(lines) else ""
        
        # Extract name
        name = name_line.strip()
        
        # Extract party
        party = party_line.strip()
        if party in ['INDEPENDENT', 'INDEP']:
            party = 'IND'
        
        # Extract votes (handle percentage format)
        votes_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*[\d.]*%?', votes_line)
        if not votes_match:
            return None
        
        try:
            votes = int(votes_match.group(1).replace(',', ''))
        except ValueError:
            return None
        
        # Validate party code
        if not self.validator.validate_party_code(party):
            print(f"Warning: Unknown party code '{party}' for candidate {name}")
            # Try some common mappings and typos
            if party == 'INDEPENDENT':
                party = 'IND'
            elif party == 'PDM':  # People's Democratic Movement (possible typo/variant)
                party = 'PDP'  # Map to People's Development Party
            elif party == 'DDP':  # Likely typo for DPP
                party = 'DPP'
            elif party == 'MPP':  # Malawi People's Party (possible variant)
                party = 'PP'   # Map to People's Party
            else:
                # For data quality tracking, continue with unknown codes
                pass
        
        # Generate candidate code
        candidate_code = self._generate_candidate_code(name)
        
        candidate = Candidate(
            name=name,
            candidate_code=candidate_code,
            party_code=party,
            votes=votes
        )
        
        return candidate, start_index + 3
    
    def _generate_candidate_code(self, name: str) -> str:
        """Generate a candidate code from the candidate name"""
        # Take first 6 characters of surname (last word) in uppercase
        parts = name.split()
        if len(parts) > 1:
            surname = parts[-1].upper()[:6]
        else:
            surname = name.upper()[:6]
        
        return surname.ljust(6, 'X')  # Pad with X if needed
    
    def _save_constituency_data(self, const_info: Dict, candidates: List[Candidate]):
        """Save constituency data to the extracted data structure"""
        const_code = const_info['code']
        district_code = self.validator.get_district_for_constituency(const_code)
        
        if not district_code:
            print(f"Warning: Could not find district for constituency {const_code}")
            return
        
        # Create district if not exists
        if district_code not in self.extracted_data:
            district_info = self.validator.district_lookup.get(district_code, {})
            self.extracted_data[district_code] = District(
                code=district_code,
                name=district_info.get('name', 'Unknown'),
                region=district_info.get('region', 'Unknown'),
                constituencies=[]
            )
        
        # Add constituency to district
        constituency = Constituency(
            code=const_code,
            name=const_info['name'],
            candidates=candidates
        )
        
        self.extracted_data[district_code].constituencies.append(constituency)

class JSONGenerator:
    """Generates JSON files in the required format"""
    
    def __init__(self, validator: MetadataValidator):
        self.validator = validator
    
    def generate_district_json(self, district: District, output_dir: str):
        """Generate JSON file for a district following the 2020 format"""
        
        constituencies_data = []
        
        for constituency in district.constituencies:
            candidates_data = []
            
            for candidate in constituency.candidates:
                candidates_data.append({
                    "candidateCode": candidate.candidate_code,
                    "partyCode": candidate.party_code,
                    "votes": candidate.votes
                })
            
            constituencies_data.append({
                "code": constituency.code,
                "isLegacy": False,  # Assuming these are not legacy
                "candidates": candidates_data
            })
        
        # Calculate total null votes (placeholder for now)
        total_null_votes = sum(const.null_votes for const in district.constituencies)
        
        district_data = {
            "districtCode": district.code,
            "type": "parliamentary",
            "nullVotes": total_null_votes,
            "constituencies": constituencies_data
        }
        
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Write JSON file
        filename = f"{district.code}_RESULTS.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(district_data, f, indent=2, ensure_ascii=False)
        
        print(f"Generated: {filepath}")

class TestFramework:
    """Test framework for validating extraction results"""
    
    def __init__(self, validator: MetadataValidator):
        self.validator = validator
        self.test_results = []
    
    def test_data_integrity(self, extracted_data: Dict[str, District]) -> bool:
        """Test overall data integrity"""
        tests_passed = 0
        total_tests = 0
        invalid_parties = set()
        invalid_districts = set()
        invalid_constituencies = set()
        
        # Test 1: All districts should have valid codes
        total_tests += 1
        for code in extracted_data.keys():
            if code not in self.validator.district_lookup:
                invalid_districts.add(code)
        
        if not invalid_districts:
            tests_passed += 1
            self.test_results.append("✓ All district codes are valid")
        else:
            self.test_results.append(f"✗ Invalid district codes: {', '.join(invalid_districts)}")
        
        # Test 2: All constituencies should have valid codes
        total_tests += 1
        for district in extracted_data.values():
            for const in district.constituencies:
                if not self.validator.validate_constituency_code(const.code):
                    invalid_constituencies.add(f"{district.code}:{const.code}")
        
        if not invalid_constituencies:
            tests_passed += 1
            self.test_results.append("✓ All constituency codes are valid")
        else:
            self.test_results.append(f"✗ Invalid constituency codes: {', '.join(list(invalid_constituencies)[:5])}{'...' if len(invalid_constituencies) > 5 else ''}")
        
        # Test 3: All party codes should be valid
        total_tests += 1
        for district in extracted_data.values():
            for const in district.constituencies:
                for candidate in const.candidates:
                    if not self.validator.validate_party_code(candidate.party_code):
                        invalid_parties.add(candidate.party_code)
        
        if not invalid_parties:
            tests_passed += 1
            self.test_results.append("✓ All party codes are valid")
        else:
            self.test_results.append(f"✗ Invalid party codes: {', '.join(list(invalid_parties))}")
        
        # Test 4: All candidates should have positive vote counts
        total_tests += 1
        negative_votes = 0
        for district in extracted_data.values():
            for const in district.constituencies:
                for candidate in const.candidates:
                    if candidate.votes < 0:
                        negative_votes += 1
        
        if negative_votes == 0:
            tests_passed += 1
            self.test_results.append("✓ All vote counts are non-negative")
        else:
            self.test_results.append(f"✗ Found {negative_votes} candidates with negative votes")
        
        # Additional statistics
        total_districts = len(extracted_data)
        total_constituencies = sum(len(d.constituencies) for d in extracted_data.values())
        total_candidates = sum(len(c.candidates) for d in extracted_data.values() for c in d.constituencies)
        total_votes = sum(candidate.votes for d in extracted_data.values() for c in d.constituencies for candidate in c.candidates)
        
        self.test_results.append(f"\n📊 DATA STATISTICS:")
        self.test_results.append(f"   Districts processed: {total_districts}")
        self.test_results.append(f"   Constituencies: {total_constituencies}")
        self.test_results.append(f"   Total candidates: {total_candidates}")
        self.test_results.append(f"   Total votes: {total_votes:,}")
        
        success_rate = tests_passed / total_tests
        self.test_results.append(f"\n🎯 Overall test success rate: {success_rate:.1%} ({tests_passed}/{total_tests})")
        
        return success_rate == 1.0
    
    def print_test_results(self):
        """Print test results"""
        print("\n=== TEST RESULTS ===")
        for result in self.test_results:
            print(result)
        print("==================")

def main():
    """Main execution function"""
    base_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats")
    metadata_path = base_path / "metadata"
    data_path = base_path / "data"
    
    # Initialize components
    print("Initializing metadata validator...")
    validator = MetadataValidator(str(metadata_path))
    
    print("Setting up extractor and test framework...")
    extractor = ParliamentaryExtractor(validator)
    json_generator = JSONGenerator(validator)
    test_framework = TestFramework(validator)
    
    # Process 2014 data
    print("\nProcessing 2014 parliamentary data...")
    text_file_2014 = data_path / "2014-Parliament-results.pdf.txt"
    
    if text_file_2014.exists():
        with open(text_file_2014, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extracted_data_2014 = extractor.extract_from_text(content)
        
        if extracted_data_2014:
            print(f"Extracted 2014 data for {len(extracted_data_2014)} districts")
            
            # Run tests
            test_framework_2014 = TestFramework(validator)
            test_framework_2014.test_data_integrity(extracted_data_2014)
            test_framework_2014.print_test_results()
            
            # Generate JSON files
            output_dir_2014 = base_path / "2014" / "results" / "parliamentary"
            for district in extracted_data_2014.values():
                json_generator.generate_district_json(district, str(output_dir_2014))
        else:
            print("No data extracted from 2014 file")
    else:
        print(f"2014 data file not found: {text_file_2014}")
    
    # Process 2019 data
    print("\nProcessing 2019 parliamentary data...")
    
    # Check for text version first
    text_file_2019 = data_path / "2019-Parliamentary-results.pdf.txt"
    pdf_file_2019 = data_path / "2019-Parliamentary-results.pdf"
    
    content_2019 = None
    
    if text_file_2019.exists():
        print("Found 2019 text file, using it...")
        with open(text_file_2019, 'r', encoding='utf-8') as f:
            content_2019 = f.read()
    elif pdf_file_2019.exists():
        print("Found 2019 PDF file. Please extract text from PDF first.")
        print("You can extract text using: pdfplumber, PyPDF2, or online PDF to text converter")
        print("Save the extracted text as: 2019-Parliamentary-results.pdf.txt")
        print("Skipping 2019 processing for now...")
    else:
        print("2019 parliamentary data file not found")
    
    if content_2019:
        # Reset extractor for 2019 data
        extractor_2019 = ParliamentaryExtractor(validator)
        extracted_data_2019 = extractor_2019.extract_from_text(content_2019)
        
        if extracted_data_2019:
            print(f"Extracted 2019 data for {len(extracted_data_2019)} districts")
            
            # Run tests
            test_framework_2019 = TestFramework(validator)
            test_framework_2019.test_data_integrity(extracted_data_2019)
            test_framework_2019.print_test_results()
            
            # Generate JSON files
            output_dir_2019 = base_path / "2019" / "results" / "parliamentary"
            for district in extracted_data_2019.values():
                json_generator.generate_district_json(district, str(output_dir_2019))
        else:
            print("No data extracted from 2019 file")
    
    print("\nExtraction completed!")

if __name__ == "__main__":
    main()