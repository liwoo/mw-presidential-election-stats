#!/usr/bin/env python3
"""
Extract 2020 Presidential Election Results
Generates missing district JSON files from PDF data following TDD principles
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Candidate:
    candidate_code: str
    party_code: str
    votes: int

@dataclass
class Constituency:
    code: str
    is_legacy: bool
    candidates: List[Candidate]

@dataclass
class DistrictResult:
    district_code: str
    type: str
    null_votes: int
    constituencies: List[Constituency]

class ElectionDataExtractor:
    """Extract and validate 2020 presidential election results"""
    
    def __init__(self, pdf_text_path: str, metadata_dir: str):
        self.pdf_text_path = pdf_text_path
        self.metadata_dir = metadata_dir
        
        # Load metadata
        self.administration_data = self.load_json(os.path.join(metadata_dir, 'administration.json'))
        self.candidates_data = self.load_json(os.path.join(metadata_dir, 'candidates.json'))
        self.parties_data = self.load_json(os.path.join(metadata_dir, 'parties.json'))
        
        # Create lookup dictionaries
        self.district_lookup = {d['name']: d['code'] for d in self.administration_data['districts']}
        self.constituency_lookup = {}
        for district in self.administration_data['districts']:
            for const in district['constituencies']:
                self.constituency_lookup[const['name']] = {
                    'code': const['code'],
                    'district_code': district['code']
                }
        
        # 2020 Presidential candidates mapping
        self.candidate_mapping = {
            'LAZARUS CHAKWERA': {'code': 'LAZCHA', 'party': 'MCP'},
            'ARTHUR PETER MUTHARIKA': {'code': 'PETMUT', 'party': 'DPP'},
            'PETER DOMINICO SINOSI DRIVER KUWANI': {'code': 'PETSIN', 'party': 'MMD'}
        }
        
    def load_json(self, filepath: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_pdf_text(self) -> str:
        """Load PDF text content"""
        with open(self.pdf_text_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_constituency_results(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract constituency results from PDF text"""
        results_by_district = {}
        
        # Split text into lines and process constituency by constituency
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for constituency results pattern
            if 'Constituency Results' in line:
                const_name_match = re.search(r'^(.+?)\s+Constituency Results', line)
                if const_name_match:
                    const_name = const_name_match.group(1).strip()
                    
                    # Extract the votes data from current and next few lines
                    combined_text = line
                    j = i + 1
                    # Read up to 5 more lines to get complete data
                    while j < len(lines) and j < i + 6:
                        combined_text += ' ' + lines[j].strip()
                        j += 1
                    
                    # Extract votes using regex
                    mcp_match = re.search(r'LAZARUS CHAKWERA \(MCP\) Votes:\s*([0-9,]+)', combined_text)
                    mmd_match = re.search(r'PETER DOMINICO SINOSI DRIVER KUWANI \(MMD\) Votes:\s*([0-9,]+)', combined_text) 
                    dpp_match = re.search(r'ARTHUR PETER MUTHARIKA \(DPP\) Votes:\s*([0-9,]+)', combined_text)
                    null_match = re.search(r'Null and Void Votes\s+([0-9,]+)', combined_text)
                    
                    if mcp_match and mmd_match and dpp_match and null_match:
                        # Parse votes (remove commas)
                        mcp_votes = int(mcp_match.group(1).replace(',', ''))
                        mmd_votes = int(mmd_match.group(1).replace(',', ''))
                        dpp_votes = int(dpp_match.group(1).replace(',', ''))
                        null_votes_int = int(null_match.group(1).replace(',', ''))
                        
                        # Try to match constituency to district
                        district_code = self.get_district_for_constituency(const_name)
                        
                        if district_code:
                            if district_code not in results_by_district:
                                results_by_district[district_code] = []
                            
                            # Get constituency code
                            const_info = self.constituency_lookup.get(const_name)
                            const_code = const_info['code'] if const_info else self.generate_constituency_code(const_name)
                            
                            constituency_result = {
                                'name': const_name,
                                'code': const_code,
                                'candidates': [
                                    {'candidateCode': 'LAZCHA', 'partyCode': 'MCP', 'votes': mcp_votes},
                                    {'candidateCode': 'PETKUW', 'partyCode': 'MMD', 'votes': mmd_votes},
                                    {'candidateCode': 'PETMUT', 'partyCode': 'DPP', 'votes': dpp_votes}
                                ],
                                'null_votes': null_votes_int
                            }
                            
                            results_by_district[district_code].append(constituency_result)
                            print(f"Extracted: {const_name} -> {district_code}")
                        else:
                            print(f"Could not map constituency: {const_name}")
            
            i += 1
        
        return results_by_district
    
    def get_district_for_constituency(self, constituency_name: str) -> Optional[str]:
        """Get district code for a given constituency name"""
        # Direct lookup first
        if constituency_name in self.constituency_lookup:
            return self.constituency_lookup[constituency_name]['district_code']
        
        # Try partial matching for variations
        constituency_lower = constituency_name.lower()
        
        # Common mappings based on constituency names
        district_mappings = {
            'chitipa': 'CT',
            'karonga': 'KR', 
            'rumphi': 'RU',
            'mzuzu': 'ZU',
            'nkhatabay': 'NB',  # Should be 'NB' not in existing files
            'nkhotakota': 'NK',
            'kasungu': 'KS',
            'mzimba': 'MZ',
            'lilongwe': 'LI',
            'dowa': 'DO',
            'salima': 'SA',
            'mchinji': 'MC',
            'ntchisi': 'NI',
            'dedza': 'DE',      # Missing from 2020
            'ntcheu': 'NU',
            'mangochi': 'MG',
            'machinga': 'MH',
            'zomba': 'ZO',
            'chiradzulu': 'CR', # Missing from 2020
            'blantyre': 'BL',
            'mulanje': 'MU',
            'phalombe': 'PH',
            'thyolo': 'TH',     # Missing from 2020
            'chikwawa': 'CK',   # Missing from 2020
            'chikhwawa': 'CK',  # Alternative spelling
            'nsanje': 'NS',     # Missing from 2020
            'mwanza': 'MW',     # Missing from 2020
            'neno': 'NE',       # Missing from 2020
            'balaka': 'BA',     # Missing from 2020
            'likoma': 'LK'
        }
        
        for district_name, district_code in district_mappings.items():
            if district_name in constituency_lower:
                return district_code
        
        print(f"Warning: Could not map constituency '{constituency_name}' to district")
        return None
    
    def generate_constituency_code(self, constituency_name: str) -> str:
        """Generate a constituency code for unmapped constituencies"""
        # This is a placeholder - in real implementation, would need proper mapping
        return f"999"  # Use 999 as placeholder
    
    def create_district_json(self, district_code: str, constituencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create district JSON in the required format"""
        
        # Calculate total null votes across constituencies
        total_null_votes = sum(const.get('null_votes', 0) for const in constituencies)
        
        # Format constituencies
        formatted_constituencies = []
        for const in constituencies:
            formatted_const = {
                'code': const['code'],
                'isLegacy': False,
                'candidates': const['candidates']
            }
            formatted_constituencies.append(formatted_const)
        
        district_result = {
            'districtCode': district_code,
            'type': 'presidential',
            'nullVotes': total_null_votes,
            'constituencies': formatted_constituencies
        }
        
        return district_result
    
    def validate_result(self, district_result: Dict[str, Any]) -> bool:
        """Validate district result structure"""
        required_fields = ['districtCode', 'type', 'nullVotes', 'constituencies']
        
        for field in required_fields:
            if field not in district_result:
                print(f"Missing field: {field}")
                return False
        
        if district_result['type'] != 'presidential':
            print(f"Invalid type: {district_result['type']}")
            return False
        
        for const in district_result['constituencies']:
            required_const_fields = ['code', 'isLegacy', 'candidates']
            for field in required_const_fields:
                if field not in const:
                    print(f"Missing constituency field: {field}")
                    return False
            
            for candidate in const['candidates']:
                required_cand_fields = ['candidateCode', 'partyCode', 'votes']
                for field in required_cand_fields:
                    if field not in candidate:
                        print(f"Missing candidate field: {field}")
                        return False
        
        return True
    
    def generate_all_missing_districts(self) -> Dict[str, Dict[str, Any]]:
        """Generate all missing district JSON files"""
        
        # Load and parse PDF data
        pdf_text = self.load_pdf_text()
        results_by_district = self.extract_constituency_results(pdf_text)
        
        generated_results = {}
        
        for district_code, constituencies in results_by_district.items():
            district_result = self.create_district_json(district_code, constituencies)
            
            if self.validate_result(district_result):
                generated_results[district_code] = district_result
                print(f"Generated result for district {district_code} with {len(constituencies)} constituencies")
            else:
                print(f"Validation failed for district {district_code}")
        
        return generated_results
    
    def save_district_results(self, results: Dict[str, Dict[str, Any]], output_dir: str):
        """Save district results to JSON files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for district_code, result in results.items():
            filename = f"{district_code}_RESULTS.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Saved {filepath}")


def main():
    """Main execution function"""
    
    # Configuration
    base_dir = r"C:\Users\lacso\Git\mw-presidential-election-stats"
    pdf_text_path = os.path.join(base_dir, "data", "Constituency2020PresidentialResults.pdf.txt")
    metadata_dir = os.path.join(base_dir, "metadata")
    output_dir = os.path.join(base_dir, "2020", "results", "presidential")
    
    # Initialize extractor
    extractor = ElectionDataExtractor(pdf_text_path, metadata_dir)
    
    # Generate missing district results
    print("Extracting 2020 presidential election results...")
    results = extractor.generate_all_missing_districts()
    
    # Save results
    print(f"\nSaving results to {output_dir}...")
    extractor.save_district_results(results, output_dir)
    
    print(f"\nCompleted! Generated {len(results)} district result files.")
    print("Districts processed:", list(results.keys()))


if __name__ == "__main__":
    main()