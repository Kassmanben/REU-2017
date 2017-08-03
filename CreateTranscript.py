import pympi, re, datetime, json, xlrd, re, pickle

# All of this needs to be entered correctly before starting the processing

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Self explanatory
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
trial_num = 3
trial_date = '06_27_17'

# ///////////////////////////////////////////////////////////////////////////////////////////////////////


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Don't need to enter any values here
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
translation = [0]


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Prints JSON data nicely
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def pretty_print_json(json_data):
    print(json.dumps(json_data, sort_keys=True, indent=4, separators=(',', ': ')))


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Return an array containing all the userIDs (Unused in this code but could be useful in future)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def get_users():
    user_list = [phrase_dict[1]['userId']]
    for i in range(1, len(phrase_dict)):
        if user_list.__contains__(phrase_dict[i]['userId']):
            continue
        else:
            user_list.append(phrase_dict[i]['userId'])
    return user_list


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# (Unused in this code but could be useful in future)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
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
    for i in range(20, len(phrase_dict) + 1):
        if phrase_dict[i]['userId'] == user:
            # print(phrase_dict[i]['total_words_spoken'])
            user_info_dict['total_words'] += phrase_dict[i]['total_words_spoken']
            user_info_dict['total_messages'] += 1
            user_info_dict['total_duration'] += phrase_dict[i]['duration']
            user_info_dict['total_words_above_75per'] += phrase_dict[i]['words_above_75%_accuracy']
            user_info_dict['total_words_below_75per'] += phrase_dict[i]['words_below_75%_accuracy']
            user_info_dict['total_words_to_message_ratio'] += phrase_dict[i]['words_above_75%_accuracy']
            user_info_dict['average_wpm_total'] = (
                60 * user_info_dict['total_words'] / user_info_dict['total_duration'])
    return user_info_dict


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Creates parent and child tiers (Unused in this code but could be useful in future)
# WARNING: This will not alter the time codes for annotations, so if annotation times fall outside the linguistic
# type, they will cause errors. This method is only meant to alter templates easily, with the option to copy the
# annotations so no data is lost
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def change_parent_child_tiers(parent_tier_id, child_tier_id, linguistic_type="default-lt"):
    temp_annotation = elan_obj.get_annotation_data_for_tier(child_tier_id)
    elan_obj.remove_tier(child_tier_id)
    elan_obj.add_tier(child_tier_id, linguistic_type, parent_tier_id)
    for t in temp_annotation:
        if type(t) is str:
            continue
        elan_obj.add_annotation(child_tier_id, t[0], t[1], t[2])


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Seperates out the data into word and word confidence,
# returns dictionary with word as key, confidence as value
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
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


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes IBM transcript and creates a rough transcription, divided by the speaker.
# This transcript will need to be corrected by the researchers since the IBM transcription isn't perfect
# Lines are presented (timestamp1, timestamp2)  speaker_id: "This is there the speaker's words are"
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def create_conversation_transcript_IBM(IBM_transcript, IBM_speaker_data):
    time_ranges = {}
    for speaker_list in IBM_speaker_data:
        try:
            if time_ranges[speaker_list[0]][-1][1] == speaker_list[1]:
                time_ranges[speaker_list[0]][-1][1] = speaker_list[2]
            else:
                time_ranges[speaker_list[0]].append([speaker_list[1], speaker_list[2], speaker_list[3]])
        except KeyError:
            time_ranges[speaker_list[0]] = ([[speaker_list[1], speaker_list[2], speaker_list[3]]])
    temp_conversation = ["Start"] + [""] * (len(IBM_transcript))
    j = 1
    for t in IBM_transcript:
        start_time = t[1][0][1]
        for ids in time_ranges.keys():
            for times in time_ranges[ids]:
                if start_time >= times[0] and start_time <= times[1]:
                    temp_string = "(" + convert_seconds_to_minsec(times[0]) + ", " + convert_seconds_to_minsec(
                        times[1]) + ")\t\t" + str(ids) + ": " + str(t[-1])
                    if len(temp_string[0]) > 0:
                        temp_conversation[j] = temp_string
        j += 1
    return temp_conversation


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Parse all string data from the app to conversation format, makes easier to view
# Appears roughly the same as the IBM transcript (though without timestamps)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def create_conversation_transcript_messages(conversation_dict):
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
        if len(temp_string) > 0:
            temp_conversation[j] = temp_string
        j += 1
    for line in temp_conversation.copy():
        if len(line) == 0:
            temp_conversation.remove(line)
    return temp_conversation


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Fixes all the parsing errors that come with turning an excel doc into a dictionary
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def parse(cell_string):
    # parse out all the excel formatting
    cell_string = cell_string.replace(re.findall(r'^(.*?)\:', cell_string)[0], "")[1:]
    if cell_string.startswith("'") and cell_string.endswith("'"):
        cell_string = cell_string[1:-1]
    if len(cell_string) == 0:
        return 0
    return cell_string


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Ah yes...the time conversion suite of functions. Basically there is data coming in in a ton of
# different formats (milliseconds, excel time, date and time, hour:minute:second, minute:second, etc...)
# These are all just here to make it easier to convert back and forth to get it into the forms used
# by the program which are milliseconds (relative to the beginning of the video)
# and hour:minute:second:millisecond (again, relative to the beginning of the video)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////



# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Excel has their dates stored in a proprietary format. This corrects it to a simple Python time
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def excel_time_to_python_time(date):
    pytime = datetime.timedelta(days=date)
    pytime = re.findall(r'(([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9])', str(pytime))
    return pytime[0][0]


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in integer value of seconds, converts to string "minutes:seconds"
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def convert_seconds_to_minsec(seconds):
    second_num = int(seconds % 60)
    minutes = int(seconds // 60)

    if len(str(second_num)) == 1:
        second_num = str('0' + str(second_num))
    if len(str(minutes)) == 1:
        minutes = str('0' + str(minutes))
    return str(minutes) + ":" + str(second_num)


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in integer value of milliseconds, converts to string "hours:minutes:seconds:milliseconds"
# NOTE: if this takes in any negative values it converts the time to "00:00:00:0000"
# (sometimes the app time to relative time conversion can spit out values like -59:-59:-59:9842
# when all it means is 00:00:00:0000
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def convert_milliseconds_to_hmsms(milliseconds):
    temp_int = milliseconds // 1000
    seconds = temp_int % 60
    if len(str(seconds)) == 1:
        seconds = str('0' + str(seconds))
    else:
        seconds = str(seconds)
    temp_int //= 60
    minutes = temp_int % 60
    if len(str(minutes)) == 1:
        minutes = str('0' + str(minutes))
    else:
        minutes = str(minutes)
    temp_int //= 60
    hours = temp_int % 24
    if len(str(hours)) == 1:
        hours = str('0' + str(hours))
    else:
        hours = str(hours)
    milliseconds -= convert_hms_to_milliseconds(str(hours) + ":" + str(minutes) + ":" + str(seconds) + ":0")
    milliseconds = str(milliseconds)
    if len(str(milliseconds)) == 1:
        milliseconds = str('00' + str(milliseconds))
    elif len(str(milliseconds)) == 2:
        milliseconds = str('0' + str(milliseconds))
    else:
        milliseconds = str(milliseconds)

    if hours.__contains__("-") or minutes.__contains__("-") or seconds.__contains__("-") or milliseconds.__contains__(
            "-"):
        hours = minutes = seconds = milliseconds = "00"
    return "{}:{}:{}:{}".format(hours, minutes, seconds, milliseconds)


# # ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in a string "hh:mm:ss", converts to int milliseconds
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def convert_hms_to_milliseconds(str_hms):
    str_hms = str_hms.split(":")
    hours = int(str_hms[0])
    minutes = int(str_hms[1])
    seconds = int(str_hms[2])
    if len(str_hms) == 4:
        milliseconds = hours * 3600000 + minutes * 60000 + seconds * 1000 + int(str_hms[3])
    else:
        milliseconds = hours * 3600000 + minutes * 60000 + seconds * 1000
    return milliseconds


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in a string "mm:ss", converts to int milliseconds
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def convert_minsec_to_milliseconds(str_hms):
    str_hms = str_hms.split(":")
    minutes = int(str_hms[0])
    seconds = int(str_hms[1])
    milliseconds = minutes * 60000 + seconds * 1000
    return milliseconds

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# See correct_app_time() for full description. This takes time from excel and gets it into the app time format
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def relative_excel_time_to_hmsms(excel_time, key_duration):
    time_1 = convert_hms_to_milliseconds(excel_time) - int(key_duration * 1000) - translation[0]
    time_2 = convert_hms_to_milliseconds(excel_time) - translation[0]
    delta = time_2 - time_1
    if delta == 0:
        time_2 += 1
    time_1 = convert_milliseconds_to_hmsms(time_1)
    time_2 = convert_milliseconds_to_hmsms(time_2)
    if time_1 == time_2:
        time_2 = convert_milliseconds_to_hmsms(convert_hms_to_milliseconds(time_2) + 1)
    return (time_1, time_2)


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Returns a list of all tiers, with their relevant annotations and timestamps
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def get_all_annotations(annotations):
    full_annotation_list = []
    for tier in annotations:
        time_tuple = elan_obj.get_full_time_interval()
        annotation_list = list(elan_obj.get_annotation_data_between_times(tier, time_tuple[0], time_tuple[1]))
        templist = []
        for annotation in annotation_list:
            converted_tuple = list(annotation)
            converted_tuple[0] = convert_milliseconds_to_hmsms(converted_tuple[0])
            converted_tuple[1] = convert_milliseconds_to_hmsms(converted_tuple[1])
            templist.append(converted_tuple)
        annotation_list = [x for x in templist]
        annotation_list.insert(0, tier)
        full_annotation_list.append(annotation_list)
    return full_annotation_list


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Returns the length of the annotation
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def get_annotation_length(annotation):
    time1 = convert_hms_to_milliseconds(annotation[0])
    time2 = convert_hms_to_milliseconds(annotation[1])
    delta_t = convert_milliseconds_to_hmsms(time2 - time1)
    return delta_t

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Prints error words next to their confidence values (Created to help entry into the Error Data table)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def output_errors(marked_up_line, line_num):
    conversation_line = []
    for word_key in phrase_dict[line_num]['content']:
        for word in word_key.keys():
            if len(word) > 0:
                value = word_key[word].replace("}", "")
                conversation_line.append((word, value))

    marked_up_line = marked_up_line[3:].split(" ")

    for i in range(0, len(conversation_line)):
        if conversation_line[i][0] != marked_up_line[i]:
            if marked_up_line[i][0] == "*":
                print(str(marked_up_line[i]))
                print(conversation_line[i][1])
                print()
                error_list.append(marked_up_line[i] + str(conversation_line[i][1]))
            if marked_up_line[i][:2] == "d#":
                print(str(marked_up_line[i]))
                print(conversation_line[i][1])
                print()
                correction_list.append(marked_up_line[i] + str(conversation_line[i][1]))

error_list = []
correction_list = []

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in excel data from app
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
workbook = xlrd.open_workbook(
    "Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(trial_num) + "_" + str(
        trial_date) + '.xlsx')
worksheet = workbook.sheet_by_index(0)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Creates a nested dictionary with each entry indexed by line_number, then filled in as the excel table was
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
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

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Loads IBM trancsript and speaker data
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

with open("Trial_" + str(trial_num) +"_"+ str(trial_date) + '/Trial_' + str(trial_num) + '_IBM_Transcript.pkl',
          'rb') as handle:
    transcript = pickle.load(handle)

with open("Trial_" + str(trial_num) +"_"+ str(trial_date) + '/Trial_' + str(
        trial_num) + '_IBM_Speaker_Data.pkl', 'rb') as handle:
    speaker_data = pickle.load(handle)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
## Creates IBM transcript (this is created from the raw data so there will be errors until you process
## it through the correct_IBM_to_error_checked() function
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
IBM_conversation = create_conversation_transcript_IBM(transcript, speaker_data)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
## Creates app transcript from raw data
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
app_conversation = create_conversation_transcript_messages(phrase_dict)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
## Creates a list of timestamps from the original IBM transcript
## This is very important if the IBM trancsript didn't catch a phrase, and the researchers had to manually
## add a timestamped line to the error-checked transcript. This list will be used to compare against the original
## timestamps and enter the new line at the correct location
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

time_list = []
for m in range(1, len(IBM_conversation)):
    time_list.append(IBM_conversation[m][:14])

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# This creates the initial "Complete IBM Transcript" file from the raw IBM data
# This will be the file that the researchers make corrections to to get the final transcript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////


e = "Instructor # = 0\nHearing Participant 1 #= 1\nHearing Participant 2 #= 2\n"
for line in IBM_conversation:
    e += line + "\n "

f = open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(trial_num) + '_Complete_Transcript.txt', 'w')
f.write(e)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# This creates the initial "Error Markup" file from the raw app data
# This will be the file that the researchers make corrections to to get the error markup data
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

e = "Deaf/ Hard of Hearing Participant # = 1\nHearing Participant 1 #= 2\nHearing Participant 2 #= 3\n"
for line in app_conversation:
    e += line + "\n "

f = open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(trial_num) + '_Error_Markup.txt', 'w')
f.write(e)
