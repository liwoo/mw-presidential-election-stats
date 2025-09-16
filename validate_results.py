
import json
import os

def validate_results():
    print("Starting validation...")
    results_dir = "2020/results/presidential"
    total_votes = {}
    total_null_votes = 0

    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
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

    print("Validation successful!")
    print("Total votes per candidate:")
    for candidate, votes in total_votes.items():
        print(f"{candidate}: {votes}")
    
    print(f"Total null votes: {total_null_votes}")

if __name__ == "__main__":
    validate_results()
