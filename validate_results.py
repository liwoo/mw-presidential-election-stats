#!/usr/bin/env python3
"""
Final validation script for parliamentary results
Validates all generated JSON files against the required structure
"""

import json
import os
from pathlib import Path

def validate_file_structure(file_path):
    """Validate individual JSON file structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Required fields
        required_fields = ['districtCode', 'type', 'nullVotes', 'constituencies']
        for field in required_fields:
            if field not in data:
                return False, f"Missing field: {field}"
        
        # Type should be parliamentary
        if data['type'] != 'parliamentary':
            return False, f"Invalid type: {data['type']}"
        
        # Validate constituencies
        if not isinstance(data['constituencies'], list):
            return False, "constituencies must be a list"
        
        for constituency in data['constituencies']:
            const_required = ['code', 'isLegacy', 'candidates']
            for field in const_required:
                if field not in constituency:
                    return False, f"Missing constituency field: {field}"
            
            # Validate candidates
            if not isinstance(constituency['candidates'], list):
                return False, "candidates must be a list"
            
            for candidate in constituency['candidates']:
                cand_required = ['candidateCode', 'partyCode', 'votes']
                for field in cand_required:
                    if field not in candidate:
                        return False, f"Missing candidate field: {field}"
                
                # Votes should be integer
                if not isinstance(candidate['votes'], int):
                    return False, f"votes must be integer, got {type(candidate['votes'])}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main validation function"""
    base_path = Path(r"C:\Users\lacso\Git\mw-presidential-election-stats")
    results_dir = base_path / "2014" / "results" / "parliamentary"
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    files = list(results_dir.glob("*.json"))
    
    print("🔍 VALIDATING PARLIAMENTARY RESULTS FILES")
    print("=" * 50)
    
    valid_files = 0
    total_constituencies = 0
    total_candidates = 0
    total_votes = 0
    
    for file_path in sorted(files):
        is_valid, message = validate_file_structure(file_path)
        
        if is_valid:
            valid_files += 1
            print(f"✅ {file_path.name}: {message}")
            
            # Count statistics
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                constituencies = len(data['constituencies'])
                candidates = sum(len(c['candidates']) for c in data['constituencies'])
                votes = sum(sum(cand['votes'] for cand in c['candidates']) for c in data['constituencies'])
                
                total_constituencies += constituencies
                total_candidates += candidates
                total_votes += votes
                
                print(f"   📊 {constituencies} constituencies, {candidates} candidates, {votes:,} votes")
        else:
            print(f"❌ {file_path.name}: {message}")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print(f"✅ Valid files: {valid_files}/{len(files)}")
    print(f"📍 Total constituencies: {total_constituencies}")
    print(f"👥 Total candidates: {total_candidates}")
    print(f"🗳️  Total votes: {total_votes:,}")
    
    if valid_files == len(files):
        print("\n🎉 ALL FILES VALIDATED SUCCESSFULLY!")
    else:
        print(f"\n⚠️  {len(files) - valid_files} files failed validation")

if __name__ == "__main__":
    main()