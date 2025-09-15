
import json
import os
import glob

demographics_dir = r'C:\Users\lacso\Git\mw-presidential-election-stats\2025\demographics'
json_files = glob.glob(os.path.join(demographics_dir, '*_STATS.json'))

for file_path in json_files:
    with open(file_path, 'r') as f:
        data = json.load(f)

    for demographic in data['demographics']:
        male_voters = int(demographic['registeredMale'])
        female_voters = int(demographic['registeredFemale'])
        total_voters = male_voters + female_voters

        if total_voters > 0:
            male_percentage = round((male_voters / total_voters) * 100, 1)
            female_percentage = round((female_voters / total_voters) * 100, 1)
        else:
            male_percentage = 0.0
            female_percentage = 0.0
        
        demographic['percentageMale'] = str(male_percentage)
        demographic['percentageFemale'] = str(female_percentage)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated {file_path} with percentages.")
