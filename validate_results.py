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

def find_constituency_details(admin_data, district_name, constituency_name):
    for district in admin_data["districts"]:
        if district["name"].lower() == district_name.lower():
            for constituency in district["constituencies"]:
                if constituency["name"].lower() == constituency_name.lower():
                    return constituency["code"], district["code"]
    return None, None

def find_candidate_by_code(candidates_data, candidate_code):
    for candidate in candidates_data:
        if candidate["code"] == candidate_code:
            return candidate
    return None

def find_party_by_code(parties_data, party_code):
    for party in parties_data:
        if party["code"] == party_code:
            return party
    return None

def parse_pdf_for_null_votes(pdf_text):
    null_votes_data = {}
    constituency_regex = re.compile(r"(.+?) Constituency Results\n.*?Null and Void Votes\s+(\d+)", re.DOTALL)

    for match in constituency_regex.finditer(pdf_text):
        constituency_full_name = match.group(1).strip()
        null_votes = int(match.group(2))
        null_votes_data[constituency_full_name] = null_votes
    return null_votes_data

def validate_results():
    print("Starting validation...")
    results_dir = "2020/results/presidential"
    
    admin_data = get_administration_data()
    candidates_data = get_candidates_data()
    parties_data = get_parties_data()

    with open("data/Constituency2020PresidentialResults.pdf.txt", "r") as f:
        pdf_text = f.read()
    pdf_null_votes_data = parse_pdf_for_null_votes(pdf_text)

    all_district_codes = {d["code"] for d in admin_data["districts"]}
    validated_district_codes = set()

    if not os.path.exists(results_dir):
        print(f"Error: Directory not found: {results_dir}")
        return

    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(results_dir, filename)
            print(f"Validating {filename}...")
            
            with open(file_path, "r") as f:
                data = json.load(f)

            # 1. Validate basic structure
            assert "districtCode" in data, f"Missing districtCode in {filename}"
            assert "type" in data, f"Missing type in {filename}"
            assert "nullVotes" in data, f"Missing nullVotes in {filename}"
            assert "constituencies" in data, f"Missing constituencies in {filename}"

            district_code = data["districtCode"]
            validated_district_codes.add(district_code)

            # 2. Verify districtCode exists in administration.json
            if district_code not in all_district_codes:
                print(f"Warning: Unknown districtCode '{district_code}' in {filename}")

            # 3. Validate nullVotes consistency with PDF
            calculated_null_votes_from_constituencies = 0
            for constituency_data in data["constituencies"]:
                constituency_name_from_admin = None
                for district_admin in admin_data["districts"]:
                    if district_admin["code"] == district_code:
                        for const_admin in district_admin["constituencies"]:
                            if const_admin["code"] == constituency_data["code"]:
                                constituency_name_from_admin = const_admin["name"]
                                break
                        if constituency_name_from_admin: break

                if constituency_name_from_admin:
                    # Adjust constituency name to match PDF format (e.g., 'Chitipa East' vs 'Chitipa East Constituency Results')
                    pdf_constituency_name_key = f"{constituency_name_from_admin} Constituency Results"
                    if pdf_constituency_name_key in pdf_null_votes_data:
                        calculated_null_votes_from_constituencies += pdf_null_votes_data[pdf_constituency_name_key]
                    else:
                        print(f"Warning: Null votes for '{constituency_name_from_admin}' not found in PDF data for {filename}")
                else:
                    print(f"Warning: Constituency code '{constituency_data['code']}' not found in admin data for district {district_code} in {filename}")

            if data["nullVotes"] != calculated_null_votes_from_constituencies:
                print(f"Error: nullVotes mismatch in {filename}. Expected {calculated_null_votes_from_constituencies}, got {data['nullVotes']}")

            # 4. Validate constituencies
            for constituency in data["constituencies"]:
                assert "code" in constituency, f"Missing constituency code in {filename}"
                assert "candidates" in constituency, f"Missing candidates list in constituency {constituency['code']} in {filename}"

                # Verify constituency code exists in administration.json for the given district
                found_constituency_in_admin = False
                for district_admin in admin_data["districts"]:
                    if district_admin["code"] == district_code:
                        for const_admin in district_admin["constituencies"]:
                            if const_admin["code"] == constituency["code"]:
                                found_constituency_in_admin = True
                                break
                        if found_constituency_in_admin: break
                if not found_constituency_in_admin:
                    print(f"Warning: Constituency code '{constituency['code']}' not found in administration data for district '{district_code}' in {filename}")

                # Check for duplicate candidates within the constituency
                seen_candidate_codes = set()
                for candidate in constituency["candidates"]:
                    if candidate["candidateCode"] in seen_candidate_codes:
                        print(f"Error: Duplicate candidate '{candidate['candidateCode']}' in constituency '{constituency['code']}' in {filename}")
                    seen_candidate_codes.add(candidate["candidateCode"])

                    # 5. Validate candidate and party codes
                    assert "candidateCode" in candidate, f"Missing candidateCode in {filename}"
                    assert "partyCode" in candidate, f"Missing partyCode in {filename}"
                    assert "votes" in candidate, f"Missing votes in {filename}"

                    if not find_candidate_by_code(candidates_data, candidate["candidateCode"]):
                        print(f"Warning: Unknown candidateCode '{candidate['candidateCode']}' in constituency '{constituency['code']}' in {filename}")
                    if not find_party_by_code(parties_data, candidate["partyCode"]):
                        print(f"Warning: Unknown partyCode '{candidate['partyCode']}' for candidate '{candidate['candidateCode']}' in constituency '{constituency['code']}' in {filename}")
                    assert isinstance(candidate["votes"], int), f"Votes for candidate '{candidate['candidateCode']}' in constituency '{constituency['code']}' in {filename}' is not an integer."

    print("\nValidation complete. Checking for missing district files...")
    missing_district_files = all_district_codes - validated_district_codes
    if missing_district_files:
        print("Error: The following district files are missing:")
        for code in sorted(list(missing_district_files)):
            print(f"- {code}_RESULTS.json")
    else:
        print("All expected district files are present.")

    print("\nOverall validation finished.")

if __name__ == "__main__":
    validate_results()