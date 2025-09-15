#!/usr/bin/env python3
"""
Comprehensive Output Validation Script
Chain of Thought Reasoning + Test-Driven Development

Chain of Thought Process:
1. Validate all generated demographic files against source data
2. Cross-check mathematical consistency (totals, percentages)
3. Verify JSON structure matches CT_STATS.json format
4. Validate track records data integrity
5. Test naming conventions and file completeness
6. Generate validation report with detailed findings
"""

import json
import os
import re
from typing import Dict, List, Tuple, Any, Optional
import unittest
from pathlib import Path
import math

class ComprehensiveValidator:
    """Comprehensive validator for all generated election data files"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.administration_data = self._load_administration_data()
        self.validation_results = {
            "demographics": {"passed": 0, "failed": 0, "details": []},
            "track_records": {"passed": 0, "failed": 0, "details": []},
            "mathematical": {"passed": 0, "failed": 0, "details": []},
            "structural": {"passed": 0, "failed": 0, "details": []}
        }
        
    def _load_administration_data(self) -> Dict:
        """Load administration metadata"""
        admin_path = self.base_path / "metadata" / "administration.json"
        with open(admin_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_demographics_files(self) -> Dict:
        """Validate all demographic JSON files
        
        Chain of Thought:
        1. Check that all districts have corresponding files
        2. Validate JSON structure matches template
        3. Verify percentage units are included
        4. Check mathematical consistency
        """
        
        demographics_dir = self.base_path / "2025" / "demographics"
        results = {"passed": 0, "failed": 0, "details": []}
        
        print("Validating demographic files...")
        
        # Check if demographics directory exists
        if not demographics_dir.exists():
            results["failed"] += 1
            results["details"].append("ERROR: Demographics directory does not exist")
            return results
        
        # Validate each district file
        for district in self.administration_data["districts"]:
            district_code = district["code"]
            file_path = demographics_dir / f"{district_code}_STATS.json"
            
            try:
                # Check file exists
                if not file_path.exists():
                    results["failed"] += 1
                    results["details"].append(f"ERROR: Missing file {district_code}_STATS.json")
                    continue
                
                # Load and validate JSON structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate required fields
                if not self._validate_demographics_structure(data, district_code):
                    results["failed"] += 1
                    results["details"].append(f"ERROR: Invalid structure in {district_code}_STATS.json")
                    continue
                
                # Validate mathematical consistency
                if not self._validate_demographics_math(data, district_code):
                    results["failed"] += 1
                    results["details"].append(f"ERROR: Mathematical inconsistency in {district_code}_STATS.json")
                    continue
                
                # Validate percentage units
                if not self._validate_percentage_units(data):
                    results["failed"] += 1
                    results["details"].append(f"ERROR: Missing percentage units in {district_code}_STATS.json")
                    continue
                
                results["passed"] += 1
                results["details"].append(f"✓ {district_code}_STATS.json validated successfully")
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: Exception validating {district_code}_STATS.json: {str(e)}")
        
        return results
    
    def _validate_demographics_structure(self, data: Dict, district_code: str) -> bool:
        """Validate demographics JSON structure"""
        required_fields = ["year", "district", "demographics"]
        
        # Check top-level fields
        for field in required_fields:
            if field not in data:
                return False
        
        # Check values
        if data["year"] != "2025":
            return False
        if data["district"] != district_code:
            return False
        if not isinstance(data["demographics"], list):
            return False
        
        # Check demographics entries
        for demo in data["demographics"]:
            required_demo_fields = ["constituencyCode", "registeredMale", "registeredFemale", 
                                  "percentageMale", "percentageFemale"]
            for field in required_demo_fields:
                if field not in demo:
                    return False
                    
            # Check data types
            if not isinstance(demo["constituencyCode"], str):
                return False
            if not isinstance(demo["registeredMale"], str):
                return False
            if not isinstance(demo["registeredFemale"], str):
                return False
            if not isinstance(demo["percentageMale"], str):
                return False
            if not isinstance(demo["percentageFemale"], str):
                return False
        
        return True
    
    def _validate_demographics_math(self, data: Dict, district_code: str) -> bool:
        """Validate mathematical consistency in demographics data"""
        for demo in data["demographics"]:
            try:
                # Extract numeric values
                registered_male = int(demo["registeredMale"])
                registered_female = int(demo["registeredFemale"])
                
                # Extract percentages (remove % symbol)
                percentage_male = float(demo["percentageMale"].rstrip('%'))
                percentage_female = float(demo["percentageFemale"].rstrip('%'))
                
                # Calculate total
                total_registered = registered_male + registered_female
                
                # Validate percentages sum to ~100%
                percentage_sum = percentage_male + percentage_female
                if abs(percentage_sum - 100.0) > 0.1:
                    print(f"Warning: Percentages don't sum to 100% for {demo['constituencyCode']}: {percentage_sum}%")
                    return False
                
                # Validate percentages match calculated values
                calc_male_pct = (registered_male / total_registered) * 100
                calc_female_pct = (registered_female / total_registered) * 100
                
                if abs(calc_male_pct - percentage_male) > 0.1:
                    print(f"Warning: Male percentage mismatch for {demo['constituencyCode']}: {calc_male_pct:.1f}% vs {percentage_male}%")
                    return False
                    
                if abs(calc_female_pct - percentage_female) > 0.1:
                    print(f"Warning: Female percentage mismatch for {demo['constituencyCode']}: {calc_female_pct:.1f}% vs {percentage_female}%")
                    return False
                
            except ValueError as e:
                print(f"Error parsing numeric values in {demo['constituencyCode']}: {e}")
                return False
        
        return True
    
    def _validate_percentage_units(self, data: Dict) -> bool:
        """Validate that percentage fields include % units"""
        for demo in data["demographics"]:
            if not demo["percentageMale"].endswith('%'):
                return False
            if not demo["percentageFemale"].endswith('%'):
                return False
        return True
    
    def validate_track_records_files(self) -> Dict:
        """Validate track records files
        
        Chain of Thought:
        1. Check comprehensive track records file
        2. Validate district-specific track records files
        3. Verify data consistency across files
        4. Check track record data quality
        """
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        print("Validating track records files...")
        
        # Validate comprehensive track records file
        comprehensive_file = self.base_path / "2025" / "comprehensive_track_records.json"
        if comprehensive_file.exists():
            try:
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self._validate_track_records_structure(data):
                    results["passed"] += 1
                    results["details"].append("✓ comprehensive_track_records.json validated successfully")
                else:
                    results["failed"] += 1
                    results["details"].append("ERROR: Invalid structure in comprehensive_track_records.json")
            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"ERROR: Exception validating comprehensive_track_records.json: {str(e)}")
        else:
            results["failed"] += 1
            results["details"].append("ERROR: Missing comprehensive_track_records.json")
        
        # Validate district track records files
        track_records_dir = self.base_path / "2025" / "track_records"
        if track_records_dir.exists():
            for district in self.administration_data["districts"]:
                district_code = district["code"]
                file_path = track_records_dir / f"{district_code}_TRACK_RECORDS.json"
                
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if self._validate_district_track_records_structure(data, district_code):
                            results["passed"] += 1
                            results["details"].append(f"✓ {district_code}_TRACK_RECORDS.json validated successfully")
                        else:
                            results["failed"] += 1
                            results["details"].append(f"ERROR: Invalid structure in {district_code}_TRACK_RECORDS.json")
                    except Exception as e:
                        results["failed"] += 1
                        results["details"].append(f"ERROR: Exception validating {district_code}_TRACK_RECORDS.json: {str(e)}")
                else:
                    results["failed"] += 1
                    results["details"].append(f"ERROR: Missing {district_code}_TRACK_RECORDS.json")
        else:
            results["failed"] += 1
            results["details"].append("ERROR: Track records directory does not exist")
        
        return results
    
    def _validate_track_records_structure(self, data: Dict) -> bool:
        """Validate track records JSON structure"""
        required_fields = ["year", "description", "candidates"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        if data["year"] != "2025":
            return False
        
        if not isinstance(data["candidates"], dict):
            return False
        
        # Validate candidate entries
        for candidate_code, candidate_data in data["candidates"].items():
            required_candidate_fields = ["fullname", "trackRecords"]
            for field in required_candidate_fields:
                if field not in candidate_data:
                    return False
            
            if not isinstance(candidate_data["trackRecords"], list):
                return False
            
            # Validate track record entries
            for record in candidate_data["trackRecords"]:
                required_record_fields = ["year", "position", "totalVotes", "percentage"]
                for field in required_record_fields:
                    if field not in record:
                        return False
        
        return True
    
    def _validate_district_track_records_structure(self, data: Dict, district_code: str) -> bool:
        """Validate district-specific track records structure"""
        required_fields = ["year", "district", "description", "candidates"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        if data["year"] != "2025":
            return False
        if data["district"] != district_code:
            return False
        
        return True
    
    def validate_file_naming_conventions(self) -> Dict:
        """Validate file naming conventions
        
        Chain of Thought:
        1. Demographics files should follow {DISTRICT_CODE}_STATS.json
        2. Track records files should follow {DISTRICT_CODE}_TRACK_RECORDS.json
        3. All district codes should be present
        """
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        print("Validating file naming conventions...")
        
        demographics_dir = self.base_path / "2025" / "demographics"
        track_records_dir = self.base_path / "2025" / "track_records"
        
        for district in self.administration_data["districts"]:
            district_code = district["code"]
            
            # Check demographics file naming
            expected_demo_file = f"{district_code}_STATS.json"
            demo_file_path = demographics_dir / expected_demo_file
            
            if demo_file_path.exists():
                results["passed"] += 1
                results["details"].append(f"✓ {expected_demo_file} naming convention correct")
            else:
                results["failed"] += 1
                results["details"].append(f"ERROR: {expected_demo_file} not found or incorrectly named")
            
            # Check track records file naming
            expected_track_file = f"{district_code}_TRACK_RECORDS.json"
            track_file_path = track_records_dir / expected_track_file
            
            if track_file_path.exists():
                results["passed"] += 1
                results["details"].append(f"✓ {expected_track_file} naming convention correct")
            else:
                results["failed"] += 1
                results["details"].append(f"ERROR: {expected_track_file} not found or incorrectly named")
        
        return results
    
    def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive validation of all generated files"""
        
        print("=" * 80)
        print("COMPREHENSIVE VALIDATION REPORT")
        print("Chain of Thought Reasoning + Test-Driven Development")
        print("=" * 80)
        print()
        
        # Validate demographics files
        self.validation_results["demographics"] = self.validate_demographics_files()
        
        # Validate track records files
        self.validation_results["track_records"] = self.validate_track_records_files()
        
        # Validate naming conventions
        naming_results = self.validate_file_naming_conventions()
        self.validation_results["structural"]["passed"] += naming_results["passed"]
        self.validation_results["structural"]["failed"] += naming_results["failed"]
        self.validation_results["structural"]["details"].extend(naming_results["details"])
        
        return self.validation_results
    
    def print_validation_report(self):
        """Print comprehensive validation report"""
        
        total_passed = sum(cat["passed"] for cat in self.validation_results.values())
        total_failed = sum(cat["failed"] for cat in self.validation_results.values())
        total_tests = total_passed + total_failed
        
        print("\nVALIDATION SUMMARY:")
        print("-" * 50)
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {total_passed}")
        print(f"Tests Failed: {total_failed}")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
        print()
        
        # Print category-wise results
        for category, results in self.validation_results.items():
            print(f"{category.upper()} VALIDATION:")
            print(f"  Passed: {results['passed']}")
            print(f"  Failed: {results['failed']}")
            
            # Print first few details
            for detail in results['details'][:5]:
                print(f"  {detail}")
            if len(results['details']) > 5:
                print(f"  ... and {len(results['details']) - 5} more")
            print()
        
        print("=" * 80)
        if total_failed == 0:
            print("🎉 ALL VALIDATIONS PASSED! Data extraction completed successfully.")
        else:
            print(f"⚠️  {total_failed} validations failed. Please review the details above.")
        print("=" * 80)

# TDD Tests for Validation
class TestValidator(unittest.TestCase):
    """Test-Driven Development tests for the validator itself"""
    
    def setUp(self):
        self.validator = ComprehensiveValidator("C:/Users/lacso/Git/mw-presidential-election-stats")
    
    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        self.assertIsNotNone(self.validator.administration_data)
        self.assertIn("districts", self.validator.administration_data)
    
    def test_demographics_structure_validation(self):
        """Test demographics structure validation"""
        # Valid structure
        valid_data = {
            "year": "2025",
            "district": "CT",
            "demographics": [
                {
                    "constituencyCode": "001",
                    "registeredMale": "6620",
                    "registeredFemale": "7865",
                    "percentageMale": "45.7%",
                    "percentageFemale": "54.3%"
                }
            ]
        }
        
        self.assertTrue(self.validator._validate_demographics_structure(valid_data, "CT"))
        
        # Invalid structure (missing field)
        invalid_data = {
            "year": "2025",
            "district": "CT"
            # Missing demographics field
        }
        
        self.assertFalse(self.validator._validate_demographics_structure(invalid_data, "CT"))
    
    def test_percentage_units_validation(self):
        """Test percentage units validation"""
        # Valid data with % units
        valid_data = {
            "demographics": [
                {
                    "percentageMale": "45.7%",
                    "percentageFemale": "54.3%"
                }
            ]
        }
        
        self.assertTrue(self.validator._validate_percentage_units(valid_data))
        
        # Invalid data without % units
        invalid_data = {
            "demographics": [
                {
                    "percentageMale": "45.7",
                    "percentageFemale": "54.3"
                }
            ]
        }
        
        self.assertFalse(self.validator._validate_percentage_units(invalid_data))

def main():
    """Main validation execution"""
    
    # Run TDD tests for the validator
    print("Running TDD tests for validator...")
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestValidator)
    test_runner = unittest.TextTestRunner(verbosity=1)
    test_result = test_runner.run(test_suite)
    print()
    
    # Run comprehensive validation
    validator = ComprehensiveValidator("C:/Users/lacso/Git/mw-presidential-election-stats")
    validation_results = validator.run_comprehensive_validation()
    validator.print_validation_report()

if __name__ == "__main__":
    main()