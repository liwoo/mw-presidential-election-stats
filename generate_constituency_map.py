import json
import os

# This will store the mapping: { "Constituency Name": {"code": "XXX", "districtCode": "YY"} }
constituency_map = {}

# List of parliamentary and presidential results files (from previous glob)
parliamentary_files = [
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\BA_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\BL_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\CK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\CR_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\CT_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\DE_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\DO_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\KR_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\KS_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\LI_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\LK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MC_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MG_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MW_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\MZ_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NB_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NE_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NI_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NS_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\NU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\PH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\RU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\SA_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\TH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\parliamentary\\ZO_RESULTS.json"
]

presidential_files = [
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\BA_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\BL_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\CK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\CR_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\CT_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\DE_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\DO_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\KR_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\KS_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\LI_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\LK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MC_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MG_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MW_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\MZ_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NB_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NE_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NI_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NK_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NS_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\NU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\PH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\RU_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\SA_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\TH_RESULTS.json",
    "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\results\\presidential\\ZO_RESULTS.json"
]

def build_constituency_map(file_list, is_parliamentary=True):
    for file_path in file_list:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                district_code = data.get("districtCode")
                constituencies = data.get("constituencies", [])
                for constituency in constituencies:
                    name = constituency.get("name")
                    code = constituency.get("code")
                    if name and code:
                        # Prioritize parliamentary results if there are duplicates
                        if is_parliamentary or name not in constituency_map:
                            constituency_map[name] = {"code": code, "districtCode": district_code}
        except Exception as e:
            print(f"Error reading or parsing {file_path}: {e}")

# Build map from parliamentary files first
build_constituency_map(parliamentary_files, is_parliamentary=True)
# Then add/override with presidential files (only if not already present from parliamentary)
build_constituency_map(presidential_files, is_parliamentary=False)

# Save the constituency map to a JSON file for later use
output_map_path = "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\constituency_map.json"
with open(output_map_path, 'w') as f:
    json.dump(constituency_map, f, indent=2)

print(f"Constituency map generated and saved to {output_map_path}")
