import re
import json
import os

ocr_content = '''
Region Name District Name
Constituency Name Ward Name
Center Name
Center Code
Male Youths Female
Total Youths % Youth to
Youths
Total
Registrants
Northern
Region
Chitipa
Chitipa Central
Yamba
Ifumbo School
01077
205
260
465
58.05%
Chinunkha School
01078
126
139
265
55.56%
Chitipa Model School
01079
332
422
754
55.44%
Ipulukutu School
01080
101
124
225
57.40%
Isyalikira School
01081
410
552
962
60.47%
Kasinde School
01082
123
154
277
52.36%
Mwakalomba School
01083
48
74
122
49.19%
Ichinga School
01084
145
209
354
53.15%
Katutula School
01085
210
303
513
48.90%
Kawale School
01086
421
403
824
56.36%
Msangano School
01087
80
106
186
52.84%
Chitipa Community Hall
01088
1,013
1,079
2,092
56.71%
Lwakwa School
01089
167
209
376
45.91%
Chimwemwe School
01090
206
237
443
51.57%
Lwambo School
01091
134
173
307
45.35%
Ilanga School
01092
150
192
342
52.21%
Muswero School
01093
94
100
194
62.18%
Namuyemba School
01094
194
252
446
53.41%
Chitipa CCAP School
01095
718
1,013
1,731
60.21%
Yamba School
01096
140
136
276
51.98%
Kakoma School
01097
124
145
269
49.72%
Kaseye School
01098
119
177
296
57.48%
Mbula School
01099
77
92
169
53.14%
Zunawala School
01100
49
60
109
55.33%
Naviziba school
01151
89
121
210
52.76%
Nakachenja School
01152
141
194
335
50.83%
Chiwale School
01153
56
55
111
58.12%
Total for Yamba Ward
5,672
6,981
12,653
55.02%
Zambwe
Namuchese School
01059
89
105
194
50.13%
Ibanda School
01060
127
135
262
51.88%
Zambwe School
01061
124
126
250
52.97%
Chendo School
01062
149
241
390
47.79%
Mubanga School
01063
239
342
581
48.66%
Lufita School
01064
428
629
1,057
58.33%
Namatubi School
01065
140
169
309
50.74%
Kanyenjere School
01066
154
179
333
49.26%
Meru School
01067
217
275
492
52.79%
Ntcherenje School
01068
184
236
420
52.90%
Nachipanga-panga
01069
95
150
245
50.20%
Miyombo School
01070
79
103
182
47.15%
Ilema School
01071
199
238
437
51.53%
Muselema School
01072
191
238
429
51.81%
Tondola School
01073
137
196
333
51.87%
Kadoli School
01074
127
156
283
51.74%
Mung'ongo School
01075
90
90
180
51.58%
Nkhamanga School
01076
160
188
348
53.05%
Chaba School
01149
134
171
305
50.41%
Chiparanje School
01150
148
176
324
57.75%
Total for Zambwe Ward
3,211
4,143
7,354
52.13%
Total for Chitipa Central Constituencv
8,883
11,124
20,007
53.92%
Chitipa East
Iponjola
Chuba School
01001
118
110
228
54.16%
Kasumbi School
01002
163
171
334
53.96%
Iponiola Schoool
01003
101
111
212
52.87%
Itulo School
01004
83
85
168
46.93%
Chinongo School
01005
147
151
298
52.28%
Sofwe School
01006
60
73
133
53.63%
Muahese School
01007
77
83
160
47.90%
Mughona School
01008
74
83
157
45.11%
Malira School
01009
76
95
171
51.82%
Chanya School
01010
127
146
273
56.64%
Chilashi School
01011
67
57
124
50.41%
Lughesyo School
01012
310
352
662
55.07%
Misuku Coffee Authority
01013
75
70
145
51.79%
Nyungu School
01014
92
102
194
49.36%
Ibabala School
01015
102
97
199
51.03%
Kapyela School
01016
37
57
94
46.77%
Ipyana School
01145
100
103
203
53.70%
Total for Iponjola Ward
1,809
1,946
3,755
52.15%
Kapoka
Chisansu School
01017
232
249
481
59.75%
Chatu School
01018
93
110
203
53.99%
Chipwela School
01019
124
152
276
48.34%
Chisitu School
01020
55
68
123
49.60%
Naching'anda School
01021
288
299
587
59.84%
Kapoka School
01022
160
204
364
50.84%
Chibanda School
01023
106
108
214
52.97%
Mwandambo School
01024
49
67
116
45.49%
Kasitu School
01025
97
89
186
48.06%
Malamula School
01026
24
34
58
51.79%
Kasaghala School
01027
137
160
297
55.93%
Sokola School
01028
105
113
218
50.11%
Mutogha School
01029
97
128
225
53.57%
Nakabushi School
01030
44
58
102
44.74%
Kalenge CCAP JP School
01146
74
73
147
62.29%
Total for Kapoka Ward
1,685
1.912
3,597
53.65%
Chitipa North
Total for Chitipa East Constituency
Hanga
3,494
3,858
7,352
52.87%
Ilenao School
01115
266
344
610
54.61%
Titi School
01116
121
153
274
55.02%
Ipenza School
01117
129
187
316
44.20%
Ipula School
01118
82
100
182
49.06%
Chiwanga School
01119
116
123
239
55.45%
Chipitu School
01120
100
123
223
53.86%
Kapere School
01121
101
140
241
48.10%
Nahatobo School
01122
155
194
349
54.53%
Nankhonza School
01123
127
168
295
48.36%
Nkhanga School
01124
148
155
303
52.33%
Ibunzya School
01156
118
166
284
54.10%
'''

# Mappings (hardcoded based on constituency_map.json)
constituency_name_to_code = {
    "Balaka Central East": "153", "Balaka North": "154", "Balaka West": "155", "Balaka South": "156",
    "Blantyre North": "170", "Blantyre North East": "173", "Blantyre Rural East": "171", "Blantyre South West": "174",
    "Blantyre City Centre": "175", "Blantyre Malabada": "199", "Blantyre City South": "200", "Blantyre City East": "201",
    "Blantyre Bangwe": "202", "Blantyre City South East": "203", "Blantyre City West": "204", "Blantyre Kabula": "205",
    "Blantyre West": "172",
    "Chikwawa South": "215", "Chikwawa Mkombezi": "214", "Chikwawa Central": "212", "Chikwawa North": "210",
    "Chikwawa East": "213", "Chikwawa West": "209",
    "Chiradzulu South": "185", "Chiradzulu Central": "186", "Chiradzulu North": "187", "Chiradzulu East": "188",
    "Chiradzulu West": "189",
    "Chitipa East": "003", "Chitipa South": "005", "Chitipa Central": "002", "Chitipa North": "001",
    "Chitipa Chendo": "004",
    "Dedza North": "114", "Dedza Central": "115", "Dedza South West": "116", "Dedza North West": "117",
    "Dedza East": "118", "Dedza South": "119", "Dedza West": "120", "Dedza Central East": "121",
    "Dowa East": "067", "Dowa South East": "069", "Dowa North East": "065", "Dowa Ngala": "060",
    "Dowa Central": "063", "Dowa West": "066", "Dowa North": "064",
    "Karonga North": "006", "Karonga North West": "007", "Karonga Central": "008", "Karonga Nyungwe": "009",
    "Karonga South": "010",
    "Kasungu North": "044", "Kasungu North North East": "047", "Kasungu West": "046", "Kasungu North West": "045",
    "Kasungu South": "053", "Kasungu South East": "051", "Kasungu East": "048", "Kasungu Central": "050",
    "Likoma Islands": "038",
    "Lilongwe Mapuyu North": "089", "Lilongwe Mapuyu South": "095", "Lilongwe North": "084", "Lilongwe Msozi South": "097",
    "Lilongwe Msozi North": "096", "Lilongwe Kumachenga": "090", "Lilongwe North East": "088", "Lilongwe City West": "111",
    "Lilongwe Mpenu Nkhoma": "098", "Lilongwe Mpenu": "094", "Lilongwe South East": "105", "Lilongwe East": "087",
    "Lilongwe Central": "093", "Lilongwe City Centre": "104", "Lilongwe North West": "112", "Lilongwe City North": "102",
    "Lilongwe South West": "109", "Lilongwe City South East": "110", "Lilongwe City South West": "108",
    "Lilongwe Msinja North": "101", "Lilongwe Msinja South": "100", "Lilongwe South": "099",
    "Machinga North East": "145", "Machinga Central": "147", "Machinga Central East": "150", "Machinga East": "148",
    "Machinga South": "152", "Machinga Likwenu": "151", "Machinga South East": "146",
    "Mangochi North": "132", "Mangochi North East": "138", "Mangochi Malombe": "142", "Mangochi East": "134",
    "Mangochi South": "141", "Mangochi South West": "140", "Mangochi Central": "137", "Mangochi Nkungulu": "143",
    "Mangochi West": "136", "Mangochi Monkey Bay": "135", "Mangochi Lutende": "133", "Mangochi Masongola": "139",
    "Mchinji North": "071", "Mchinji North East": "070", "Mchinji East": "072", "Mchinji Central": "074",
    "Mchinji South": "076", "Mchinji South West": "075",
    "Mulanje South East": "197", "Mulanje South": "195", "Mulanje Central": "196", "Mulanje Limbuli": "194",
    "Mulanje Bale": "198", "Mulanje South West": "193", "Mulanje Pasani": "192", "Mulanje West": "191",
    "Mulanje North": "190",
    "Mwanza Central": "178", "Mwanza West": "179",
    "Mzimba North": "016", "Mzimba North East": "019", "Mzimba West": "017", "Mzimba South": "026",
    "Mzimba Central": "020", "Mzimba Hora": "022", "Mzimba Luwerezi": "028", "Mzimba Solola": "024",
    "Mzimba East": "021", "Mzimba South West": "023", "Mzimba South East": "027", "Mzuzu City": "018",
    "Neno South": "169", "Neno North": "167",
    "Nkhata Bay North": "029", "Nkhata Bay Central": "031", "Nkhata Bay West": "032", "Nkhata Bay North West": "033",
    "Nkhata Bay South East": "035", "Nkhata Bay South": "034",
    "Nkhotakota North": "039", "Nkhotakota North East": "040", "Nkhotakota Central": "041", "Nkhotakota South": "042",
    "Nkhotakota South East": "043",
    "Nsanje South": "228", "Nsanje South West": "228", "Nsanje Central": "227", "Nsanje Lalanje": "226",
    "Nsanje North": "225",
    "Ntcheu North East": "124", "Ntcheu Bwanje North": "125", "Ntcheu Bwanje South": "126", "Ntcheu Central": "128",
    "Ntcheu South": "131", "Ntcheu North": "124", "Ntcheu West": "129",
    "Ntchisi East": "058", "Ntchisi South": "059", "Ntchisi North": "055", "Ntchisi North East": "056",
    "Phalombe South": "183", "Phalombe Central": "182", "Phalombe North": "180", "Phalombe East": "184",
    "Phalombe North East": "181",
    "Rumphi East": "014", "Rumphi Central": "015", "Rumphi West": "013", "Rumphi North": "012",
    "Salima North": "077", "Salima Central": "080", "Salima South": "082", "Salima South East": "083",
    "Salima North West": "078",
    "Thyolo North": "216", "Thyolo West": "217", "Thyolo Central": "220", "Thyolo South (Thekerani)": "223",
    "Thyolo East": "218", "Thyolo South West": "222", "Thyolo Thava": "221",
    "Zomba Nsondole": "159", "Zomba Thondwe": "165", "Zomba Chingale": "160", "Zomba Changalume": "162",
    "Zomba Lisanjala": "166", "Zomba Malosa": "158", "Zomba Ntonya": "163", "Zomba Central/City": "176",
    "Zomba Likangala": "161", "Zomba Chisi": "164"
}

district_name_to_code = {
    "Balaka": "BA", "Blantyre": "BL", "Chikhwawa": "CK", "Chiradzulu": "CR", "Chitipa": "CT",
    "Dedza": "DE", "Dowa": "DO", "Karonga": "KR", "Kasungu": "KS", "Likoma": "LK",
    "Lilongwe": "LI", "Machinga": "MH", "Mangochi": "MG", "Mchinji": "MC", "Mulanje": "MU",
    "Mwanza": "MW", "Mzimba": "MZ", "Neno": "NE", "Nkhatabay": "NB", "Nkhotakota": "NK",
    "Nsanje": "NS", "Ntcheu": "NU", "Ntchisi": "NI", "Phalombe": "PH", "Rumphi": "RU",
    "Salima": "SA", "Thyolo": "TH", "Zomba": "ZO"
}

demographics_data = {}
current_district_name = None

lines = ocr_content.split('\n')

# State machine for parsing
# 0: Looking for Region Name
# 1: Found Region Name, looking for District Name
# 2: Found District Name, processing constituencies
parsing_state = 0

for i, line in enumerate(lines):
    stripped_line = line.strip()

    if parsing_state == 0:
        if stripped_line in ["Northern", "Central", "Southern"]:
            parsing_state = 1
            # print(f"DEBUG: Found Region marker: {stripped_line}") # Debugging
            continue
    elif parsing_state == 1:
        if stripped_line == "Region": # This line is just "Region"
            continue
        else:
            # This should be the District Name
            if stripped_line in district_name_to_code:
                current_district_name = stripped_line
                parsing_state = 2
                # print(f"DEBUG: Identified District: {current_district_name}") # Debugging
            else:
                # If it's not a known district, reset state or handle error
                # print(f"DEBUG: Warning: Unknown district name found after Region: {stripped_line}") # Debugging
                current_district_name = None # Reset to avoid incorrect association
                parsing_state = 0 # Reset state
            continue

    if parsing_state == 2:
        # Try to find a constituency total
        constituency_total_pattern = re.compile(r'Total for (.*?) Constituenc[vy]\s+([\d,]+)\s+([\d,]+)')
        constituency_match = constituency_total_pattern.match(stripped_line)

        if constituency_match:
            constituency_raw_name = constituency_match.group(1).strip()
            male_youths = int(constituency_match.group(2).replace(',', ''))
            female_youths = int(constituency_match.group(3).replace(',', ''))

            # Normalize constituency name for lookup
            constituency_name_for_lookup = constituency_raw_name
            if constituency_name_for_lookup.endswith(" Constituency"):
                constituency_name_for_lookup = constituency_name_for_lookup.replace(" Constituency", "").strip()

            # Apply specific replacements for known OCR discrepancies
            # This is a more robust way to handle the known issues.
            # print(f"DEBUG: Processing constituency raw name: {constituency_name_for_lookup}") # Debugging
            for old, new in replacements.items():
                if constituency_name_for_lookup == old:
                    constituency_name_for_lookup = new
                    # print(f"DEBUG: Applied replacement: {old} -> {new}") # Debugging
                    break

            constituency_code = constituency_name_to_code.get(constituency_name_for_lookup)

            if constituency_code:
                district_code = district_name_to_code.get(current_district_name)
                if district_code:
                    if district_code not in demographics_data:
                        demographics_data[district_code] = {
                            "year": "2019",
                            "district": district_code,
                            "demographics": []
                        }
                    demographics_data[district_code]["demographics"].append({
                        "constituencyCode": constituency_code,
                        "registeredMale": str(male_youths),
                        "registeredFemale": str(female_youths),
                        "percentageMale": f"{((male_youths / (male_youths + female_youths)) * 100):.1f}%" if (male_youths + female_youths) > 0 else "0.0%",
                        "percentageFemale": f"{((female_youths / (male_youths + female_youths)) * 100):.1f}%" if (male_youths + female_youths) > 0 else "0.0%"
                    })
                    # print(f"DEBUG: Added data for {current_district_name} - {constituency_name_for_lookup}") # Debugging
                else:
                    print(f"Warning: Could not find district code for '{current_district_name}' (Constituency: {constituency_name_for_lookup})")
            else:
                print(f"Warning: Could not find constituency code for '{constituency_name_for_lookup}' in district '{current_district_name}'")

# Write data to JSON files
output_dir = "C:\\Users\\lacso\\Git\\mw-presidential-election-stats\\2019\\demographics"
os.makedirs(output_dir, exist_ok=True)

for district_code, data in demographics_data.items():
    file_path = os.path.join(output_dir, f"{district_code}_STATS.json")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

print("Demographics data extraction complete.")
