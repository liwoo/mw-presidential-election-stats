import json
import os
import re

def find_district_code(district_name, admin_data):
    for district in admin_data['districts']:
        if district['name'].lower() == district_name.lower():
            return district['code']
    return None

def find_candidate_code(candidate_name, candidate_data):
    for candidate in candidate_data:
        if candidate['lastname'].lower() in candidate_name.lower():
            return candidate['code']
    return "UNKNOWN"

def find_party_code(party_name, party_data):
    for party in party_data:
        if party['abbreviation'] == party_name:
            return party['code']
    return "UNKNOWN"

def parse_2014_data(ocr_text, admin_data, candidate_data, party_data):
    pages = re.split(r'==End of OCR for page \d+==', ocr_text)
    all_district_results = {}
    valid_district_names = [d['name'].lower() for d in admin_data['districts']]

    for page in pages:
        if not page.strip():
            continue

        lines = page.split('\n')
        district_name = None
        for line in lines:
            if line.strip().lower() in valid_district_names:
                district_name = line.strip()
                break
        
        if not district_name:
            continue

        if "M'MBELWA" in district_name:
            district_name = "Mzimba"

        district_code = find_district_code(district_name, admin_data)
        if not district_code:
            continue

        candidate_matches = re.findall(r'([A-Z][a-z].*?)\n([A-Z]{2,})\n(\d+)', page)
        
        candidates = []
        for match in candidate_matches:
            candidate_name = match[0].strip()
            party_abbr = match[1].strip()
            votes = int(match[2])

            candidate_code = find_candidate_code(candidate_name, candidate_data)
            party_code = find_party_code(party_abbr, party_data)

            if party_code != "UNKNOWN":
                candidates.append({
                    "candidateCode": candidate_code,
                    "partyCode": party_code,
                    "votes": votes
                })

        null_votes_match = re.search(r'NULL & VOID\n(\d+)', page)
        null_votes = int(null_votes_match.group(1)) if null_votes_match else 0

        constituency = {"code": "000", "isLegacy": True, "candidates": candidates}

        district_results = {
            "districtCode": district_code,
            "type": "presidential",
            "nullVotes": null_votes,
            "constituencies": [constituency]
        }
        
        all_district_results[district_code] = district_results

    return all_district_results

def main():
    with open('metadata/administration.json', 'r') as f:
        admin_data = json.load(f)
    with open('ocr_2014.txt', 'r') as f:
        ocr_text = f.read()
    with open('metadata/candidates.json', 'r') as f:
        candidate_data = json.load(f)
    with open('metadata/parties.json', 'r') as f:
        party_data = json.load(f)

    parsed_results = parse_2014_data(ocr_text, admin_data, candidate_data, party_data)

    output_dir = '2014/results/presidential'
    for district_code, data in parsed_results.items():
        file_path = os.path.join(output_dir, f"{district_code}_RESULTS.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully wrote {file_path}")

if __name__ == '__main__':
    main()