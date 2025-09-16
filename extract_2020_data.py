
import json
import re

def extract_2020_data():
    print("Starting data extraction...")
    # Load metadata
    with open("metadata/administration.json") as f:
        administration = json.load(f)
    print("Loaded administration data.")
    with open("metadata/candidates.json") as f:
        candidates = json.load(f)
    print("Loaded candidates data.")
    with open("metadata/parties.json") as f:
        parties = json.load(f)

    # Add missing candidate and party from 2019 election
    candidates.append({"code": "PETKUW", "firstname": "Peter", "lastname": "Kuwani", "fullname": "Peter Kuwani", "gender": "Male"})
    parties.append({"code": "MMD", "name": "Mbakuwaku Movement for Development", "abbreviation": "MMD"})

    # Create mapping for faster lookup
    candidate_map = {c["fullname"].upper(): c["code"] for c in candidates}
    candidate_map["LAZARUS CHAKWERA"] = "LAZCHA"
    candidate_map["ARTHUR PETER MUTHARIKA"] = "PETMUT"
    candidate_map["PETER DOMINICO SINOSI DRIVER KUWANI"] = "PETKUW"
    party_map = {p["abbreviation"]: p["code"] for p in parties}

    # In-memory store for results
    results = {}

    # Read PDF content
    with open("data/2020-Constituency Presidential Results.pdf.txt") as f:
        ocr_text = f.read()

    # Regex to find constituency results
    constituency_regex = re.compile(r"(.+?) Constituency Results", re.IGNORECASE)
    
    # Split text by page
    pages = ocr_text.split("==End of OCR for page")

    for page_num, page in enumerate(pages):
        lines = page.strip().split("\n")
        
        # Find constituencies in the page
        for i, line in enumerate(lines):
            match = constituency_regex.search(line)
            if match:
                constituency_name_full = match.group(1).strip()
                
                # Find the district and constituency codes
                district_code = None
                constituency_code = None
                for district in administration["districts"]:
                    for constituency in district["constituencies"]:
                        if constituency["name"].upper() in constituency_name_full.upper() or constituency_name_full.upper() in constituency["name"].upper():
                            district_code = district["code"]
                            constituency_code = constituency["code"]
                            break
                    if district_code:
                        break
                
                if not district_code:
                    continue

                if district_code not in results:
                    results[district_code] = {
                        "districtCode": district_code,
                        "type": "presidential",
                        "nullVotes": 0,
                        "constituencies": []
                    }

                # Extract candidate data
                candidate_data = []
                null_votes = 0
                
                # Look for candidates in the lines following the constituency name
                for j in range(i + 1, len(lines)):
                    line_text = lines[j]
                    if "Constituency Results" in line_text: # Stop at next constituency
                        break

                    votes_match = re.search(r"Votes: ([\d,]+)", line_text)
                    if votes_match:
                        votes = int(votes_match.group(1).replace(",", ""))
                        # Find which candidate the votes belong to
                        # Look at previous lines
                        for k in range(j - 1, max(j - 4, -1), -1):
                            prev_line = lines[k]
                            if "LAZARUS CHAKWERA" in prev_line:
                                candidate_data.append({"candidateCode": "LAZCHA", "partyCode": "MCP", "votes": votes})
                                break
                            elif "PETER DOMINICO SINOSI DRIVER KUWANI" in prev_line:
                                candidate_data.append({"candidateCode": "PETKUW", "partyCode": "MMD", "votes": votes})
                                break
                            elif "ARTHUR PETER MUTHARIKA" in prev_line:
                                candidate_data.append({"candidateCode": "PETMUT", "partyCode": "DPP", "votes": votes})
                                break

                    elif "Null and Void Votes" in line_text:
                        try:
                            null_votes = int(re.search(r"(\\d+)", line_text).group(1))
                        except (AttributeError, IndexError):
                            pass

                if candidate_data:
                    results[district_code]["constituencies"].append({
                        "code": constituency_code,
                        "isLegacy": False,
                        "candidates": candidate_data
                    })
                    results[district_code]["nullVotes"] += null_votes


    # Write to files
    for district_code, data in results.items():
        file_path = f"2020/results/presidential/{district_code}_RESULTS.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully generated {file_path}")

if __name__ == "__main__":
    extract_2020_data()
