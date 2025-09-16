"""
Base PDF extraction utilities for Malawi election results.
Provides common functionality for extracting data from election PDFs.
"""

import fitz  # PyMuPDF
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    """Represents a candidate with their election results."""
    name: str
    party: str
    votes: int
    percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching expected JSON structure."""
        return {
            "candidateCode": self.generate_candidate_code(),
            "partyCode": self.party,
            "votes": self.votes
        }
    
    def generate_candidate_code(self) -> str:
        """Generate 6-character candidate code from name."""
        # Extract first 3 letters of first name and first 3 of last name
        names = self.name.upper().replace("DR.", "").replace("PROF.", "").strip().split()
        if len(names) >= 2:
            first_part = re.sub(r'[^A-Z]', '', names[0])[:3]
            last_part = re.sub(r'[^A-Z]', '', names[-1])[:3]
            return (first_part + last_part).ljust(6, 'X')[:6]
        else:
            # Fallback for single names
            clean_name = re.sub(r'[^A-Z]', '', names[0] if names else 'UNKNOWN')
            return clean_name[:6].ljust(6, 'X')


@dataclass
class Constituency:
    """Represents a constituency with its election results."""
    code: str
    candidates: List[Candidate]
    is_legacy: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching expected JSON structure."""
        return {
            "code": self.code,
            "isLegacy": self.is_legacy,
            "candidates": [candidate.to_dict() for candidate in self.candidates]
        }


@dataclass
class DistrictResults:
    """Represents complete district election results."""
    district_code: str
    election_type: str
    null_votes: int
    constituencies: List[Constituency]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching expected JSON structure."""
        return {
            "districtCode": self.district_code,
            "type": self.election_type,
            "nullVotes": self.null_votes,
            "constituencies": [constituency.to_dict() for constituency in self.constituencies]
        }


class PDFExtractor:
    """Base class for extracting election results from PDF files."""
    
    def __init__(self, pdf_path: str, metadata_path: str = None):
        """
        Initialize PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
            metadata_path: Path to administration metadata JSON
        """
        self.pdf_path = Path(pdf_path)
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self.administration_data = self._load_administration_data()
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    def _load_administration_data(self) -> Optional[Dict[str, Any]]:
        """Load administration metadata for validation."""
        if not self.metadata_path or not self.metadata_path.exists():
            logger.warning("Administration metadata not found")
            return None
        
        try:
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading administration data: {e}")
            return None
    
    def get_valid_district_codes(self) -> List[str]:
        """Get list of valid district codes from metadata."""
        if not self.administration_data:
            return []
        return [district["code"] for district in self.administration_data["districts"]]
    
    def get_constituencies_for_district(self, district_code: str) -> List[str]:
        """Get list of constituency codes for a given district."""
        if not self.administration_data:
            return []
        
        for district in self.administration_data["districts"]:
            if district["code"] == district_code:
                return [const["code"] for const in district["constituencies"]]
        return []
    
    def extract_text_from_page(self, page_num: int) -> str:
        """Extract text from a specific page."""
        try:
            doc = fitz.open(str(self.pdf_path))
            page = doc.load_page(page_num)
            text = page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num}: {e}")
            return ""
    
    def extract_tables_from_page(self, page_num: int) -> List[List[List[str]]]:
        """Extract tables from a specific page."""
        try:
            doc = fitz.open(str(self.pdf_path))
            page = doc.load_page(page_num)
            tables = page.find_tables()
            
            extracted_tables = []
            for table in tables:
                table_data = table.extract()
                if table_data:
                    extracted_tables.append(table_data)
            
            doc.close()
            return extracted_tables
        except Exception as e:
            logger.error(f"Error extracting tables from page {page_num}: {e}")
            return []
    
    def get_page_count(self) -> int:
        """Get total number of pages in PDF."""
        try:
            doc = fitz.open(str(self.pdf_path))
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0
    
    def parse_candidate_row(self, row: List[str]) -> Optional[Candidate]:
        """Parse a table row to extract candidate information."""
        if len(row) < 4:
            return None
        
        try:
            # Expected format: [District/Empty, Candidate Name, Party, Votes, Percentage]
            candidate_name = row[1].strip() if len(row) > 1 else ""
            party = row[2].strip() if len(row) > 2 else ""
            votes_str = row[3].strip() if len(row) > 3 else "0"
            
            # Clean and parse votes
            votes_str = re.sub(r'[^\d]', '', votes_str)
            votes = int(votes_str) if votes_str.isdigit() else 0
            
            # Parse percentage if available
            percentage = 0.0
            if len(row) > 4:
                percentage_str = row[4].strip().replace('%', '')
                try:
                    percentage = float(percentage_str)
                except ValueError:
                    percentage = 0.0
            
            if candidate_name and party and votes >= 0:
                return Candidate(
                    name=candidate_name,
                    party=party,
                    votes=votes,
                    percentage=percentage
                )
        except Exception as e:
            logger.error(f"Error parsing candidate row {row}: {e}")
        
        return None
    
    def extract_district_from_text(self, text: str) -> Optional[str]:
        """Extract district name from text and map to district code."""
        if not self.administration_data:
            return None
        
        # Create mapping from district names to codes
        name_to_code = {}
        for district in self.administration_data["districts"]:
            name_to_code[district["name"].upper()] = district["code"]
        
        # Look for district names in text
        text_upper = text.upper()
        for district_name, district_code in name_to_code.items():
            if district_name in text_upper:
                return district_code
        
        return None
    
    def extract_null_votes(self, text: str) -> int:
        """Extract null/void votes from text."""
        # Look for patterns like "NULL & VOID 402" or "402 0.50"
        patterns = [
            r'NULL\s*&\s*VOID\s*(\d+)',
            r'(\d+)\s*0\.\d+\s*%',  # votes followed by small percentage
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return 0
    
    def validate_district_code(self, district_code: str) -> bool:
        """Validate that district code exists in metadata."""
        valid_codes = self.get_valid_district_codes()
        return district_code in valid_codes
    
    def save_results(self, results: DistrictResults, output_dir: str) -> str:
        """Save district results to JSON file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{results.district_code}_RESULTS.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        
        logger.info(f"Saved results to {filepath}")
        return str(filepath)


class ElectionPDFExtractor(PDFExtractor):
    """Specialized extractor for election results PDFs."""
    
    def __init__(self, pdf_path: str, election_year: int, metadata_path: str = None):
        """
        Initialize election PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
            election_year: Year of the election (2014, 2019, 2020)
            metadata_path: Path to administration metadata JSON
        """
        super().__init__(pdf_path, metadata_path)
        self.election_year = election_year
        self.election_type = "presidential"
    
    def extract_all_districts(self) -> List[DistrictResults]:
        """Extract results for all districts from the PDF."""
        all_results = []
        page_count = self.get_page_count()
        
        logger.info(f"Processing {page_count} pages for {self.election_year} election")
        
        for page_num in range(page_count):
            try:
                district_result = self.extract_district_from_page(page_num)
                if district_result:
                    all_results.append(district_result)
                    logger.info(f"Extracted data for district {district_result.district_code}")
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
        
        return all_results
    
    def extract_district_from_page(self, page_num: int) -> Optional[DistrictResults]:
        """Extract district results from a single page."""
        # This method will be implemented in specific year extractors
        raise NotImplementedError("Subclasses must implement extract_district_from_page")


if __name__ == "__main__":
    # Basic test
    pdf_path = "src/04 PRESIDENTIAL SUMMARY RESULTS FOR 2014 ELECTIONS.pdf"
    metadata_path = "metadata/administration.json"
    
    try:
        extractor = ElectionPDFExtractor(pdf_path, 2014, metadata_path)
        print(f"PDF has {extractor.get_page_count()} pages")
        print(f"Valid district codes: {extractor.get_valid_district_codes()[:5]}...")
    except Exception as e:
        print(f"Error: {e}")
