#!/usr/bin/env python3
"""
Test Suite for Presidential Election Data Extractor
==================================================
Test-Driven Development (TDD) approach for validating presidential election data
extraction and JSON generation.

Testing Strategy:
1. Test metadata loading and validation
2. Test JSON structure compliance
3. Test data integrity and consistency
4. Test file naming conventions
5. Test presidential-specific requirements
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, mock_open

# Import our extractor (assuming it's in the same directory)
try:
    from extract_presidential_data import PresidentialDataExtractor, Candidate, Constituency, DistrictResults
except ImportError:
    # If running tests independently
    import sys
    sys.path.append('.')
    from extract_presidential_data import PresidentialDataExtractor, Candidate, Constituency, DistrictResults


class TestPresidentialDataExtractor(unittest.TestCase):
    """Test cases for PresidentialDataExtractor using TDD methodology"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.metadata_dir = Path(self.test_dir) / "metadata"
        self.data_dir = Path(self.test_dir) / "data"
        self.metadata_dir.mkdir()
        self.data_dir.mkdir()
        
        # Create mock metadata files
        self._create_mock_metadata()
        
        # Change to test directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def _create_mock_metadata(self):
        """Create mock metadata files for testing"""
        # Administration metadata
        admin_data = {
            "districts": [
                {
                    "code": "CT",
                    "name": "Chitipa",
                    "region": "northern",
                    "constituencies": [
                        {"code": "001", "name": "Chitipa North"},
                        {"code": "002", "name": "Chitipa Central"}
                    ]
                },
                {
                    "code": "KR",
                    "name": "Karonga", 
                    "region": "northern",
                    "constituencies": [
                        {"code": "006", "name": "Karonga Songwe"},
                        {"code": "007", "name": "Karonga Lufilya"}
                    ]
                }
            ]
        }
        
        # Candidates metadata
        candidates_data = [
            {
                "code": "LAZCHA",
                "firstname": "Lazarus",
                "lastname": "Chakwera",
                "fullname": "Dr. Lazarus Mccarthy Chakwera",
                "gender": "Male"
            },
            {
                "code": "PETMUT",
                "firstname": "Peter",
                "lastname": "Mutharika", 
                "fullname": "Prof. Peter Mutharika",
                "gender": "Male"
            },
            {
                "code": "ATUMUL",
                "firstname": "Atupele",
                "lastname": "Muluzi",
                "fullname": "Atupele Muluzi",
                "gender": "Male"
            }
        ]
        
        # Parties metadata
        parties_data = [
            {"code": "MCP", "name": "Malawi Congress Party", "abbreviation": "MCP"},
            {"code": "DPP", "name": "Democratic Progressive Party", "abbreviation": "DPP"},
            {"code": "UTM", "name": "UTM Party", "abbreviation": "UTM"},
            {"code": "UDF", "name": "United Democratic Front", "abbreviation": "UDF"},
            {"code": "IND", "name": "Independent", "abbreviation": "IND"}
        ]
        
        # Write metadata files
        with open(self.metadata_dir / "administration.json", 'w') as f:
            json.dump(admin_data, f)
        
        with open(self.metadata_dir / "candidates.json", 'w') as f:
            json.dump(candidates_data, f)
            
        with open(self.metadata_dir / "parties.json", 'w') as f:
            json.dump(parties_data, f)
    
    def test_metadata_loading(self):
        """Test that metadata is loaded correctly"""
        extractor = PresidentialDataExtractor()
        
        # Test districts loading
        self.assertIn("CT", extractor.districts)
        self.assertIn("KR", extractor.districts)
        self.assertEqual(extractor.districts["CT"]["name"], "Chitipa")
        
        # Test candidates loading
        self.assertIn("LAZCHA", extractor.candidates)
        self.assertIn("PETMUT", extractor.candidates)
        self.assertEqual(extractor.candidates["LAZCHA"]["firstname"], "Lazarus")
        
        # Test parties loading
        self.assertIn("MCP", extractor.parties)
        self.assertIn("DPP", extractor.parties)
        self.assertEqual(extractor.parties["MCP"]["name"], "Malawi Congress Party")
    
    def test_candidate_lookup_creation(self):
        """Test candidate lookup dictionary creation"""
        extractor = PresidentialDataExtractor()
        
        # Test lookup by various name formats
        self.assertEqual(extractor.candidate_lookup["CHAKWERA"], "LAZCHA")
        self.assertEqual(extractor.candidate_lookup["LAZARUS"], "LAZCHA")
        self.assertEqual(extractor.candidate_lookup["LAZARUS CHAKWERA"], "LAZCHA")
        self.assertEqual(extractor.candidate_lookup["DR. LAZARUS MCCARTHY CHAKWERA"], "LAZCHA")
    
    def test_json_structure_compliance(self):
        """Test that generated JSON follows the correct structure"""
        extractor = PresidentialDataExtractor()
        
        # Create sample data
        sample_results = extractor.create_sample_data_for_testing("2020")
        
        # Generate JSON for one district
        extractor.generate_json_files(sample_results[:1], "2020")
        
        # Read generated file
        json_file = Path("2020/results/presidential/CT_RESULTS.json")
        self.assertTrue(json_file.exists())
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Test required fields
        self.assertIn("districtCode", data)
        self.assertIn("type", data)
        self.assertIn("nullVotes", data)
        self.assertIn("constituencies", data)
        
        # Test field values
        self.assertEqual(data["type"], "presidential")
        self.assertEqual(data["districtCode"], "CT")
        self.assertIsInstance(data["nullVotes"], int)
        self.assertIsInstance(data["constituencies"], list)
        
        # Test constituency structure
        if data["constituencies"]:
            constituency = data["constituencies"][0]
            self.assertIn("code", constituency)
            self.assertIn("isLegacy", constituency)
            self.assertIn("candidates", constituency)
            
            # Test candidate structure
            if constituency["candidates"]:
                candidate = constituency["candidates"][0]
                self.assertIn("candidateCode", candidate)
                self.assertIn("partyCode", candidate)
                self.assertIn("votes", candidate)
                self.assertIsInstance(candidate["votes"], int)
    
    def test_file_naming_convention(self):
        """Test that files follow the correct naming convention"""
        extractor = PresidentialDataExtractor()
        
        # Create sample data for multiple districts
        sample_results = extractor.create_sample_data_for_testing("2019")
        extractor.generate_json_files(sample_results, "2019")
        
        # Check file names
        results_dir = Path("2019/results/presidential")
        self.assertTrue(results_dir.exists())
        
        json_files = list(results_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0)
        
        for json_file in json_files:
            # Should match pattern: {DISTRICT_CODE}_RESULTS.json
            self.assertTrue(json_file.name.endswith("_RESULTS.json"))
            
            district_code = json_file.name.replace("_RESULTS.json", "")
            self.assertEqual(len(district_code), 2)  # District codes are 2 letters
            
            # Verify district code exists in metadata
            self.assertIn(district_code, extractor.districts)
    
    def test_presidential_type_consistency(self):
        """Test that all generated files have type='presidential'"""
        extractor = PresidentialDataExtractor()
        
        for year in ["2019", "2020"]:
            sample_results = extractor.create_sample_data_for_testing(year)
            extractor.generate_json_files(sample_results, year)
            
            results_dir = Path(f"{year}/results/presidential")
            json_files = list(results_dir.glob("*.json"))
            
            for json_file in json_files:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                self.assertEqual(data["type"], "presidential")
    
    def test_candidate_party_mapping(self):
        """Test that candidates are mapped to correct parties by year"""
        extractor = PresidentialDataExtractor()
        
        # Test 2019 mapping
        party_2019 = extractor._get_candidate_party("LAZCHA", "2019")
        self.assertEqual(party_2019, "MCP")
        
        party_2019 = extractor._get_candidate_party("PETMUT", "2019")
        self.assertEqual(party_2019, "DPP")
        
        # Test 2020 mapping
        party_2020 = extractor._get_candidate_party("LAZCHA", "2020")
        self.assertEqual(party_2020, "MCP")
        
        party_2020 = extractor._get_candidate_party("ATUMUL", "2020")
        self.assertEqual(party_2020, "UTM")
    
    def test_data_integrity(self):
        """Test data integrity and consistency"""
        extractor = PresidentialDataExtractor()
        
        sample_results = extractor.create_sample_data_for_testing("2020")
        
        for district_result in sample_results:
            # Test district code validity
            self.assertIn(district_result.district_code, extractor.districts)
            
            # Test null votes are non-negative
            self.assertGreaterEqual(district_result.null_votes, 0)
            
            for constituency in district_result.constituencies:
                # Test constituency code validity
                district = extractor.districts[district_result.district_code]
                const_codes = [c["code"] for c in district["constituencies"]]
                self.assertIn(constituency.code, const_codes)
                
                for candidate in constituency.candidates:
                    # Test candidate code validity
                    self.assertIn(candidate.code, extractor.candidates)
                    
                    # Test party code validity
                    self.assertIn(candidate.party_code, extractor.parties)
                    
                    # Test votes are non-negative
                    self.assertGreaterEqual(candidate.votes, 0)
    
    def test_json_serialization(self):
        """Test that all data can be serialized to JSON without errors"""
        extractor = PresidentialDataExtractor()
        
        for year in ["2019", "2020"]:
            sample_results = extractor.create_sample_data_for_testing(year)
            
            # Test serialization doesn't raise exceptions
            try:
                extractor.generate_json_files(sample_results, year)
                serialization_success = True
            except (TypeError, ValueError, json.JSONDecodeError) as e:
                serialization_success = False
                self.fail(f"JSON serialization failed for {year}: {e}")
            
            self.assertTrue(serialization_success)
    
    def test_missing_metadata_handling(self):
        """Test handling of missing metadata files"""
        # Remove metadata file to test error handling
        os.remove(self.metadata_dir / "candidates.json")
        
        with self.assertRaises(FileNotFoundError):
            PresidentialDataExtractor()
    
    def test_empty_results_handling(self):
        """Test handling of empty results"""
        extractor = PresidentialDataExtractor()
        
        # Test with empty results list
        extractor.generate_json_files([], "2020")
        
        # Should not create any files
        results_dir = Path("2020/results/presidential")
        if results_dir.exists():
            json_files = list(results_dir.glob("*.json"))
            self.assertEqual(len(json_files), 0)


class TestDataStructures(unittest.TestCase):
    """Test data structure classes"""
    
    def test_candidate_dataclass(self):
        """Test Candidate dataclass"""
        candidate = Candidate("LAZCHA", "Lazarus Chakwera", "MCP", 1500)
        
        self.assertEqual(candidate.code, "LAZCHA")
        self.assertEqual(candidate.name, "Lazarus Chakwera")
        self.assertEqual(candidate.party_code, "MCP")
        self.assertEqual(candidate.votes, 1500)
    
    def test_constituency_dataclass(self):
        """Test Constituency dataclass"""
        candidate = Candidate("LAZCHA", "Lazarus Chakwera", "MCP", 1500)
        constituency = Constituency("001", "Chitipa North", False, [candidate])
        
        self.assertEqual(constituency.code, "001")
        self.assertEqual(constituency.name, "Chitipa North")
        self.assertFalse(constituency.is_legacy)
        self.assertEqual(len(constituency.candidates), 1)
        self.assertEqual(constituency.candidates[0].code, "LAZCHA")
    
    def test_district_results_dataclass(self):
        """Test DistrictResults dataclass"""
        candidate = Candidate("LAZCHA", "Lazarus Chakwera", "MCP", 1500)
        constituency = Constituency("001", "Chitipa North", False, [candidate])
        district = DistrictResults("CT", "Chitipa", 25, [constituency])
        
        self.assertEqual(district.district_code, "CT")
        self.assertEqual(district.district_name, "Chitipa")
        self.assertEqual(district.null_votes, 25)
        self.assertEqual(len(district.constituencies), 1)


def run_tests():
    """Run all tests"""
    print("Running Presidential Election Data Extractor Tests")
    print("="*50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPresidentialDataExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestDataStructures))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} tests failed")
        return False


if __name__ == "__main__":
    run_tests()