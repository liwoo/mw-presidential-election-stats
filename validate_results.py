
import json
import os

def validate_results():
    print("Starting validation...")
    results_dir = "2020/results/presidential"
    total_votes = {}
    total_null_votes = 0

    with open("metadata/administration.json") as f:
        administration = json.load(f)
    
    all_districts = {d["code"] for d in administration["districts"]}
    validated_districts = set()

    if not os.path.exists(results_dir):
        print(f"Directory not found: {results_dir}")
        return

    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            district_code = filename.split("_")[0]
            validated_districts.add(district_code)
            print(f"Validating {filename}...")
            file_path = os.path.join(results_dir, filename)
            with open(file_path) as f:
                data = json.load(f)

            # Validate structure
            assert "districtCode" in data
            assert "type" in data
            assert "nullVotes" in data
            assert "constituencies" in data

            total_null_votes += data["nullVotes"]

            for constituency in data["constituencies"]:
                assert "code" in constituency
                assert "candidates" in constituency
                for candidate in constituency["candidates"]:
                    assert "candidateCode" in candidate
                    assert "partyCode" in candidate
                    assert "votes" in candidate

                    # Aggregate votes
                    candidate_code = candidate["candidateCode"]
                    if candidate_code not in total_votes:
                        total_votes[candidate_code] = 0
                    total_votes[candidate_code] += candidate["votes"]

    print("\nValidation successful!")
    print("Total votes per candidate:")
    for candidate, votes in total_votes.items():
        print(f"{candidate}: {votes}")
    
    print(f"Total null votes: {total_null_votes}")

    missing_districts = all_districts - validated_districts
    if missing_districts:
        print("\nMissing districts:")
        for district in missing_districts:
            print(district)

if __name__ == "__main__":
    validate_results()
