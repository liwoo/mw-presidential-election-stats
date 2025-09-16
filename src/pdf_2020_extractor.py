"""
Specialized PDF extractor for 2020 Fresh Presidential Election Results.
Extends the base PDFExtractor to handle the specific format of the 2020 PDF.
"""

import fitz  # PyMuPDF
import json
import re
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFExtractor, DistrictResults

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_candidate_code(full_name: str) -> str:
    """
    Generate 6-character candidate code from full name.
    Takes first 3 letters of first name + first 3 letters of last name.
    
    Args:
        full_name: Full candidate name with party (e.g., "LAZARUS CHAKWERA (MCP)")
    
    Returns:
        6-character uppercase candidate code (e.g., "LAZCHA")
    """
    # Remove party info in parentheses
    name_part = full_name.split('(')[0].strip()
    words = name_part.split()
    
    if len(words) >= 2:
        first_name = words[0]
        last_name = words[-1]  # Take the last word as surname
        code = (first_name[:3] + last_name[:3]).upper()
        return code
    
    # Fallback for single name
    return name_part[:6].upper()


@dataclass
class CandidateInfo:
    """Information about a candidate."""
    name: str
    party: str
    code: str


@dataclass
class PollingStationResult:
    """Results from a single polling station."""
    centre_code: str
    polling_station: str
    registered_voters: int
    null_votes: int
    total_voted: int
    candidate_votes: Dict[str, int]  # candidate_code -> votes


class PDF2020Extractor(PDFExtractor):
    """Specialized extractor for 2020 Presidential Election Results PDF."""

    def __init__(self, pdf_path: str, metadata_path: str):
        """
        Initialize the 2020 PDF extractor.

        Args:
            pdf_path: Path to the 2020 PDF file
            metadata_path: Path to administration metadata JSON
        """
        super().__init__(pdf_path, metadata_path)
        self.candidates = self._extract_candidates_from_header()
        self.candidate_map = {c.code: c for c in self.candidates}
        self.centre_to_constituency_map = self._build_centre_to_constituency_map()
    
    def _extract_candidates_from_header(self) -> List[CandidateInfo]:
        """Extract candidate information from PDF header."""
        candidates = []

        # Candidates from the Fresh Presidential Election 2020 PDF
        candidate_data = [
            ("LAZARUS CHAKWERA (MCP)", "MCP"),
            ("PETER DOMINICO SINOSI DRIVER KUWANI (MMD)", "MMD"),
            ("ARTHUR PETER MUTHARIKA (DPP)", "DPP")
        ]

        for name, party in candidate_data:
            code = generate_candidate_code(name)
            candidates.append(CandidateInfo(name=name, party=party, code=code))

        return candidates

    def _build_centre_to_constituency_map(self) -> Dict[str, str]:
        """
        Build mapping from centre codes to constituency codes.

        Approach: Centre Code → Constituency → District → District Code
        1. Extract centre code (e.g., "01001")
        2. Use last 3 digits as constituency code (e.g., "001")
        3. Find which district contains this constituency using administration metadata
        4. Map centre to constituency if valid

        Returns:
            Dictionary mapping centre codes to constituency codes
        """
        if not self.administration_data:
            return {}

        logger.info("Building centre code to constituency mapping using administration metadata...")

        # Build constituency to district mapping from metadata
        constituency_to_district = {}
        for district in self.administration_data["districts"]:
            for constituency in district["constituencies"]:
                constituency_to_district[constituency["code"]] = district["code"]

        centre_to_constituency = {}

        # Extract all centre codes from the PDF
        all_centres = self._extract_all_centre_codes()

        # Map each centre code to constituency
        for centre_code in all_centres:
            constituency_code = self._map_centre_to_constituency_simple(centre_code, constituency_to_district)
            if constituency_code:
                centre_to_constituency[centre_code] = constituency_code
                logger.debug(f"Mapped centre {centre_code} -> constituency {constituency_code}")

        logger.info(f"Built mapping for {len(centre_to_constituency)} centre codes")
        return centre_to_constituency

    def _extract_all_centre_codes(self) -> List[str]:
        """Extract all 5-digit centre codes from the PDF."""
        centre_codes = []
        page_count = self.get_page_count()

        for page_num in range(page_count):
            text = self.extract_text_from_page(page_num)
            lines = text.split('\n')

            for line in lines:
                line_clean = line.strip()
                if re.match(r'^\d{5}$', line_clean):
                    centre_codes.append(line_clean)

        return centre_codes

    def _map_centre_to_constituency_simple(self, centre_code: str, constituency_to_district: Dict[str, str]) -> Optional[str]:
        """
        Map centre code to constituency using simple logic:
        Centre Code → Constituency (last 3 digits) → validate against metadata

        Args:
            centre_code: 5-digit centre code (e.g., "01001")
            constituency_to_district: Mapping of constituency codes to district codes

        Returns:
            Constituency code if valid, None otherwise
        """
        if len(centre_code) != 5:
            return None

        # Use last 3 digits as constituency code
        constituency_code = centre_code[-3:]

        # Check if this constituency exists in our metadata
        if constituency_code in constituency_to_district:
            return constituency_code
        else:
            logger.warning(f"Centre {centre_code} maps to constituency {constituency_code} which doesn't exist in metadata")
            return None


    def extract_candidates(self) -> List[Dict[str, str]]:
        """
        Extract candidate information.
        
        Returns:
            List of candidate dictionaries with candidateCode and partyCode
        """
        return [
            {"candidateCode": c.code, "partyCode": c.party}
            for c in self.candidates
        ]
    
    def parse_constituency_from_centre(self, centre_code: str) -> str:
        """
        Parse constituency code from centre code using the built mapping.

        Args:
            centre_code: 5-digit centre code (e.g., "01001")

        Returns:
            3-digit constituency code (e.g., "001")
        """
        if centre_code in self.centre_to_constituency_map:
            return self.centre_to_constituency_map[centre_code]

        # Fallback: try to parse from the code structure
        logger.warning(f"Centre code {centre_code} not found in mapping, using fallback")
        if len(centre_code) >= 5:
            return centre_code[-3:]  # Last 3 digits
        return centre_code
    
    def get_district_from_constituency(self, constituency_code: str) -> Optional[str]:
        """
        Get district code from constituency code using metadata.
        
        Args:
            constituency_code: 3-digit constituency code
        
        Returns:
            2-character district code or None if not found
        """
        if not self.administration_data:
            return None
        
        for district in self.administration_data["districts"]:
            for constituency in district["constituencies"]:
                if constituency["code"] == constituency_code:
                    return district["code"]
        
        return None
    
    def validate_constituency_code(self, constituency_code: str) -> bool:
        """Validate that constituency code exists in metadata."""
        if not self.administration_data:
            return False
        
        for district in self.administration_data["districts"]:
            for constituency in district["constituencies"]:
                if constituency["code"] == constituency_code:
                    return True
        
        return False
    
    def validate_district_code(self, district_code: str) -> bool:
        """Validate that district code exists in metadata."""
        valid_codes = self.get_valid_district_codes()
        return district_code in valid_codes
    
    def _parse_page_data(self, page_num: int) -> List[PollingStationResult]:
        """
        Parse polling station data from a single page.

        Args:
            page_num: Page number to parse

        Returns:
            List of polling station results
        """
        text = self.extract_text_from_page(page_num)
        lines = text.split('\n')

        results = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and headers
            if not line or 'MALAWI ELECTORAL COMMISSION' in line or 'FRESH PRESIDENTIAL' in line or 'Page' in line or 'Generated on' in line:
                i += 1
                continue

            # Check if this is a centre code (5 digits)
            if re.match(r'^\d{5}$', line):
                centre_code = line

                # Look for PS marker in the next few lines
                j = i + 1
                ps_found = False
                while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
                    next_line = lines[j].strip()
                    if re.match(r'^PS\d*$', next_line):  # More precise PS pattern
                        ps_found = True
                        ps_line = next_line

                        # Collect the next 6 numeric values (handle commas)
                        data_values = []
                        k = j + 1
                        while k < len(lines) and len(data_values) < 6:
                            potential_value = lines[k].strip()
                            # Handle numbers with commas (e.g., "1,095")
                            if re.match(r'^\d{1,3}(,\d{3})*$', potential_value) or re.match(r'^\d+$', potential_value):
                                data_values.append(int(potential_value.replace(',', '')))
                            elif potential_value and not re.match(r'^\d{5}$', potential_value):
                                # If we hit non-numeric, non-centre-code data, stop looking
                                break
                            k += 1

                        # Process if we have exactly 6 values
                        if len(data_values) == 6:
                            registered_voters, null_votes, total_voted_pdf, \
                            chakwera_votes, kuwani_votes, mutharika_votes = data_values

                            # *** CRITICAL VALIDATION STEP ***
                            # Ensure the sum of individual votes matches the 'Total Voted' column.
                            calculated_total = chakwera_votes + kuwani_votes + mutharika_votes + null_votes
                            if calculated_total == total_voted_pdf:
                                candidate_votes = {
                                    self.candidates[0].code: chakwera_votes,   # LAZCHA
                                    self.candidates[1].code: kuwani_votes,     # PETKUW
                                    self.candidates[2].code: mutharika_votes,  # ARTMUT
                                }

                                result = PollingStationResult(
                                    centre_code=centre_code,
                                    polling_station=ps_line,
                                    registered_voters=registered_voters,
                                    null_votes=null_votes,
                                    total_voted=total_voted_pdf,
                                    candidate_votes=candidate_votes
                                )
                                results.append(result)

                                # Move past the processed data
                                i = k
                                break
                            else:
                                logger.debug(f"Validation failed on page {page_num+1} for centre {centre_code} {ps_line}. "
                                           f"Sum ({calculated_total}) != Total ({total_voted_pdf})")

                        # Continue looking for additional PS lines for the same centre
                        j = k
                        continue  # Continue the PS search loop
                    else:
                        j += 1

                if not ps_found:
                    logger.debug(f"No PS marker found for centre {centre_code} on page {page_num+1}")
                    i += 1
            else:
                i += 1

        return results
    
    def extract_district_data(self, district_code: str) -> Dict[str, Any]:
        """
        Extract all data for a specific district with enhanced structure.

        Structure: Centre Code → Constituency Name (with code) → Vote totals

        Args:
            district_code: 2-character district code (e.g., "CT")

        Returns:
            District data with constituency names and centre code details
        """
        # Get district info from administration data
        district_info = None
        for district in self.administration_data["districts"]:
            if district["code"] == district_code:
                district_info = district
                break

        if not district_info:
            raise ValueError(f"District {district_code} not found in administration data")

        # Create constituency code to name mapping
        constituency_names = {}
        district_constituencies = set()
        for const in district_info["constituencies"]:
            constituency_names[const["code"]] = const["name"]
            district_constituencies.add(const["code"])

        # Collect all polling station results
        all_results = []
        page_count = self.get_page_count()

        logger.info(f"Extracting data for district {district_code} ({district_info['name']})")

        for page_num in range(page_count):
            page_results = self._parse_page_data(page_num)
            all_results.extend(page_results)

        # Group results by constituency with centre code details
        constituency_data = defaultdict(lambda: {
            "code": "",
            "name": "",
            "isLegacy": False,
            "centres": defaultdict(lambda: {
                "centreCode": "",
                "nullVotes": 0,
                "candidates": defaultdict(int)
            }),
            "candidates": defaultdict(int)
        })

        district_null_votes = 0

        for result in all_results:
            constituency_code = self.parse_constituency_from_centre(result.centre_code)

            # Only include results for this district
            if constituency_code not in district_constituencies:
                continue

            # Initialize constituency if not exists
            if not constituency_data[constituency_code]["code"]:
                constituency_data[constituency_code]["code"] = constituency_code
                constituency_data[constituency_code]["name"] = constituency_names[constituency_code]

            # Initialize centre if not exists
            centre_code = result.centre_code
            if not constituency_data[constituency_code]["centres"][centre_code]["centreCode"]:
                constituency_data[constituency_code]["centres"][centre_code]["centreCode"] = centre_code

            # Aggregate votes at centre level
            constituency_data[constituency_code]["centres"][centre_code]["nullVotes"] += result.null_votes
            for candidate_code, votes in result.candidate_votes.items():
                constituency_data[constituency_code]["centres"][centre_code]["candidates"][candidate_code] += votes

            # Aggregate votes at constituency level
            district_null_votes += result.null_votes
            for candidate_code, votes in result.candidate_votes.items():
                constituency_data[constituency_code]["candidates"][candidate_code] += votes

        # Convert to final format (matching 2019 structure exactly)
        constituencies = []
        for const_code in sorted(constituency_data.keys()):
            const_data = constituency_data[const_code]

            # Build constituency-level candidate totals only (no centres array)
            candidates = []
            for candidate in self.candidates:
                candidates.append({
                    "candidateCode": candidate.code,
                    "partyCode": candidate.party,
                    "votes": const_data["candidates"][candidate.code]
                })

            constituencies.append({
                "code": const_code,
                "isLegacy": False,
                "candidates": candidates
            })

        return {
            "districtCode": district_code,
            "type": "presidential",
            "nullVotes": district_null_votes,
            "constituencies": constituencies
        }
    
    def get_output_filename(self, district_code: str) -> str:
        """
        Get the output filename for a district.
        
        Args:
            district_code: 2-character district code
        
        Returns:
            Filename in format "{DISTRICT_CODE}_RESULTS.json"
        """
        return f"{district_code}_RESULTS.json"


if __name__ == "__main__":
    # Test the extractor
    pdf_path = "src/2020-Fresh-Presidential-Election-Results-Per-station.pdf"
    metadata_path = "metadata/administration.json"
    
    try:
        extractor = PDF2020Extractor(pdf_path, metadata_path)
        print(f"PDF has {extractor.get_page_count()} pages")
        
        candidates = extractor.extract_candidates()
        print(f"Candidates: {candidates}")
        
        # Test with Chitipa district
        district_data = extractor.extract_district_data("CT")
        print(f"Chitipa data: {len(district_data['constituencies'])} constituencies")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
