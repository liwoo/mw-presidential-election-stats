#!/usr/bin/env python3
"""
Create empty parliamentary district files for missing 2019 districts.
These districts exist in presidential data but not in parliamentary data.
"""

import json
from pathlib import Path

def create_empty_district_file(district_code: str, output_dir: Path):
    """Create an empty district file with proper structure"""
    
    # District name mappings
    district_names = {
        'BA': 'Balaka',
        'CK': 'Chikwawa', 
        'CR': 'Chiradzulu',
        'DE': 'Dedza',
        'DO': 'Dowa',
        'LK': 'Likoma',
        'MC': 'Mchinji',
        'NB': 'Nkhotakota', # Note: NK is already handled, this might be Nkhatabay
        'NE': 'Neno',
        'RU': 'Rumphi',
        'ZU': 'Mzuzu City'
    }
    
    district_data = {
        "districtCode": district_code,
        "type": "parliamentary",
        "nullVotes": 0,
        "constituencies": []
    }
    
    output_file = output_dir / f"{district_code}_RESULTS.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(district_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created empty district file: {output_file}")
    return output_file

def main():
    """Main function to create missing district files"""
    
    # Missing districts from parliamentary data
    missing_districts = ['BA', 'CK', 'CR', 'DE', 'DO', 'LK', 'MC', 'NB', 'NE', 'RU', 'ZU']
    
    output_dir = Path("C:/Users/lacso/Git/mw-presidential-election-stats/2019/results/parliamentary")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating empty district files for {len(missing_districts)} missing districts...")
    print("=" * 60)
    
    created_files = []
    
    for district_code in missing_districts:
        try:
            file_path = create_empty_district_file(district_code, output_dir)
            created_files.append(file_path)
        except Exception as e:
            print(f"Error creating file for district {district_code}: {e}")
    
    print("=" * 60)
    print(f"Successfully created {len(created_files)} empty district files")
    
    # Now check total count
    all_files = list(output_dir.glob("*.json"))
    print(f"Total district files in parliamentary directory: {len(all_files)}")
    
    # List all districts
    all_districts = sorted([f.stem.replace('_RESULTS', '') for f in all_files])
    print(f"All districts: {', '.join(all_districts)}")
    
    # Compare with presidential
    presidential_dir = Path("C:/Users/lacso/Git/mw-presidential-election-stats/2019/results/presidential")
    presidential_files = list(presidential_dir.glob("*.json"))
    presidential_districts = sorted([f.stem.replace('_RESULTS', '') for f in presidential_files])
    
    print(f"\\nComparison:")
    print(f"Presidential districts ({len(presidential_districts)}): {', '.join(presidential_districts)}")
    print(f"Parliamentary districts ({len(all_districts)}): {', '.join(all_districts)}")
    
    missing_from_parliamentary = set(presidential_districts) - set(all_districts)
    extra_in_parliamentary = set(all_districts) - set(presidential_districts)
    
    if missing_from_parliamentary:
        print(f"\\nStill missing from parliamentary: {', '.join(sorted(missing_from_parliamentary))}")
    
    if extra_in_parliamentary:
        print(f"\\nExtra in parliamentary: {', '.join(sorted(extra_in_parliamentary))}")
    
    if len(all_districts) == len(presidential_districts) and not missing_from_parliamentary:
        print(f"\\n✅ SUCCESS: Parliamentary district count now matches presidential ({len(all_districts)} districts)")
    else:
        print(f"\\n⚠️  WARNING: District counts still don't match")

if __name__ == "__main__":
    main()