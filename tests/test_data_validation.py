#!/usr/bin/env python3
"""
Test Data Validation for 2019 Parliamentary Election Results

This module contains test cases to validate that the 2019 parliamentary election data
matches the metadata standards for candidates, constituencies, and parties.

Following TDD approach - tests are written first to define expected behavior.
"""

import json
import os
import unittest
from pathlib import Path


class TestParliamentaryDataValidation(unittest.TestCase):
    """Test cases for validating parliamentary data against metadata standards."""
    
    @classmethod
    def setUpClass(cls):
        """Load metadata and result files for testing."""
        cls.base_path = Path(__file__).parent.parent
        
        # Load metadata
        with open(cls.base_path / "metadata" / "administration.json", 'r') as f:
            cls.admin_metadata = json.load(f)
        
        with open(cls.base_path / "metadata" / "candidates.json", 'r') as f:
            cls.candidates_metadata = json.load(f)
        
        with open(cls.base_path / "metadata" / "parties.json", 'r') as f:
            cls.parties_metadata = json.load(f)
        
        # Create lookup dictionaries for efficient validation
        cls.valid_district_codes = {d["code"] for d in cls.admin_metadata["districts"]}
        cls.valid_constituency_codes = set()
        cls.district_constituencies = {}
        
        for district in cls.admin_metadata["districts"]:
            district_code = district["code"]
            cls.district_constituencies[district_code] = {
                c["code"] for c in district["constituencies"]
            }
            cls.valid_constituency_codes.update(cls.district_constituencies[district_code])
        
        cls.valid_candidate_codes = {c["code"] for c in cls.candidates_metadata}
        cls.valid_party_codes = {p["code"] for p in cls.parties_metadata}
        
        # Load result files
        cls.result_files = []
        results_dir = cls.base_path / "2019" / "results" / "parliamentary"
        for file_path in results_dir.glob("*_RESULTS.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                cls.result_files.append((file_path.name, data))

    def test_district_codes_are_valid(self):
        """Test that all district codes in result files match metadata."""
        for filename, data in self.result_files:
            with self.subTest(file=filename):
                district_code = data.get("districtCode")
                self.assertIn(
                    district_code, 
                    self.valid_district_codes,
                    f"Invalid district code '{district_code}' in {filename}"
                )

    def test_constituency_codes_are_valid(self):
        """Test that all constituency codes match the administration metadata."""
        for filename, data in self.result_files:
            district_code = data.get("districtCode")
            for constituency in data.get("constituencies", []):
                constituency_code = constituency.get("code")
                with self.subTest(file=filename, constituency=constituency_code):
                    # Check constituency code exists globally
                    self.assertIn(
                        constituency_code,
                        self.valid_constituency_codes,
                        f"Invalid constituency code '{constituency_code}' in {filename}"
                    )
                    
                    # Check constituency belongs to correct district
                    if district_code in self.district_constituencies:
                        self.assertIn(
                            constituency_code,
                            self.district_constituencies[district_code],
                            f"Constituency '{constituency_code}' does not belong to district '{district_code}' in {filename}"
                        )

    def test_candidate_codes_are_valid(self):
        """Test that all candidate codes match the candidates metadata."""
        for filename, data in self.result_files:
            for constituency in data.get("constituencies", []):
                for candidate in constituency.get("candidates", []):
                    candidate_code = candidate.get("candidateCode")
                    with self.subTest(file=filename, candidate=candidate_code):
                        self.assertIn(
                            candidate_code,
                            self.valid_candidate_codes,
                            f"Invalid candidate code '{candidate_code}' in {filename}"
                        )

    def test_party_codes_are_valid(self):
        """Test that all party codes match the parties metadata."""
        for filename, data in self.result_files:
            for constituency in data.get("constituencies", []):
                for candidate in constituency.get("candidates", []):
                    party_code = candidate.get("partyCode")
                    with self.subTest(file=filename, party=party_code):
                        self.assertIn(
                            party_code,
                            self.valid_party_codes,
                            f"Invalid party code '{party_code}' in {filename}"
                        )

    def test_vote_counts_are_reasonable(self):
        """Test that vote counts are within reasonable ranges."""
        for filename, data in self.result_files:
            for constituency in data.get("constituencies", []):
                for candidate in constituency.get("candidates", []):
                    votes = candidate.get("votes", 0)
                    with self.subTest(file=filename, candidate=candidate.get("candidateCode")):
                        # Votes should be non-negative
                        self.assertGreaterEqual(
                            votes, 0,
                            f"Negative vote count {votes} for candidate {candidate.get('candidateCode')} in {filename}"
                        )
                        
                        # Votes should be reasonable (less than 100,000 for parliamentary constituency)
                        self.assertLessEqual(
                            votes, 100000,
                            f"Unreasonably high vote count {votes} for candidate {candidate.get('candidateCode')} in {filename}"
                        )

    def test_required_fields_present(self):
        """Test that all required fields are present in the data structure."""
        for filename, data in self.result_files:
            with self.subTest(file=filename):
                # Test root level fields
                self.assertIn("districtCode", data, f"Missing districtCode in {filename}")
                self.assertIn("type", data, f"Missing type in {filename}")
                self.assertEqual(data.get("type"), "parliamentary", f"Wrong type in {filename}")
                self.assertIn("constituencies", data, f"Missing constituencies in {filename}")
                
                # Test constituency level fields
                for constituency in data.get("constituencies", []):
                    self.assertIn("code", constituency, f"Missing constituency code in {filename}")
                    self.assertIn("candidates", constituency, f"Missing candidates in {filename}")
                    
                    # Test candidate level fields
                    for candidate in constituency.get("candidates", []):
                        self.assertIn("candidateCode", candidate, f"Missing candidateCode in {filename}")
                        self.assertIn("partyCode", candidate, f"Missing partyCode in {filename}")
                        self.assertIn("votes", candidate, f"Missing votes in {filename}")

    def test_no_duplicate_candidates_per_constituency(self):
        """Test that there are no duplicate candidate-party combinations per constituency."""
        for filename, data in self.result_files:
            for constituency in data.get("constituencies", []):
                constituency_code = constituency.get("code")
                candidate_party_pairs = []
                
                for candidate in constituency.get("candidates", []):
                    candidate_code = candidate.get("candidateCode")
                    party_code = candidate.get("partyCode")
                    pair = (candidate_code, party_code)
                    
                    with self.subTest(file=filename, constituency=constituency_code, pair=pair):
                        self.assertNotIn(
                            pair, candidate_party_pairs,
                            f"Duplicate candidate-party pair {pair} in constituency {constituency_code} in {filename}"
                        )
                    candidate_party_pairs.append(pair)

    def test_constituency_completeness(self):
        """Test that each district has all its constituencies represented."""
        for filename, data in self.result_files:
            district_code = data.get("districtCode")
            if district_code in self.district_constituencies:
                expected_constituencies = self.district_constituencies[district_code]
                actual_constituencies = {
                    c.get("code") for c in data.get("constituencies", [])
                    if c.get("code") is not None
                }
                
                with self.subTest(file=filename, district=district_code):
                    # Check for missing constituencies
                    missing_constituencies = expected_constituencies - actual_constituencies
                    if missing_constituencies:
                        self.fail(
                            f"Missing constituencies {missing_constituencies} in district {district_code} in {filename}"
                        )


def run_validation_tests():
    """Run all validation tests and return results."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_validation_tests()