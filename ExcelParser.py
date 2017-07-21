import datetime
import json

import xlrd
import re

workbook = xlrd.open_workbook('ExcelData.xlsx')
worksheet = workbook.sheet_by_index(2)


# Seperates out the data into word and word confidence, returns dictionary
def cell_parse(given_cell):
    given_cell = str(given_cell).replace(",:", ":")
    given_cell = given_cell.replace("\u0000", "")
    given_cell = given_cell.replace("\\u0000", "")
    given_cell = given_cell.replace("\\", "")
    cell_words = []
    if str(given_cell).__contains__('},'):
        given_cell = str(given_cell).split('},')
        for word_and_confidence in given_cell:
            word_and_confidence = word_and_confidence[1:]
            word_and_confidence = word_and_confidence.split(":")
            if word_and_confidence[0].__contains__('"'):
                word_and_confidence[0] = word_and_confidence[0][1:-1]
            word = {word_and_confidence[0]: word_and_confidence[1]}
            cell_words.append(word)
    else:
        if not given_cell == '0':
            given_cell = given_cell[1:].split(":")
            if given_cell[0].__contains__('"'):
                given_cell[0] = given_cell[0].replace('"', "")
            word = {given_cell[0]: given_cell[1]}
            cell_words.append(word)
    return cell_words


# Parse all string data to conversation format, makes easier to view
def create_conversation_transcript(conversation_dict):
    temp_conversation = ["Start"] + [""] * (len(worksheet.col(0)) - 1)
    j = 1
    for i in range(1, len(worksheet.col(0))):
        conversation_dict[i]['content'] = cell_parse(conversation_dict[i]['content'])
        temp_string = ""
        for word in conversation_dict[i]['content']:
            for key, value in word.items():
                if not key == "":
                    temp_string += key + " "
                if key == "":
                    continue
        temp_string = str(conversation_dict[i]['userId']) + ": " + temp_string
        if temp_string[0] == temp_conversation[j - 1][0]:
            temp_conversation[j - 1] += "\n\t" + temp_string[2:]
            continue
        if len(temp_string) > 0:
            temp_conversation[j] = temp_string
        j += 1
    for line in temp_conversation.copy():
        if len(line) == 0:
            temp_conversation.remove(line)
    return temp_conversation


# Return an array containing all the userIDs
def get_users():
    user_list = [phrase_dict[1]['userId']]
    for i in range(1, len(phrase_dict)):
        if user_list.__contains__(phrase_dict[i]['userId']):
            continue
        else:
            user_list.append(phrase_dict[i]['userId'])
    return user_list


def user_info(user):
    user_info_dict = {
        'total_words': 0,
        'total_messages': 0,
        'total_duration': 0,
        'total_words_above_75per': 0,
        'total_words_below_75per': 0,
        'total_words_to_message_ratio': 0,
        'average_wpm_total': 0
    }
    for i in range(20, len(phrase_dict)+1):
        if phrase_dict[i]['userId'] == user:
            #print(phrase_dict[i]['total_words_spoken'])
            user_info_dict['total_words'] += phrase_dict[i]['total_words_spoken']
            user_info_dict['total_messages'] += 1
            user_info_dict['total_duration'] += phrase_dict[i]['duration']
            user_info_dict['total_words_above_75per'] += phrase_dict[i]['words_above_75%_accuracy']
            user_info_dict['total_words_below_75per'] += phrase_dict[i]['words_below_75%_accuracy']
            user_info_dict['total_words_to_message_ratio'] += phrase_dict[i]['words_above_75%_accuracy']
            user_info_dict['average_wpm_total'] = (
            60 * user_info_dict['total_words'] / user_info_dict['total_duration'])
    return user_info_dict


def excel_time_to_python_time(date):
    pytime = datetime.timedelta(days=date)
    pytime = re.findall(r'(([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])', str(pytime))
    return pytime[0][0]


def parse(cell_string):
    # parse out all the excel formatting
    cell_string = cell_string.replace(re.findall(r'^(.*?)\:', cell_string)[0], "")[1:]
    if cell_string.startswith("'") and cell_string.endswith("'"):
        cell_string = cell_string[1:-1]
    if len(cell_string) == 0:
        return 0
    return cell_string


phrase_dict = {}
for i in range(1, len(worksheet.col(0))):
    content = parse(str(worksheet.cell(i, 1)))
    duration = float(parse(str(worksheet.cell(i, 2))))
    id_ = int(float(parse(str(worksheet.cell(i, 3)))))
    posted_at = str(excel_time_to_python_time(float(parse(str(worksheet.cell(i, 4))))))
    roomId = int(float(parse(str(worksheet.cell(i, 5)))))
    userId = int(float(parse(str(worksheet.cell(i, 6)))))
    total_words_spoken = int(float(parse(str(worksheet.cell(i, 7)))))
    words_below_75per_accuracy = int(float(parse(str(worksheet.cell(i, 8)))))
    words_above_75per_accuracy = int(float(parse(str(worksheet.cell(i, 9)))))
    total_words_per_minute = float(parse(str(worksheet.cell(i, 10))))
    words_below_75per_accuracy_per_minute = float(parse(str(worksheet.cell(i, 11))))
    words_above_75per_accuracy_per_minute = float(parse(str(worksheet.cell(i, 12))))

    cell = {
        'content': content,
        'duration': duration,
        'id': id_,
        'posted_at': posted_at,
        'roomId': roomId,
        'userId': userId,
        'total_words_spoken': total_words_spoken,
        'words_below_75%_accuracy': words_below_75per_accuracy,
        'words_above_75%_accuracy': words_above_75per_accuracy,
        'total_words_per_minute': total_words_per_minute,
        'words_below_75%_accuracy_per_minute': words_below_75per_accuracy_per_minute,
        'words_above_75%_accuracy_per_minute': words_below_75per_accuracy_per_minute
    }
    phrase_dict[i] = cell

conversation = create_conversation_transcript(phrase_dict)

# for line in conversation:
#     if line.__contains__("*"):
#         print(line)

users = get_users()

#print(json.dumps(user_info(users[1]), sort_keys=True, indent=4, separators=(',', ': ')))

# print(json.dumps(phrase_dict, sort_keys=True, indent=4, separators=(',', ': ')))
