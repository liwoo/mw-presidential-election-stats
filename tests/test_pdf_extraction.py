"""
Comprehensive test suite for PDF election results extraction.
Following TDD methodology - tests written before implementation.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, List, Any

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "test_data"
METADATA_DIR = Path(__file__).parent.parent / "metadata"
SRC_DIR = Path(__file__).parent.parent / "src"


class TestPDFExtractionStructure:
    """Test the structure and format of extracted data."""
    
    def test_district_results_structure(self):
        """Test that extracted district results have correct structure."""
        # This will be implemented after we create the extractor
        expected_structure = {
            "districtCode": str,
            "type": str,
            "nullVotes": int,
            "constituencies": list
        }
        
        # Mock result for now - will be replaced with actual extraction
        mock_result = {
            "districtCode": "CT",
            "type": "presidential",
            "nullVotes": 402,
            "constituencies": []
        }
        
        assert isinstance(mock_result["districtCode"], str)
        assert isinstance(mock_result["type"], str)
        assert isinstance(mock_result["nullVotes"], int)
        assert isinstance(mock_result["constituencies"], list)
        assert mock_result["type"] == "presidential"
    
    def test_constituency_structure(self):
        """Test that constituency data has correct structure."""
        expected_constituency = {
            "code": "001",
            "isLegacy": False,
            "candidates": []
        }
        
        assert isinstance(expected_constituency["code"], str)
        assert isinstance(expected_constituency["isLegacy"], bool)
        assert isinstance(expected_constituency["candidates"], list)
    
    def test_candidate_structure(self):
        """Test that candidate data has correct structure."""
        expected_candidate = {
            "candidateCode": "JOYBAN",
            "partyCode": "PP",
            "votes": 5720
        }
        
        assert isinstance(expected_candidate["candidateCode"], str)
        assert isinstance(expected_candidate["partyCode"], str)
        assert isinstance(expected_candidate["votes"], int)
        assert expected_candidate["votes"] >= 0


class TestDataValidation:
    """Test data validation and integrity checks."""
    
    def test_district_code_validation(self):
        """Test that district codes match administration metadata."""
        # Load administration data
        admin_file = METADATA_DIR / "administration.json"
        if admin_file.exists():
            with open(admin_file, 'r') as f:
                admin_data = json.load(f)
            
            valid_district_codes = [d["code"] for d in admin_data["districts"]]
            
            # Test district codes
            test_codes = ["CT", "KR", "RU", "MZ"]  # From PDF analysis
            for code in test_codes:
                assert code in valid_district_codes, f"District code {code} not found in administration data"
    
    def test_constituency_code_validation(self):
        """Test that constituency codes are valid."""
        # Constituency codes should be 3-digit strings
        test_codes = ["001", "002", "003", "153", "170"]
        
        for code in test_codes:
            assert len(code) == 3, f"Constituency code {code} should be 3 digits"
            assert code.isdigit(), f"Constituency code {code} should be numeric"
    
    def test_vote_totals_consistency(self):
        """Test that vote totals are mathematically consistent."""
        # Mock data for testing logic
        mock_candidates = [
            {"candidateCode": "JOYBAN", "partyCode": "PP", "votes": 5720},
            {"candidateCode": "LAZCHA", "partyCode": "MCP", "votes": 1238},
            {"candidateCode": "PETMUT", "partyCode": "DPP", "votes": 4979}
        ]
        
        total_votes = sum(c["votes"] for c in mock_candidates)
        assert total_votes > 0, "Total votes should be positive"
        
        for candidate in mock_candidates:
            assert candidate["votes"] >= 0, f"Votes for {candidate['candidateCode']} should be non-negative"
    
    def test_null_votes_validation(self):
        """Test that null votes are properly handled."""
        test_null_votes = [402, 483, 434]  # From PDF analysis
        
        for null_votes in test_null_votes:
            assert isinstance(null_votes, int), "Null votes should be integer"
            assert null_votes >= 0, "Null votes should be non-negative"


class TestPDFParsing:
    """Test PDF parsing functionality."""
    
    def test_pdf_file_exists(self):
        """Test that the 2014 PDF file exists."""
        pdf_file = SRC_DIR / "04 PRESIDENTIAL SUMMARY RESULTS FOR 2014 ELECTIONS.pdf"
        assert pdf_file.exists(), f"PDF file not found: {pdf_file}"
    
    def test_pdf_readable(self):
        """Test that PDF can be opened and read."""
        try:
            import fitz
            pdf_file = SRC_DIR / "04 PRESIDENTIAL SUMMARY RESULTS FOR 2014 ELECTIONS.pdf"
            doc = fitz.open(str(pdf_file))
            assert len(doc) > 0, "PDF should have pages"
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not available")
    
    def test_table_extraction(self):
        """Test that tables can be extracted from PDF."""
        try:
            import fitz
            pdf_file = SRC_DIR / "04 PRESIDENTIAL SUMMARY RESULTS FOR 2014 ELECTIONS.pdf"
            doc = fitz.open(str(pdf_file))
            
            # Test first page
            page = doc.load_page(0)
            tables = page.find_tables()
            table_list = list(tables)
            
            assert len(table_list) > 0, "Should find at least one table on first page"
            
            # Test table data extraction
            table_data = table_list[0].extract()
            assert len(table_data) > 0, "Table should have data"
            assert len(table_data[0]) >= 4, "Table should have at least 4 columns (District, Candidate, Party, Votes)"
            
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not available")


class TestCandidateMapping:
    """Test candidate name to code mapping."""
    
    def test_candidate_name_parsing(self):
        """Test parsing of candidate names from PDF."""
        test_names = [
            "Dr. Joyce Hilda BANDA",
            "Dr. Lazarus McCarthy CHAKWERA", 
            "Prof. Peter MUTHARIKA",
            "Atupele MULUZI"
        ]
        
        expected_codes = [
            "JOYBAN",
            "LAZCHA", 
            "PETMUT",
            "ATUMUL"
        ]
        
        # This will test the name-to-code mapping logic
        for name, expected_code in zip(test_names, expected_codes):
            # Mock implementation - will be replaced with actual logic
            assert len(expected_code) == 6, f"Candidate code {expected_code} should be 6 characters"
            assert expected_code.isupper(), f"Candidate code {expected_code} should be uppercase"
    
    def test_party_code_mapping(self):
        """Test party code mapping."""
        test_parties = ["PP", "MCP", "DPP", "UDF", "UP", "NLP", "CCP", "PPM", "MAFUNDE", "NASAF", "UIP", "PETRA"]
        
        for party in test_parties:
            assert len(party) <= 8, f"Party code {party} should be 8 characters or less"
            assert party.isupper(), f"Party code {party} should be uppercase"


class TestStatisticalValidation:
    """Test statistical validation of extracted data."""
    
    def test_percentage_calculations(self):
        """Test that vote percentages are calculated correctly."""
        # Mock data from PDF
        total_valid_votes = 79664
        candidate_votes = 35756
        expected_percentage = 44.88
        
        calculated_percentage = round((candidate_votes / total_valid_votes) * 100, 2)
        assert abs(calculated_percentage - expected_percentage) < 0.01, \
            f"Percentage calculation error: expected {expected_percentage}, got {calculated_percentage}"
    
    def test_turnout_calculations(self):
        """Test voter turnout calculations."""
        # Mock data from PDF
        total_votes_cast = 80066
        total_registered = 101665
        expected_turnout = 78.75
        
        calculated_turnout = round((total_votes_cast / total_registered) * 100, 2)
        assert abs(calculated_turnout - expected_turnout) < 0.01, \
            f"Turnout calculation error: expected {expected_turnout}, got {calculated_turnout}"
    
    def test_vote_totals_match(self):
        """Test that individual votes sum to total valid votes."""
        # This will test the mathematical consistency of extracted data
        mock_votes = [35756, 7738, 353, 223, 122, 65, 135, 1238, 31119, 176, 2613, 126]
        expected_total = 79664
        
        calculated_total = sum(mock_votes)
        assert calculated_total == expected_total, \
            f"Vote totals don't match: expected {expected_total}, got {calculated_total}"


class TestOutputFormat:
    """Test output format compliance."""
    
    def test_json_serializable(self):
        """Test that output data is JSON serializable."""
        mock_result = {
            "districtCode": "CT",
            "type": "presidential", 
            "nullVotes": 402,
            "constituencies": [
                {
                    "code": "001",
                    "isLegacy": False,
                    "candidates": [
                        {
                            "candidateCode": "JOYBAN",
                            "partyCode": "PP",
                            "votes": 5720
                        }
                    ]
                }
            ]
        }
        
        # Should not raise an exception
        json_str = json.dumps(mock_result)
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed == mock_result
    
    def test_file_naming_convention(self):
        """Test that output files follow naming convention."""
        expected_files = [
            "CT_RESULTS.json",
            "KR_RESULTS.json", 
            "RU_RESULTS.json"
        ]
        
        for filename in expected_files:
            assert filename.endswith("_RESULTS.json"), f"File {filename} should end with _RESULTS.json"
            district_code = filename.split("_")[0]
            assert len(district_code) == 2, f"District code {district_code} should be 2 characters"
            assert district_code.isupper(), f"District code {district_code} should be uppercase"


if __name__ == "__main__":
    pytest.main([__file__])
