#!/usr/bin/env python3
"""
Validate the generated 2020 demographic data files for integrity and structure.
Compares against the 2025 structure and performs mathematical verification.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def validate_structure(data: Dict[str, Any], template: Dict[str, Any], filename: str) -> List[str]:
    """Validate that data matches the expected structure."""
    errors = []
    
    # Check top-level fields
    if data.get("year") != "2020":
        errors.append(f"{filename}: Expected year '2020', got '{data.get('year')}'")
    
    if "district" not in data:
        errors.append(f"{filename}: Missing 'district' field")
    
    if "demographics" not in data:
        errors.append(f"{filename}: Missing 'demographics' field")
        return errors
    
    # Check demographics structure
    demographics = data["demographics"]
    if not isinstance(demographics, list):
        errors.append(f"{filename}: 'demographics' should be a list")
        return errors
    
    template_demo = template["demographics"][0] if template["demographics"] else {}
    required_fields = set(template_demo.keys())
    
    for i, demo in enumerate(demographics):
        demo_fields = set(demo.keys())
        if demo_fields != required_fields:
            missing = required_fields - demo_fields
            extra = demo_fields - required_fields
            if missing:
                errors.append(f"{filename}: Demo {i} missing fields: {missing}")
            if extra:
                errors.append(f"{filename}: Demo {i} extra fields: {extra}")
    
    return errors

def validate_mathematics(data: Dict[str, Any], filename: str) -> List[str]:
    """Validate mathematical consistency in demographic data."""
    errors = []
    
    for i, demo in enumerate(data.get("demographics", [])):
        try:
            male_count = int(demo["registeredMale"])
            female_count = int(demo["registeredFemale"])
            male_pct_str = demo["percentageMale"].rstrip("%")
            female_pct_str = demo["percentageFemale"].rstrip("%")
            
            male_pct = float(male_pct_str)
            female_pct = float(female_pct_str)
            
            total = male_count + female_count
            if total == 0:
                continue
            
            # Check percentage calculations (allow 0.1% tolerance for rounding)
            expected_male_pct = (male_count / total) * 100
            expected_female_pct = (female_count / total) * 100
            
            if abs(male_pct - expected_male_pct) > 0.1:
                errors.append(f"{filename}: Demo {i} male percentage mismatch: {male_pct}% vs expected {expected_male_pct:.1f}%")
            
            if abs(female_pct - expected_female_pct) > 0.1:
                errors.append(f"{filename}: Demo {i} female percentage mismatch: {female_pct}% vs expected {expected_female_pct:.1f}%")
            
            # Check percentages sum to 100% (allow 0.2% tolerance)
            if abs((male_pct + female_pct) - 100.0) > 0.2:
                errors.append(f"{filename}: Demo {i} percentages don't sum to 100%: {male_pct + female_pct}%")
            
        except (ValueError, KeyError) as e:
            errors.append(f"{filename}: Demo {i} data error: {e}")
    
    return errors

def validate_constituency_codes(data: Dict[str, Any], admin_data: Dict[str, Any], filename: str) -> List[str]:
    """Validate that constituency codes are valid and correctly mapped to districts."""
    errors = []
    
    # Build constituency to district mapping
    const_to_district = {}
    for district in admin_data["districts"]:
        for constituency in district["constituencies"]:
            const_to_district[constituency["code"]] = district["code"]
    
    expected_district = data.get("district")
    if not expected_district:
        return errors
    
    for i, demo in enumerate(data.get("demographics", [])):
        const_code = demo.get("constituencyCode")
        if not const_code:
            errors.append(f"{filename}: Demo {i} missing constituencyCode")
            continue
        
        if const_code not in const_to_district:
            errors.append(f"{filename}: Demo {i} invalid constituency code: {const_code}")
            continue
        
        actual_district = const_to_district[const_code]
        if actual_district != expected_district:
            errors.append(f"{filename}: Demo {i} constituency {const_code} belongs to {actual_district}, not {expected_district}")
    
    return errors

def main():
    """Main validation function."""
    repo_root = Path.cwd()
    demographics_dir = repo_root / "2020" / "demographics"
    template_path = repo_root / "2025" / "demographics" / "BL_STATS.json"
    admin_path = repo_root / "metadata" / "administration.json"
    
    if not demographics_dir.exists():
        print("Error: 2020/demographics directory not found")
        return 1
    
    # Load template and admin data
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)
    
    with open(admin_path, "r", encoding="utf-8") as f:
        admin_data = json.load(f)
    
    # Validate all demographic files
    all_errors = []
    file_count = 0
    
    for json_file in demographics_dir.glob("*_STATS.json"):
        file_count += 1
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            filename = json_file.name
            
            # Run all validations
            all_errors.extend(validate_structure(data, template, filename))
            all_errors.extend(validate_mathematics(data, filename))
            all_errors.extend(validate_constituency_codes(data, admin_data, filename))
            
        except Exception as e:
            all_errors.append(f"{json_file.name}: Failed to load/parse: {e}")
    
    # Report results
    print(f"Validated {file_count} demographic files")
    
    if all_errors:
        print(f"\\nFound {len(all_errors)} validation errors:")
        for error in all_errors:
            print(f"  ❌ {error}")
        return 1
    else:
        print("✅ All validations passed!")
        
        # Summary statistics
        total_demographics = 0
        total_male = 0
        total_female = 0
        
        for json_file in demographics_dir.glob("*_STATS.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            total_demographics += len(data["demographics"])
            for demo in data["demographics"]:
                total_male += int(demo["registeredMale"])
                total_female += int(demo["registeredFemale"])
        
        total_registered = total_male + total_female
        if total_registered > 0:
            overall_male_pct = (total_male / total_registered) * 100
            overall_female_pct = (total_female / total_registered) * 100
            
            print(f"\\nSummary Statistics:")
            print(f"  📊 Total constituencies: {total_demographics}")
            print(f"  👨 Total male voters: {total_male:,} ({overall_male_pct:.1f}%)")
            print(f"  👩 Total female voters: {total_female:,} ({overall_female_pct:.1f}%)")
            print(f"  📋 Total registered voters: {total_registered:,}")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())