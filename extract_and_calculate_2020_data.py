import json
import os
import re

def get_administration_data():
    with open("metadata/administration.json", "r") as f:
        return json.load(f)

def get_candidates_data():
    with open("metadata/candidates.json", "r") as f:
        return json.load(f)

def get_parties_data():
    with open("metadata/parties.json", "r") as f:
        return json.load(f)

def find_constituency_code(admin_data, full_constituency_name):
    # print(f"Debugging find_constituency_code: Looking for '{full_constituency_name}'")
    # Try to find exact match first
    for district in admin_data["districts"]:
        for constituency in district["constituencies"]:
            if full_constituency_name.lower() == constituency["name"].lower():
                # print(f"Found exact match: {constituency['code']}, {district['code']}")
                return constituency["code"], district["code"]
    
    # If no exact match, try partial matching for district and then constituency
    for district in admin_data["districts"]:
        # print(f"Checking district: {district['name']}")
        if district["name"].lower() in full_constituency_name.lower():
            for constituency in district["constituencies"]:
                # print(f"  Checking constituency: {constituency['name']}")
                if constituency["name"].lower() in full_constituency_name.lower():
                    # print(f"Found partial match: {constituency['code']}, {district['code']}")
                    return constituency["code"], district["code"]
    # print(f"No constituency code found for '{full_constituency_name}'")
    return None, None

def find_candidate_code(candidates_data, candidate_name):
    # print(f"Debugging find_candidate_code: Looking for '{candidate_name}'")
    for candidate in candidates_data:
        if candidate_name.lower() in candidate["fullname"].lower() or \
           candidate_name.lower() in candidate["lastname"].lower() or \
           candidate["fullname"].lower() in candidate_name.lower() or \
           candidate["lastname"].lower() in candidate_name.lower():
            # print(f"Found candidate code: {candidate['code']}")
            return candidate["code"]
    # print(f"Candidate code not found for '{candidate_name}'")
    return "UNKNOWN"

def find_party_code(parties_data, party_abbreviation):
    # print(f"Debugging find_party_code: Looking for '{party_abbreviation}'")
    for party in parties_data:
        if party["abbreviation"].lower() == party_abbreviation.lower():
            # print(f"Found party code: {party['code']}")
            return party["code"]
    # print(f"Party code not found for '{party_abbreviation}'")
    return "UNKNOWN"

def parse_pdf_data(pdf_text, admin_data, candidates_data, parties_data):
    results = {}
    
    # Regex to find constituency blocks
    constituency_block_regex = re.compile(r"(.+? Constituency Results)\n(.*?)(?=(?:.+? Constituency Results)|$)", re.DOTALL)

    for match in constituency_block_regex.finditer(pdf_text):
        constituency_header = match.group(1).strip()
        constituency_content = match.group(2).strip()

        constituency_full_name = constituency_header.replace(" Constituency Results", "").strip()
        
        constituency_code, district_code = find_constituency_code(admin_data, constituency_full_name)

        if not district_code:
            print(f"Warning: Could not determine district for constituency: {constituency_full_name}. Skipping.")
            continue

        if district_code not in results:
            results[district_code] = {
                "districtCode": district_code,
                "type": "presidential",
                "nullVotes": 0,
                "constituencies": []
            }

        # Extract candidate information
        candidate_lines = re.findall(r"([A-Z\s]+)\n([A-Z]+)\nVotes: ([\d,]+)", constituency_content)
        
        candidates_in_constituency = {}
        for cand_name, party_abbr, votes_str in candidate_lines:
            candidate_code = find_candidate_code(candidates_data, cand_name.strip())
            party_code = find_party_code(parties_data, party_abbr.strip())
            votes = int(votes_str.replace(",", ""))

            if candidate_code in candidates_in_constituency:
                candidates_in_constituency[candidate_code]["votes"] += votes
            else:
                candidates_in_constituency[candidate_code] = {
                    "candidateCode": candidate_code,
                    "partyCode": party_code,
                    "votes": votes
                }
        
        final_candidates = list(candidates_in_constituency.values())

        null_votes_match = re.search(r"Null and Void Votes\s+([\d,]+)", constituency_content)
        null_votes = int(null_votes_match.group(1).replace(",", "")) if null_votes_match else 0
        
        results[district_code]["nullVotes"] += null_votes

        if constituency_code:
            results[district_code]["constituencies"].append({
                "code": constituency_code,
                "isLegacy": False,
                "candidates": final_candidates
            })
        else:
            print(f"Warning: Could not find constituency code for {constituency_full_name}. Skipping.")

    return results

def main():
    admin_data = get_administration_data()
    candidates_data = get_candidates_data()
    parties_data = get_parties_data()

    with open("data/Constituency2020PresidentialResults.pdf.txt", "r") as f:
        pdf_text = f.read()

    presidential_results = parse_pdf_data(pdf_text, admin_data, candidates_data, parties_data)

    output_dir = "2020/results/presidential"
    os.makedirs(output_dir, exist_ok=True)

    for district_code, data in presidential_results.items():
        file_path = os.path.join(output_dir, f"{district_code}_RESULTS.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()