
import re

def calculate_totals_from_text():
    print("Calculating totals directly from text file...")
    total_votes = {
        "LAZCHA": 0,
        "PETMUT": 0,
        "PETKUW": 0
    }
    total_null_votes = 0

    with open("data/2020-Constituency Presidential Results.pdf.txt") as f:
        lines = f.readlines()

    last_candidate = None
    for line in lines:
        line = line.strip()
        if "LAZARUS CHAKWERA" in line:
            last_candidate = "LAZCHA"
        elif "ARTHUR PETER MUTHARIKA" in line:
            last_candidate = "PETMUT"
        elif "PETER DOMINICO SINOSI DRIVER KUWANI" in line:
            last_candidate = "PETKUW"
        
        if "Votes:" in line and last_candidate:
            try:
                votes = int(re.search(r"Votes: ([\d,]+)", line).group(1).replace(",", "")))
                total_votes[last_candidate] += votes
                last_candidate = None # Reset last candidate after assigning votes
            except:
                pass

        if "Null and Void Votes" in line:
            try:
                null_votes = int(re.search(r"(\d+)", line).group(1)))
                total_null_votes += null_votes
            except:
                pass

    print("\n--- Final Vote Counts ---")
    for candidate, votes in total_votes.items():
        print(f"{candidate}: {votes}")
    print(f"Total null votes: {total_null_votes}")

if __name__ == "__main__":
    calculate_totals_from_text()
