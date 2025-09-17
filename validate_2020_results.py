#!/usr/bin/env python3
"""
Validate 2020 Presidential Election Results JSON Files
Verifies structure, data integrity, and completeness of generated district files
"""

import json
import os
from typing import Dict, List, Any
import sys

class ResultsValidator:
    """Validate 2020 presidential election results"""
    
    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        self.errors = []
        self.warnings = []
        
    def validate_file_structure(self, filepath: str) -> Dict[str, Any]:
        """Validate the structure of a single result file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.errors.append(f"Failed to load {filepath}: {e}")
            return None
        
        # Check required fields
        required_fields = ['districtCode', 'type', 'nullVotes', 'constituencies']
        for field in required_fields:
            if field not in data:
                self.errors.append(f"{filepath}: Missing field '{field}'")
        
        # Validate field values
        if 'type' in data and data['type'] != 'presidential':
            self.errors.append(f"{filepath}: Invalid type '{data['type']}', expected 'presidential'")
        
        if 'nullVotes' in data and not isinstance(data['nullVotes'], int):
            self.errors.append(f"{filepath}: nullVotes must be integer, got {type(data['nullVotes'])}")
        
        # Validate constituencies
        if 'constituencies' in data:
            for i, const in enumerate(data['constituencies']):
                self.validate_constituency(filepath, i, const)
        
        return data
    
    def validate_constituency(self, filepath: str, index: int, constituency: Dict[str, Any]):
        """Validate a constituency structure"""
        required_fields = ['code', 'isLegacy', 'candidates']
        for field in required_fields:
            if field not in constituency:
                self.errors.append(f"{filepath}: Constituency {index} missing field '{field}'")
        
        # Validate candidates
        if 'candidates' in constituency:
            expected_candidates = {'LAZCHA', 'PETKUW', 'PETMUT'}
            found_candidates = set()
            
            for j, candidate in enumerate(constituency['candidates']):
                self.validate_candidate(filepath, index, j, candidate)
                if 'candidateCode' in candidate:
                    found_candidates.add(candidate['candidateCode'])
            
            # Check we have all expected candidates
            missing_candidates = expected_candidates - found_candidates
            if missing_candidates:
                self.warnings.append(f"{filepath}: Constituency {index} missing candidates: {missing_candidates}")
            
            # Check for unexpected candidates
            extra_candidates = found_candidates - expected_candidates
            if extra_candidates:
                self.warnings.append(f"{filepath}: Constituency {index} has unexpected candidates: {extra_candidates}")
    
    def validate_candidate(self, filepath: str, const_idx: int, cand_idx: int, candidate: Dict[str, Any]):
        """Validate a candidate structure"""
        required_fields = ['candidateCode', 'partyCode', 'votes']
        for field in required_fields:
            if field not in candidate:
                self.errors.append(f"{filepath}: Constituency {const_idx}, Candidate {cand_idx} missing field '{field}'")
        
        # Validate votes is integer
        if 'votes' in candidate and not isinstance(candidate['votes'], int):
            self.errors.append(f"{filepath}: Constituency {const_idx}, Candidate {cand_idx} votes must be integer")
        
        # Validate candidate-party combinations
        expected_combinations = {
            'LAZCHA': 'MCP',
            'PETKUW': 'MMD', 
            'PETMUT': 'DPP'
        }
        
        if 'candidateCode' in candidate and 'partyCode' in candidate:
            candidate_code = candidate['candidateCode']
            party_code = candidate['partyCode']
            
            if candidate_code in expected_combinations:
                expected_party = expected_combinations[candidate_code]
                if party_code != expected_party:
                    self.errors.append(f"{filepath}: {candidate_code} should have party {expected_party}, got {party_code}")
    
    def validate_all_files(self) -> Dict[str, Dict[str, Any]]:
        """Validate all result files in the directory"""
        results = {}
        
        if not os.path.exists(self.results_dir):
            self.errors.append(f"Results directory not found: {self.results_dir}")
            return results
        
        # Get all JSON files
        files = [f for f in os.listdir(self.results_dir) if f.endswith('_RESULTS.json')]
        
        print(f"Found {len(files)} result files to validate...")
        
        for filename in sorted(files):
            filepath = os.path.join(self.results_dir, filename)
            district_code = filename.replace('_RESULTS.json', '')
            
            print(f"Validating {district_code}...")
            data = self.validate_file_structure(filepath)
            
            if data:
                results[district_code] = data
                
                # Check district code consistency
                if 'districtCode' in data and data['districtCode'] != district_code:
                    self.errors.append(f"{filename}: District code mismatch. Filename suggests {district_code}, content has {data['districtCode']}")
        
        return results
    
    def generate_summary(self, results: Dict[str, Dict[str, Any]]):
        """Generate a summary of the validation results"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total files validated: {len(results)}")
        print(f"Errors found: {len(self.errors)}")
        print(f"Warnings found: {len(self.warnings)}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        # District summary
        print(f"\nDISTRICT SUMMARY:")
        print(f"{'District':<12} {'Constituencies':<15} {'Total Votes':<12} {'Null Votes':<10}")
        print("-" * 60)
        
        total_constituencies = 0
        total_votes = 0
        total_null_votes = 0
        
        for district_code in sorted(results.keys()):
            data = results[district_code]
            const_count = len(data.get('constituencies', []))
            null_votes = data.get('nullVotes', 0)
            
            # Calculate total votes for district
            district_total_votes = 0
            for const in data.get('constituencies', []):
                for candidate in const.get('candidates', []):
                    district_total_votes += candidate.get('votes', 0)
            
            print(f"{district_code:<12} {const_count:<15} {district_total_votes:<12} {null_votes:<10}")
            
            total_constituencies += const_count
            total_votes += district_total_votes
            total_null_votes += null_votes
        
        print("-" * 60)
        print(f"{'TOTAL':<12} {total_constituencies:<15} {total_votes:<12} {total_null_votes:<10}")
        
        # Top performers summary
        print(f"\nCANDIDATE PERFORMANCE SUMMARY:")
        candidate_totals = {'LAZCHA': 0, 'PETKUW': 0, 'PETMUT': 0}
        
        for data in results.values():
            for const in data.get('constituencies', []):
                for candidate in const.get('candidates', []):
                    code = candidate.get('candidateCode', '')
                    votes = candidate.get('votes', 0)
                    if code in candidate_totals:
                        candidate_totals[code] += votes
        
        for candidate_code, votes in sorted(candidate_totals.items(), key=lambda x: x[1], reverse=True):
            party_map = {'LAZCHA': 'MCP', 'PETKUW': 'MMD', 'PETMUT': 'DPP'}
            party = party_map.get(candidate_code, 'Unknown')
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            print(f"  {candidate_code} ({party}): {votes:,} votes ({percentage:.1f}%)")
        
        print("\n" + "="*60)
        
        return len(self.errors) == 0

def main():
    """Main validation function"""
    results_dir = r"C:\Users\lacso\Git\mw-presidential-election-stats\2020\results\presidential"
    
    validator = ResultsValidator(results_dir)
    results = validator.validate_all_files()
    success = validator.generate_summary(results)
    
    if success:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())