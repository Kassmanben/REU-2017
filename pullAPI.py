import requests
import pandas as pd
import numpy as np
import json
from pandas.io.json import json_normalize


def pretty_print_json(json_data):
    print(json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': ')))

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Enter these in before starting. You'll need to create a folder with the name "Trial_#_date" before pulling
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
trial_date = '07_07_17'
trial_number = '9'

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# API URL shouldn't change but if it does, you can change it here.
# The access token may or may not still be linked
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

response = requests.get("http://129.21.53.47:3000/api/messages?access_token=ASRM33t!")
results = response.json()

json_data = json_normalize(results)
print(json_data)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# These lines are just for printing the conversation out with ease while the experiment is running
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

for c in json_data["content"]:
    exclude=["{","}",":",",",'"',"1","2","3","4","5","6","7","8","9","0"]
    c.replace("}"," ")
    c.replace(","," ")
    t_str = ""
    for letter in c:
        if letter not in exclude:
            t_str+=letter
        if letter == "}":
            t_str+=" "
    print(t_str)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Parses the data into a reasonable format
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

json_data["duration"] = json_data["duration"].astype('float64')

json_data['posted_at'] = json_data['posted_at'].apply(pd.to_datetime)

content = []
for i in json_data['content']:
    i = i.replace("/", "")
    i = i.replace('"', "")
    content.append(i)

num_words = []
num_words_below_75 = []
num_words_above_75 = []
for i in content:
    words = i.split(",")
    # Counts total number of words spoken
    count1 = 0
    # Counts words above 75 %
    count2 = 0
    # Counts words below 75 %
    count3 = 0
    for word in words:
        word = word.replace("{", "")
        word = word.replace("}", "")
        count1 += 1

        if len(word.split(":")) > 1:
            try:
                confidence = int(word.split(":")[1])
                if confidence >= 750:
                    count2 += 1
                else:
                    count3 += 1
            except ValueError:
                confidence = 0

    num_words.append(count1)
    num_words_below_75.append(count3)
    num_words_above_75.append(count2)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Creates json file with app data, saves as .json and as .csv.
# csv file will need to be converted to .xlsx file for ELANparser.py program
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

json_data['total_words_spoken'] = num_words
json_data['words_below_75%_accuracy'] = num_words_below_75
json_data['words_above_75%_accuracy'] = num_words_above_75
json_data['Total_Words_Per_Minute'] = (json_data['total_words_spoken'] / (json_data["duration"] / 60)).replace(
    [np.inf, -np.inf], np.nan).fillna(0.0)
json_data['Words_below_75%_Per_Minute'] = (
json_data['words_below_75%_accuracy'] / (json_data["duration"] / 60)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
json_data['Words_above_75%_Per_Minute'] = (
json_data['words_above_75%_accuracy'] / (json_data["duration"] / 60)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
json_data = json_data[1:]

json_data.to_csv("Trial_"+trial_number+"_"+trial_date+'/Trial_'+trial_number+"_"+trial_date+".csv")

with open("Trial_"+trial_number+"_"+trial_date+'/Trial_'+trial_number+"_"+trial_date+'.json', 'w') as output:
    json_data.to_json(output)


