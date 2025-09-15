
import json
import os

# Data for Chitipa District
chitipa_demographics = {
  "year": "2025",
  "district": "CT",
  "demographics": [
    {
      "constituencyCode": "001",
      "registeredMale": "6620",
      "registeredFemale": "7865"
    },
    {
      "constituencyCode": "002",
      "registeredMale": "8298",
      "registeredFemale": "9860"
    },
    {
      "constituencyCode": "003",
      "registeredMale": "7399",
      "registeredFemale": "8796"
    },
    {
      "constituencyCode": "004",
      "registeredMale": "7938",
      "registeredFemale": "9432"
    },
    {
      "constituencyCode": "005",
      "registeredMale": "9493",
      "registeredFemale": "11279"
    }
  ]
}

# Create the 2025/demographics directory if it doesn't exist
demographics_dir = 'C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2025\\demographics'
os.makedirs(demographics_dir, exist_ok=True)

# Write the CT_STATS.json file
ct_stats_path = os.path.join(demographics_dir, 'CT_STATS.json')
with open(ct_stats_path, 'w') as f:
    json.dump(chitipa_demographics, f, indent=2)

print(f"Generated {ct_stats_path}")

# Create the 2025/track_records directory
track_records_dir = 'C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2025\\track_records'
os.makedirs(track_records_dir, exist_ok=True)

# Create a README.md in the track_records directory
readme_path = os.path.join(track_records_dir, 'README.md')
with open(readme_path, 'w') as f:
    f.write("This directory is intended to store track records of candidates. The format and content are yet to be defined. Please provide more details on what you would like to see here.")

print(f"Generated {readme_path}")
