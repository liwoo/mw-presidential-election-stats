#!/usr/bin/env python3
"""
Enhanced 2019 Parliamentary Election Data Extractor
Handles all districts by improving name matching and context extraction.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, namedtuple

# Data structures
Candidate = namedtuple('Candidate', ['name', 'affiliation', 'votes'])

class Parliamentary2019EnhancedExtractor:
    def __init__(self, validator):
        self.validator = validator
        self.constituency_data = defaultdict(lambda: defaultdict(int))
        self.constituency_info = {}
        self.current_context = {}
        self.debug_contexts = []  # Store for debugging
        
        # Enhanced district name mappings
        self.district_mappings = {
            'chitipa': 'CT', 'karonga': 'KR', 'rumphi': 'RU', 'mzimba': 'MZ',
            'nkhatabay': 'NB', 'nkhata bay': 'NB', 'likoma': 'LK', 'nkhotakota': 'NK',
            'kasungu': 'KS', 'ntchisi': 'NI', 'dowa': 'DO', 'mchinji': 'MC',
            'salima': 'SA', 'lilongwe': 'LI', 'dedza': 'DE', 'ntcheu': 'NU',
            'mangochi': 'MG', 'machinga': 'MH', 'balaka': 'BA', 'zomba': 'ZO',
            'neno': 'NE', 'blantyre': 'BL', 'mwanza': 'MW', 'phalombe': 'PH',
            'chiradzulu': 'CR', 'mulanje': 'MU', 'nsanje': 'NS', 'thyolo': 'TH',
            'chikwawa': 'CK', 'chikhwawa': 'CK',  # Handle spelling variations
            'mzuzu': 'ZU',
            # Additional variations
            'mbalaka': 'BA'
        }
        
        # Enhanced constituency name normalization
        self.constituency_normalizations = {
            'north': 'North', 'south': 'South', 'east': 'East', 'west': 'West',
            'central': 'Central', 'city': 'City',
            'lisanjala': 'Lisanjala', 'chisi': 'Chisi',
            'kabula': 'Kabula', 'wenya': 'Wenya'
        }
    
    def extract(self, file_path: str):
        """Extract all parliamentary data from the 2019 text file"""
        print(f"📄 Processing enhanced 2019 parliamentary data from {Path(file_path).name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"⚙️ Enhanced extraction from {len(lines)} lines...")
        self._process_lines(lines)
        
        print(f"Found {len(self.constituency_data)} constituencies")
        print(f"Collected {len(self.debug_contexts)} context entries")
        
        # Debug: show some contexts
        print("\nSample contexts found:")
        for i, ctx in enumerate(self.debug_contexts[:10]):
            print(f"  {i+1}. {ctx}")
        
        return self._aggregate_to_districts()
    
    def _process_lines(self, lines: List[str]):
        """Enhanced processing with better context extraction"""
        multi_line_buffer = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Handle multi-line contexts
            if self._looks_like_context_fragment(line):
                multi_line_buffer += " " + line
                continue
            
            # Process complete context line
            if multi_line_buffer:
                complete_line = multi_line_buffer.strip()
                context = self._extract_context_enhanced(complete_line)
                if context:
                    self.current_context = context
                    self.debug_contexts.append(f"Multi-line: {complete_line[:100]}... -> {context}")
                multi_line_buffer = ""
            
            # Try to extract context from current line
            context = self._extract_context_enhanced(line)
            if context:
                self.current_context = context
                self.debug_contexts.append(f"Single: {line[:100]}... -> {context}")
            
            # Try to extract candidate from current line
            candidate = self._extract_candidate_enhanced(line)
            if candidate:
                self._process_candidate(candidate)
    
    def _looks_like_context_fragment(self, line: str) -> bool:
        """Check if line looks like a context fragment that should be buffered"""
        context_indicators = [
            r'^\d+[A-Z][a-z]+$',  # "1Chitipa"
            r'^[A-Z][a-z]+ \d+$',  # "Region 1"
            r'^\d+ [A-Z][a-z]+ \d+$',  # "1 Chitipa 01"
            r'^[A-Z][a-z]+ [A-Z][a-z]+ \d+$'  # "Chitipa East 001"
        ]
        
        return any(re.match(pattern, line.strip()) for pattern in context_indicators)
    
    def _extract_context_enhanced(self, line: str) -> Optional[Dict[str, str]]:
        """Enhanced context extraction with better pattern matching"""
        line = line.strip()
        
        # Pattern 1: Full context line like "Northern Region 1Chitipa 01 Chitipa East 001"
        match = re.match(r'([A-Z][a-z]+)\s+Region\s+(\d*)([A-Z][a-z]+)\s+(\d+)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(\d+)', line)
        if match:
            region, district_num, district, district_code, constituency, const_code = match.groups()
            return {
                'region': region,
                'district': district,
                'district_code': district_code.zfill(2),
                'constituency': constituency,
                'constituency_code': const_code.zfill(3)
            }
        
        # Pattern 2: Context with embedded numbers like "Northern Region Chitipa 01 Chitipa East 001"
        match = re.match(r'([A-Z][a-z]+)\s+Region\s+([A-Z][a-z]+)\s+(\d+)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(\d+)', line)
        if match:
            region, district, district_code, constituency, const_code = match.groups()
            return {
                'region': region,
                'district': district,
                'district_code': district_code.zfill(2),
                'constituency': constituency,
                'constituency_code': const_code.zfill(3)
            }
        
        # Pattern 3: Simple district constituency pattern "Chitipa 01 Chitipa East 001"
        match = re.match(r'([A-Z][a-z]+)\s+(\d+)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(\d+)', line)
        if match:
            district, district_code, constituency, const_code = match.groups()
            return {
                'region': 'Unknown',
                'district': district,
                'district_code': district_code.zfill(2),
                'constituency': constituency,
                'constituency_code': const_code.zfill(3)
            }
        
        # Pattern 4: District only "Dowa 10"
        match = re.match(r'^([A-Z][a-z]+)\s+(\d+)\s', line)
        if match:
            district, district_code = match.groups()
            return {
                'region': 'Unknown',
                'district': district,
                'district_code': district_code.zfill(2),
                'constituency': 'Unknown',
                'constituency_code': '000'
            }
        
        # Pattern 5: Constituency with complex names "Balaka North 026"
        match = re.match(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(\d+)', line)
        if match:
            constituency, const_code = match.groups()
            # Try to extract district from constituency name
            district = constituency.split()[0]
            return {
                'region': 'Unknown',
                'district': district,
                'district_code': '00',
                'constituency': constituency,
                'constituency_code': const_code.zfill(3)
            }
        
        return None
    
    def _extract_candidate_enhanced(self, line: str) -> Optional[Candidate]:
        """Enhanced candidate extraction with better error handling"""
        line = line.strip()
        
        # Skip obvious non-candidate lines
        skip_patterns = [
            r'^Total\s+No\.\s+of',
            r'^Station\s+\d+',
            r'^\d+\s*$',
            r'^[A-Z][a-z]+\s+School',
            r'^[A-Z][a-z]+\s+Region',
            r'Region\s+\d'
        ]
        
        if any(re.match(pattern, line) for pattern in skip_patterns):
            return None
        
        # Enhanced candidate patterns
        patterns = [
            # Pattern 1: "NAME SURNAME PARTY 123"
            r'^([A-Z][A-Z\s\-\']+?)\s+([A-Z]{2,6})\s+(\d+)(?:\s|$)',
            # Pattern 2: "NAME SURNAME MIDDLE PARTY 123"  
            r'^([A-Z][A-Z\s\-\']{4,})\s+([A-Z]{2,6})\s+(\d+)(?:\s|$)',
            # Pattern 3: Handle names with punctuation
            r'^([A-Z][A-Z\s\-\'\.]+?)\s+([A-Z]{3,6})\s+(\d+)(?:\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1).strip()
                party = match.group(2).strip()
                votes_str = match.group(3).strip()
                
                # Validation
                if len(name) < 3 or len(party) < 2:
                    continue
                
                # Clean up common OCR errors in names
                name = re.sub(r'[^A-Z\s\-\']', '', name)
                if len(name.split()) < 1:
                    continue
                
                try:
                    votes = int(votes_str)
                    if votes < 0:
                        continue
                    
                    return Candidate(
                        name=name.strip(),
                        affiliation=party,
                        votes=votes
                    )
                except ValueError:
                    continue
        
        return None
    
    def _process_candidate(self, candidate: Candidate):
        """Process candidate with enhanced context handling"""
        if not self.current_context:
            return
        
        # Use constituency from context, with fallbacks
        const_name = self.current_context.get('constituency', 'Unknown')
        district_name = self.current_context.get('district', 'Unknown')
        region = self.current_context.get('region', 'Unknown')
        
        # Skip if we don't have enough context
        if const_name == 'Unknown' and district_name == 'Unknown':
            return
        
        # If constituency is unknown but we have district, create a generic constituency
        if const_name == 'Unknown' and district_name != 'Unknown':
            const_name = f"{district_name} General"
        
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
        """Enhanced aggregation to district level"""
        from parliamentary_extractor import District, Constituency, Candidate as ExtractorCandidate
        
        districts = {}
        processed_constituencies = 0
        skipped_constituencies = []
        
        for const_name, candidates_data in self.constituency_data.items():
            if not candidates_data:
                continue
            
            processed_constituencies += 1
            const_info = self.constituency_info.get(const_name, {})
            district_name = const_info.get('district', 'Unknown')
            
            # Enhanced district code lookup
            district_code = self._find_district_code_enhanced(district_name)
            if not district_code:
                skipped_constituencies.append(f"{const_name} (district: {district_name})")
                continue
            
            # Enhanced constituency code lookup
            constituency_code = self._find_constituency_code_enhanced(const_name, district_code)
            if not constituency_code:
                # Generate a constituency code if we can't find one
                constituency_code = f"{int(district_code):03d}"
            
            # Create district if not exists
            if district_code not in districts:
                district_info = self.validator.district_lookup.get(district_code, {})
                districts[district_code] = District(
                    code=district_code,
                    name=district_info.get('name', district_name),
                    region=const_info.get('region', 'Unknown'),
                    constituencies=[]
                )
            
            # Create candidates list with enhanced filtering
            candidates = []
            for candidate_key, votes in candidates_data.items():
                if '|' not in candidate_key:
                    continue
                
                name, affiliation = candidate_key.split('|', 1)
                
                # Enhanced affiliation cleaning
                affiliation = self._clean_party_code_enhanced(affiliation)
                if not affiliation:
                    continue
                
                candidate_code = self._generate_candidate_code(name)
                
                candidates.append(ExtractorCandidate(
                    name=name,
                    candidate_code=candidate_code,
                    party_code=affiliation,
                    votes=votes
                ))
            
            # Add constituency if it has valid candidates
            if candidates:
                constituency = Constituency(
                    code=constituency_code,
                    name=const_name,
                    candidates=candidates
                )
                districts[district_code].constituencies.append(constituency)
        
        if skipped_constituencies:
            print(f"\nSkipped {len(skipped_constituencies)} constituencies due to mapping issues:")
            for skipped in skipped_constituencies[:10]:  # Show first 10
                print(f"  - {skipped}")
            if len(skipped_constituencies) > 10:
                print(f"  ... and {len(skipped_constituencies) - 10} more")
        
        return districts
    
    def _find_district_code_enhanced(self, district_name: str) -> Optional[str]:
        """Enhanced district code lookup with better matching"""
        if not district_name or district_name == 'Unknown':
            return None
        
        district_name_clean = district_name.strip().lower()
        
        # Direct mapping lookup
        if district_name_clean in self.district_mappings:
            return self.district_mappings[district_name_clean]
        
        # Try partial matches
        for name_pattern, code in self.district_mappings.items():
            if name_pattern in district_name_clean or district_name_clean in name_pattern:
                return code
        
        # Fuzzy matching against metadata
        for code, district_info in self.validator.district_lookup.items():
            meta_name = district_info['name'].lower()
            if (district_name_clean == meta_name or 
                district_name_clean in meta_name or 
                meta_name in district_name_clean):
                return code
        
        return None
    
    def _find_constituency_code_enhanced(self, const_name: str, district_code: str) -> Optional[str]:
        """Enhanced constituency code lookup"""
        const_name_clean = const_name.strip().lower()
        
        # Direct match
        for code, const_info in self.validator.constituency_lookup.items():
            if const_info['name'].lower() == const_name_clean:
                return code
        
        # Partial matching within the same district
        district_constituencies = [
            (code, info) for code, info in self.validator.constituency_lookup.items()
            if info.get('districtCode') == district_code
        ]
        
        best_match = None
        best_score = 0
        
        for code, const_info in district_constituencies:
            const_meta_name = const_info['name'].lower()
            score = self._calculate_name_similarity_enhanced(const_name_clean, const_meta_name)
            
            if score > best_score and score > 0.5:  # Lower threshold
                best_score = score
                best_match = code
        
        return best_match
    
    def _calculate_name_similarity_enhanced(self, name1: str, name2: str) -> float:
        """Enhanced name similarity calculation"""
        # Normalize constituency names
        for old, new in self.constituency_normalizations.items():
            name1 = name1.replace(old.lower(), new.lower())
            name2 = name2.replace(old.lower(), new.lower())
        
        # Remove common words and calculate overlap
        common_words = {'constituency', 'north', 'south', 'east', 'west', 'central', 'city'}
        
        words1 = {w for w in name1.split() if w not in common_words and len(w) > 2}
        words2 = {w for w in name2.split() if w not in common_words and len(w) > 2}
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def _clean_party_code_enhanced(self, party_code: str) -> Optional[str]:
        """Enhanced party code cleaning"""
        if not party_code:
            return None
        
        # Remove obvious parsing errors
        if (len(party_code) > 15 or 
            'Station' in party_code or
            'School' in party_code or
            party_code.isdigit() or
            re.match(r'^\d+[A-Za-z]+', party_code)):
            return None
        
        # Valid party codes
        valid_parties = {'MCP', 'DPP', 'UTM', 'UDF', 'IND', 'PP', 'AFORD', 'DePeCo'}
        if party_code in valid_parties:
            return party_code
        
        # Default questionable codes to IND
        return 'IND'
    
    def _generate_candidate_code(self, name: str) -> str:
        """Generate candidate code from name"""
        parts = name.split()
        if len(parts) > 1:
            surname = parts[-1].upper()[:6]
        else:
            surname = name.upper()[:6]
        
        return surname.ljust(6, 'X')

def main():
    """Main function for enhanced 2019 extraction"""
    from parliamentary_extractor import MetadataValidator, JSONGenerator, TestFramework
    
    base_path = Path(r"C:\\Users\\lacso\\Git\\mw-presidential-election-stats")
    metadata_path = base_path / "metadata"
    data_path = base_path / "data"
    
    # Initialize components
    print("🚀 Starting ENHANCED 2019 parliamentary extraction...")
    validator = MetadataValidator(str(metadata_path))
    extractor = Parliamentary2019EnhancedExtractor(validator)
    json_generator = JSONGenerator(validator)
    test_framework = TestFramework(validator)
    
    # Process 2019 data
    text_file = data_path / "2019-Parliamentary-results.pdf.txt"
    
    if text_file.exists():
        districts = extractor.extract(str(text_file))
        
        # Generate summary
        total_constituencies = sum(len(d.constituencies) for d in districts.values())
        total_candidates = sum(sum(len(c.candidates) for c in d.constituencies) for d in districts.values())
        total_votes = sum(sum(sum(cand.votes for cand in c.candidates) for c in d.constituencies) for d in districts.values())
        
        print(f"\n✅ ENHANCED 2019 Parliamentary Extraction Results:")
        print(f"   📍 Districts: {len(districts)}")
        print(f"   🏛️  Constituencies: {total_constituencies}")
        print(f"   👥 Candidates: {total_candidates}")
        print(f"   🗳️  Total Votes: {total_votes:,}")
        
        print(f"\n📋 Districts processed:")
        for district_code in sorted(districts.keys()):
            district = districts[district_code]
            print(f"   - {district_code}: {district.name} ({len(district.constituencies)} constituencies)")
        
        # Run validation tests
        print(f"\n🔍 Running validation tests...")
        test_framework.run_tests(districts)
        
        # Generate JSON files
        print(f"\n📁 Generating JSON files...")
        output_path = base_path / "2019" / "results" / "parliamentary"
        output_path.mkdir(parents=True, exist_ok=True)
        
        for district_code, district in districts.items():
            json_generator.generate_district_json(district, str(output_path), year=2019, election_type="parliamentary")
        
        print(f"\n🎉 ENHANCED 2019 Parliamentary extraction completed successfully!")
        print(f"📦 Generated {len(districts)} district files in: {output_path}")
    
    else:
        print(f"❌ Text file not found: {text_file}")

if __name__ == "__main__":
    main()