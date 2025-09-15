#!/usr/bin/env python3
"""
Clean up parsing errors in 2019 parliamentary election data.
This script fixes common OCR and parsing artifacts in party codes.
"""

import json
import os
import re
from pathlib import Path

def clean_party_code(party_code):
    """Clean up party code parsing errors"""
    if not party_code:
        return "IND"
    
    # Dictionary of common party code fixes
    party_fixes = {
        "school": "IND",
        "chool": "IND", 
        "enter": "IND",
        "tation": "IND",
        "T/Office": "IND",
        "Office": "IND"
    }
    
    # Direct mapping if found
    if party_code in party_fixes:
        return party_fixes[party_code]
    
    # Pattern-based fixes
    # Remove numbers and location names (OCR artifacts)
    if re.match(r'^\d+[A-Za-z]+$', party_code):
        # Extract the text part after numbers
        text_part = re.sub(r'^\d+', '', party_code)
        if len(text_part) >= 3 and text_part.upper() in ['MCP', 'DPP', 'UTM', 'UDF', 'IND']:
            return text_part.upper()
        return "IND"
    
    # Handle cases like "5Namiyango", "88Mlale", etc.
    if re.match(r'^\d+[A-Z][a-z]+$', party_code):
        return "IND"
    
    # Handle XXXXX patterns (parsing errors)
    if 'XXX' in party_code:
        # Try to extract valid party code
        clean_code = re.sub(r'XXX.*$', '', party_code)
        if clean_code in ['MCP', 'DPP', 'UTM', 'UDF', 'IND', 'PP']:
            return clean_code
        return "IND"
    
    # Handle valid party codes
    valid_parties = ['MCP', 'DPP', 'UTM', 'UDF', 'IND', 'PP', 'AFORD', 'DePeCo']
    if party_code in valid_parties:
        return party_code
    
    # Default to IND for unrecognized codes
    print(f"Warning: Unknown party code '{party_code}' converted to IND")
    return "IND"

def clean_candidate_code(candidate_code):
    """Clean up candidate code parsing errors"""
    if not candidate_code:
        return "UNKNOWN"
    
    # Handle common parsing errors
    if candidate_code in ["INDXXX", "MCPXXX", "DPPXXX", "STATIO"]:
        return "UNKNOWN"
    
    # Remove non-alphabetic characters from the end
    cleaned = re.sub(r'[^A-Z]+$', '', candidate_code.upper())
    if len(cleaned) < 3:
        return "UNKNOWN"
    
    return cleaned[:6]  # Limit to 6 characters

def clean_district_file(file_path):
    """Clean a single district file"""
    print(f"Cleaning {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_candidates_cleaned = 0
    
    for constituency in data.get('constituencies', []):
        for candidate in constituency.get('candidates', []):
            original_party = candidate.get('partyCode', '')
            original_candidate = candidate.get('candidateCode', '')
            
            # Clean party code
            cleaned_party = clean_party_code(original_party)
            if cleaned_party != original_party:
                candidate['partyCode'] = cleaned_party
                total_candidates_cleaned += 1
                print(f"  Fixed party: {original_party} -> {cleaned_party}")
            
            # Clean candidate code
            cleaned_candidate = clean_candidate_code(original_candidate)
            if cleaned_candidate != original_candidate:
                candidate['candidateCode'] = cleaned_candidate
                total_candidates_cleaned += 1
                print(f"  Fixed candidate: {original_candidate} -> {cleaned_candidate}")
    
    # Write back the cleaned data
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return total_candidates_cleaned

def main():
    """Main function to clean all 2019 parliamentary files"""
    data_dir = Path("C:/Users/lacso/Git/mw-presidential-election-stats/2019/results/parliamentary")
    
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("No JSON files found in directory")
        return
    
    print(f"Found {len(json_files)} district files to clean")
    print("=" * 50)
    
    total_cleaned = 0
    
    for file_path in sorted(json_files):
        candidates_cleaned = clean_district_file(file_path)
        total_cleaned += candidates_cleaned
        
    print("=" * 50)
    print(f"Cleanup complete! Total candidate records cleaned: {total_cleaned}")
    
    # Generate a summary report
    print("\nGenerating summary report...")
    
    # Count total candidates and constituencies per district
    summary = []
    for file_path in sorted(json_files):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        district_code = data.get('districtCode', 'UNKNOWN')
        constituency_count = len(data.get('constituencies', []))
        candidate_count = sum(len(c.get('candidates', [])) for c in data.get('constituencies', []))
        total_votes = sum(sum(cand.get('votes', 0) for cand in c.get('candidates', [])) 
                         for c in data.get('constituencies', []))
        
        summary.append({
            'district': district_code,
            'constituencies': constituency_count,
            'candidates': candidate_count,
            'total_votes': total_votes
        })
    
    print("\nDistrict Summary:")
    print(f"{'District':<10} {'Constit.':<10} {'Candidates':<12} {'Total Votes':<12}")
    print("-" * 50)
    
    total_constituencies = 0
    total_candidates = 0
    total_votes = 0
    
    for item in summary:
        print(f"{item['district']:<10} {item['constituencies']:<10} {item['candidates']:<12} {item['total_votes']:<12}")
        total_constituencies += item['constituencies']
        total_candidates += item['candidates']
        total_votes += item['total_votes']
    
    print("-" * 50)
    print(f"{'TOTAL':<10} {total_constituencies:<10} {total_candidates:<12} {total_votes:<12}")

if __name__ == "__main__":
    main()