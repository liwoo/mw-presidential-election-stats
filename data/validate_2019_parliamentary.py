#!/usr/bin/env python3
"""
Validation script for 2019 parliamentary election data.
Checks data integrity, structure, and consistency.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter

def validate_district_file(file_path):
    """Validate a single district JSON file"""
    errors = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [f"Failed to load JSON: {e}"], []
    
    # Check required top-level fields
    required_fields = ['districtCode', 'type', 'constituencies']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check type is parliamentary
    if data.get('type') != 'parliamentary':
        errors.append(f"Expected type 'parliamentary', got '{data.get('type')}'")
    
    # Check district code format
    district_code = data.get('districtCode')
    if not district_code or len(district_code) != 2:
        errors.append(f"Invalid district code: {district_code}")
    
    # Check constituencies
    constituencies = data.get('constituencies', [])
    if not constituencies:
        errors.append("No constituencies found")
        return errors, warnings
    
    constituency_codes = set()
    total_candidates = 0
    total_votes = 0
    party_votes = defaultdict(int)
    
    for i, constituency in enumerate(constituencies):
        # Check constituency structure
        if 'code' not in constituency:
            errors.append(f"Constituency {i} missing code")
            continue
        
        const_code = constituency['code']
        if const_code in constituency_codes:
            errors.append(f"Duplicate constituency code: {const_code}")
        constituency_codes.add(const_code)
        
        # Check candidates
        candidates = constituency.get('candidates', [])
        if not candidates:
            warnings.append(f"Constituency {const_code} has no candidates")
            continue
        
        candidate_codes = set()
        for j, candidate in enumerate(candidates):
            # Check candidate structure
            required_cand_fields = ['candidateCode', 'partyCode', 'votes']
            for field in required_cand_fields:
                if field not in candidate:
                    errors.append(f"Constituency {const_code}, candidate {j}: missing {field}")
            
            # Check for duplicates
            cand_key = (candidate.get('candidateCode'), candidate.get('partyCode'))
            if cand_key in candidate_codes:
                errors.append(f"Constituency {const_code}: duplicate candidate {cand_key}")
            candidate_codes.add(cand_key)
            
            # Check vote count
            votes = candidate.get('votes', 0)
            if not isinstance(votes, int) or votes < 0:
                errors.append(f"Invalid vote count: {votes} for candidate {candidate.get('candidateCode')}")
            else:
                total_votes += votes
                party_votes[candidate.get('partyCode')] += votes
            
            total_candidates += 1
    
    return errors, warnings, {
        'district_code': district_code,
        'constituencies': len(constituencies),
        'candidates': total_candidates,
        'total_votes': total_votes,
        'party_votes': dict(party_votes)
    }

def main():
    """Main validation function"""
    data_dir = Path("C:/Users/lacso/Git/mw-presidential-election-stats/2019/results/parliamentary")
    
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("No JSON files found")
        return
    
    print(f"Validating {len(json_files)} district files...")
    print("=" * 60)
    
    total_errors = 0
    total_warnings = 0
    all_stats = []
    all_party_votes = defaultdict(int)
    
    for file_path in sorted(json_files):
        print(f"\nValidating {file_path.name}...")
        
        result = validate_district_file(file_path)
        if len(result) == 2:
            errors, warnings = result
            stats = None
        else:
            errors, warnings, stats = result
        
        if errors:
            print(f"  ❌ ERRORS ({len(errors)}):")
            for error in errors:
                print(f"    - {error}")
            total_errors += len(errors)
        
        if warnings:
            print(f"  ⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"    - {warning}")
            total_warnings += len(warnings)
        
        if not errors and not warnings:
            print("  ✅ VALID")
        
        if stats:
            all_stats.append(stats)
            for party, votes in stats['party_votes'].items():
                all_party_votes[party] += votes
    
    # Summary report
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if total_errors == 0 and total_warnings == 0:
        print("🎉 ALL FILES PASSED VALIDATION!")
    else:
        print(f"Total errors: {total_errors}")
        print(f"Total warnings: {total_warnings}")
    
    if all_stats:
        print("\nDATA SUMMARY:")
        print(f"Districts: {len(all_stats)}")
        print(f"Total constituencies: {sum(s['constituencies'] for s in all_stats)}")
        print(f"Total candidates: {sum(s['candidates'] for s in all_stats)}")
        print(f"Total votes: {sum(s['total_votes'] for s in all_stats):,}")
        
        print("\nVOTES BY PARTY:")
        sorted_parties = sorted(all_party_votes.items(), key=lambda x: x[1], reverse=True)
        for party, votes in sorted_parties:
            percentage = (votes / sum(all_party_votes.values())) * 100 if sum(all_party_votes.values()) > 0 else 0
            print(f"  {party:<10}: {votes:>10,} ({percentage:5.1f}%)")
        
        print("\nDISTRICT BREAKDOWN:")
        print(f"{'District':<8} {'Const.':<6} {'Cand.':<6} {'Votes':<12}")
        print("-" * 35)
        for stats in sorted(all_stats, key=lambda x: x['district_code']):
            print(f"{stats['district_code']:<8} {stats['constituencies']:<6} {stats['candidates']:<6} {stats['total_votes']:<12,}")

if __name__ == "__main__":
    main()