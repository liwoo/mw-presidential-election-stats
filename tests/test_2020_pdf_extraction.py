"""
Test suite for 2020 Presidential Election PDF extraction.
Following TDD principles - tests written before implementation.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Test data and expected structures
EXPECTED_CANDIDATES = [
    {"candidateCode": "LAZCHA", "partyCode": "MCP"},
    {"candidateCode": "PETKUW", "partyCode": "MMD"}, 
    {"candidateCode": "ARTMUT", "partyCode": "DPP"}
]

EXPECTED_JSON_STRUCTURE = {
    "districtCode": str,
    "type": str,
    "nullVotes": int,
    "constituencies": list
}

EXPECTED_CONSTITUENCY_STRUCTURE = {
    "code": str,
    "isLegacy": bool,
    "candidates": list
}

EXPECTED_CANDIDATE_STRUCTURE = {
    "candidateCode": str,
    "partyCode": str,
    "votes": int
}


class TestCandidateCodeGeneration:
    """Test candidate code generation from names."""
    
    def test_lazarus_chakwera_code_generation(self):
        """Test that LAZARUS CHAKWERA generates LAZCHA."""
        from src.pdf_2020_extractor import generate_candidate_code
        
        result = generate_candidate_code("LAZARUS CHAKWERA (MCP)")
        assert result == "LAZCHA"
    
    def test_peter_kuwani_code_generation(self):
        """Test that PETER KUWANI generates PETKUW."""
        from src.pdf_2020_extractor import generate_candidate_code
        
        result = generate_candidate_code("PETER DOMINICO SINOSI DRIVER KUWANI (MMD)")
        assert result == "PETKUW"
    
    def test_arthur_mutharika_code_generation(self):
        """Test that ARTHUR MUTHARIKA generates ARTMUT."""
        from src.pdf_2020_extractor import generate_candidate_code
        
        result = generate_candidate_code("ARTHUR PETER MUTHARIKA (DPP)")
        assert result == "ARTMUT"
    
    def test_candidate_code_length(self):
        """Test that all candidate codes are exactly 6 characters."""
        from src.pdf_2020_extractor import generate_candidate_code
        
        candidates = [
            "LAZARUS CHAKWERA (MCP)",
            "PETER DOMINICO SINOSI DRIVER KUWANI (MMD)",
            "ARTHUR PETER MUTHARIKA (DPP)"
        ]
        
        for candidate in candidates:
            code = generate_candidate_code(candidate)
            assert len(code) == 6
            assert code.isupper()


class TestPDFDataExtraction:
    """Test PDF data extraction functionality."""
    
    def test_pdf_file_exists(self):
        """Test that the 2020 PDF file exists."""
        pdf_path = Path("src/2020-Fresh-Presidential-Election-Results-Per-station.pdf")
        assert pdf_path.exists(), f"PDF file not found: {pdf_path}"
    
    def test_pdf_page_count(self):
        """Test that PDF has expected number of pages."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        page_count = extractor.get_page_count()
        assert page_count == 233
    
    def test_candidate_extraction_from_pdf(self):
        """Test that all three candidates are extracted from PDF."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        candidates = extractor.extract_candidates()
        assert len(candidates) == 3
        
        candidate_codes = [c["candidateCode"] for c in candidates]
        assert "LAZCHA" in candidate_codes
        assert "PETKUW" in candidate_codes
        assert "ARTMUT" in candidate_codes
    
    def test_centre_code_parsing(self):
        """Test parsing of centre codes to constituency codes."""
        from src.pdf_2020_extractor import PDF2020Extractor

        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )

        # Test centre code 01001 should map to constituency 001 (Chitipa North)
        constituency_code = extractor.parse_constituency_from_centre("01001")
        assert constituency_code == "001"

        # Test centre code 01045 should map to constituency 005 (Chitipa South)
        constituency_code = extractor.parse_constituency_from_centre("01045")
        assert constituency_code == "005"

        # Test centre code 01102 should map to constituency 001 (Chitipa North)
        constituency_code = extractor.parse_constituency_from_centre("01102")
        assert constituency_code == "001"
    
    def test_district_mapping_from_constituency(self):
        """Test mapping constituency codes to district codes."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        # Constituency 001 should map to district CT (Chitipa)
        district_code = extractor.get_district_from_constituency("001")
        assert district_code == "CT"


class TestDataValidation:
    """Test data validation against metadata."""
    
    def test_constituency_code_validation(self):
        """Test that constituency codes exist in metadata."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        # Valid constituency codes
        assert extractor.validate_constituency_code("001") == True
        assert extractor.validate_constituency_code("002") == True
        
        # Invalid constituency code
        assert extractor.validate_constituency_code("999") == False
    
    def test_district_code_validation(self):
        """Test that district codes exist in metadata."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        # Valid district codes
        assert extractor.validate_district_code("CT") == True
        assert extractor.validate_district_code("KR") == True
        
        # Invalid district code
        assert extractor.validate_district_code("XX") == False


class TestJSONStructureCompliance:
    """Test that generated JSON matches expected structure."""
    
    def test_district_json_structure(self):
        """Test that district JSON has correct structure."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        # Extract data for Chitipa district (should have constituencies 001-005)
        district_data = extractor.extract_district_data("CT")
        
        # Validate top-level structure
        assert isinstance(district_data["districtCode"], str)
        assert district_data["districtCode"] == "CT"
        assert district_data["type"] == "presidential"
        assert isinstance(district_data["nullVotes"], int)
        assert isinstance(district_data["constituencies"], list)
        assert len(district_data["constituencies"]) == 5  # CT has 5 constituencies
    
    def test_constituency_structure(self):
        """Test that constituency data has correct structure."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        district_data = extractor.extract_district_data("CT")
        constituency = district_data["constituencies"][0]
        
        assert isinstance(constituency["code"], str)
        assert len(constituency["code"]) == 3
        assert constituency["isLegacy"] == False
        assert isinstance(constituency["candidates"], list)
        assert len(constituency["candidates"]) == 3  # Three candidates
    
    def test_candidate_structure(self):
        """Test that candidate data has correct structure."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        district_data = extractor.extract_district_data("CT")
        candidate = district_data["constituencies"][0]["candidates"][0]
        
        assert isinstance(candidate["candidateCode"], str)
        assert len(candidate["candidateCode"]) == 6
        assert isinstance(candidate["partyCode"], str)
        assert isinstance(candidate["votes"], int)
        assert candidate["votes"] >= 0


class TestVoteAggregation:
    """Test vote counting and aggregation."""
    
    def test_null_votes_aggregation(self):
        """Test that null votes are correctly aggregated."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        district_data = extractor.extract_district_data("CT")
        
        # Null votes should be positive integer
        assert isinstance(district_data["nullVotes"], int)
        assert district_data["nullVotes"] >= 0
    
    def test_vote_totals_consistency(self):
        """Test that vote totals are mathematically consistent."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        district_data = extractor.extract_district_data("CT")
        
        # For each constituency, sum of candidate votes should be reasonable
        for constituency in district_data["constituencies"]:
            total_candidate_votes = sum(c["votes"] for c in constituency["candidates"])
            assert total_candidate_votes > 0, f"No votes found for constituency {constituency['code']}"


class TestFileOutput:
    """Test file generation and output."""
    
    def test_json_serialization(self):
        """Test that extracted data can be serialized to JSON."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        district_data = extractor.extract_district_data("CT")
        
        # Should not raise an exception
        json_str = json.dumps(district_data, indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed_data = json.loads(json_str)
        assert parsed_data == district_data
    
    def test_output_filename_format(self):
        """Test that output filenames follow the correct format."""
        from src.pdf_2020_extractor import PDF2020Extractor
        
        extractor = PDF2020Extractor(
            "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf",
            "metadata/administration.json"
        )
        
        filename = extractor.get_output_filename("CT")
        assert filename == "CT_RESULTS.json"
        
        filename = extractor.get_output_filename("KR")
        assert filename == "KR_RESULTS.json"


if __name__ == "__main__":
    pytest.main([__file__])
