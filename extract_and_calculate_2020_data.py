
import json
import re
import os

def extract_and_calculate_2020_data():
    print("Starting 2020 data extraction and calculation...")

    # Load metadata
    with open("metadata/administration.json") as f:
        administration = json.load(f)
    with open("metadata/candidates.json") as f:
        candidates = json.load(f)
    with open("metadata/parties.json") as f:
        parties = json.load(f)

    # Add missing candidate and party from 2020 election
    if not any(c["code"] == "PETKUW" for c in candidates):
        candidates.append({"code": "PETKUW", "firstname": "Peter", "lastname": "Kuwani", "fullname": "Peter Kuwani", "gender": "Male"})
    if not any(p["code"] == "MMD" for p in parties):
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
    lines = ocr_text.split('\n')

    for district in administration["districts"]:
        district_code = district["code"]
        results[district_code] = {
            "districtCode": district_code,
            "type": "presidential",
            "nullVotes": 0,
            "constituencies": []
        }
        for constituency in district["constituencies"]:
            constituency_code = constituency["code"]
            constituency_name = constituency["name"]
            print(f"Processing constituency: {constituency_name}")

            # Search for constituency name in the OCR text
            constituency_match_found = False
            for match in re.finditer(re.escape(constituency_name), ocr_text, re.IGNORECASE):
                start_index = match.start()
                # Extract a larger block of text around the constituency name
                end_of_search_block = min(start_index + 200, len(ocr_text)) # Search up to 200 characters after the name
                search_block = ocr_text[start_index:end_of_search_block]

                # Confirm it's a constituency block by looking for 'Constituency Results' or 'Constituency'
                if re.search(r"(?:Constituency Results|constituency)", search_block, re.IGNORECASE):
                    constituency_match_found = True
                    lines = search_block.strip().split('\n')

                    # Extract candidate data
                    candidate_data = []
                    null_votes = 0

                    for j, line in enumerate(lines):
                        current_candidate_code = None
                        if "LAZARUS CHAKWERA" in line:
                            current_candidate_code = "LAZCHA"
                        elif "PETER DOMINICO SINOSI DRIVER KUWANI" in line:
                            current_candidate_code = "PETKUW"
                        elif "ARTHUR PETER MUTHARIKA" in line:
                            current_candidate_code = "PETMUT"
                        
                        if current_candidate_code:
                            for k in range(j + 1, min(j + 5, len(lines))): # Search next 4 lines for votes
                                votes_match = re.search(r"Votes: ([\d,]+)", lines[k])
                                if votes_match:
                                    votes = int(votes_match.group(1).replace(",", ""))
                                    candidate_data.append({"candidateCode": current_candidate_code, "partyCode": party_map.get(current_candidate_code, "UNKNOWN"), "votes": votes})
                                    break
                        elif "Null and Void Votes" in line:
                            try:
                                null_votes = int(re.search(r"(\d+)", line).group(1))
                                results[district_code]["nullVotes"] += null_votes
                            except:
                                pass
                    
                    if candidate_data:
                        results[district_code]["constituencies"].append({
                            "code": constituency_code,
                            "isLegacy": False,
                            "candidates": candidate_data
                        })
                    break # Break after finding and processing the first valid constituency block
            if constituency_match_found:
                break # Break outer loop if constituency was found and processed
        
        if candidate_data:
            results[district_code]["constituencies"].append({
                "code": constituency["code"],
                "isLegacy": False,
                "candidates": candidate_data
            })

    # Write to files
    for district_code, data in results.items():
        if data["constituencies"]:
            file_path = f"2020/results/presidential/{district_code}_RESULTS.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Successfully generated {file_path}")

    # Recalculate and print totals
    total_votes = {}
    total_null_votes = 0
    for district_code, data in results.items():
        total_null_votes += data.get("nullVotes", 0)
        for constituency in data.get("constituencies", []):
            for candidate in constituency.get("candidates", []):
                candidate_code = candidate["candidateCode"]
                if candidate_code not in total_votes:
                    total_votes[candidate_code] = 0
                total_votes[candidate_code] += candidate["votes"]
    
    print("\n---------------------")
    print("Recalculated Total votes per candidate:")
    for candidate, votes in total_votes.items():
        print(f"{candidate}: {votes}")
    
    print(f"Total null votes: {total_null_votes}")

if __name__ == "__main__":
    extract_and_calculate_2020_data()
