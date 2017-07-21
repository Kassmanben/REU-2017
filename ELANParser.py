import pympi, re, datetime, json, xlrd, re, pickle

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# All of this needs to be entered correctly before starting the processing
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
#  Get these values from the IBM transcript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
instructor_id = '0'
hearing_participant_1_IBM = '1'
hearing_participant_2_IBM = '-1'

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
#  Get these from the app transcript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
dhh_participant_app = '2'
hearing_participant_1_app = '3'
hearing_participant_2_app = '-1'

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# The first time that someone speaks into the app. Required so that we can sync up the
# timestamps from the app to the timestamps from the IBM transcript. See correct_app_time for more info
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
start_time = "00:41"

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Self explanatory
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
trial_num = 3
trial_date = '06_27_17'
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
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
                    temp_string = "(" + convert_seconds_to_ms(times[0]) + ", " + convert_seconds_to_ms(
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
# App data takes time in relative to the date, spits out something like "June 26, 2017 17:24:30"
# This takes in the start_time (first time that someone speaks into the app) and syncs up the
# timestamps from the app to that of the video (sometimes you need to fiddle with the start_time
# just check the ELAN file ("Dictating into app" tiers will be off if the start time is incorrect)
# Line the "Dictating into app" tiers up with the "Every word spoken" tier
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def correct_app_time(sd):
    # first time that hearing participant speak, match times up with
    for i in range(2, len(worksheet.col(0))):
        if int(float(parse(str(worksheet.cell(i, 6))))) == int(hearing_participant_1_app) or int(
                float(parse(str(worksheet.cell(i, 6))))) == int(hearing_participant_2_app):
            t_h0 = float(parse(str(worksheet.cell(i, 4)))) - (float(parse(str(worksheet.cell(i, 2)))) / 86400)
            t_h0 = convert_hms_to_milliseconds(excel_time_to_python_time(t_h0))
            break
    eq_t_h0 = convert_ms_to_milliseconds(start_time)
    translation[0] = t_h0 - eq_t_h0


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
# Combines the error checked IBM transcript made by the researchers and the timestamp data from
# the raw IBM data. Adds to tiers "Label every word spoken". Returns a corrected version of the
# IBM transcript. Takes in raw IBM transcript and the error checked IBM transcript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def correct_IBM_to_error_checked(IBM_trans, complete_t):
    k = 0
    for i in range(0, len(IBM_trans)):
        IBM_trans[i][2] = complete_t[i]
        if complete_t[i][0] == instructor_id:
            continue
        if complete_t[i][0] == "(":
            time_1 = convert_ms_to_milliseconds(complete_t[i][1:6])
            time_2 = convert_ms_to_milliseconds(complete_t[i][8:13])
            if time_1 == time_2:
                time_2 += 1
            if complete_t[i][14] == instructor_id:
                continue
            if complete_t[i][14] == hearing_participant_1_IBM:
                elan_obj.add_annotation('B2-P2 Label Every Word Spoken', time_1,
                                        time_2, complete_t[i][17:])
            if complete_t[i][14] == hearing_participant_2_IBM:
                elan_obj.add_annotation('B3-P3 Label Every Word Spoken', time_1,
                                        time_2, complete_t[i][17:])
        new_t_list = complete_t[i][3:].split(" ")
        for j in range(0, len(new_t_list)):
            try:
                if new_t_list[j] != IBM_trans[k][0][j][0]:
                    IBM_trans[i][0][j][0] = new_t_list[j]
                    IBM_trans[i][1][j][0] = new_t_list[j]
            except IndexError:
                try:
                    IBM_trans[i][0][-1:][0][0] += " " + str(new_t_list[j])
                    IBM_trans[i][1][-1:][0][0] += " " + str(new_t_list[j])
                except IndexError:
                    IBM_trans[i][0][j][0] = ""
                    IBM_trans[i][1][j][0] = ""
    return IBM_trans

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Adds transcript annotations to the "Label Every Word Spoken" tier
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def add_transcription_to_annotation(transcription_list, identity):
    for caption in transcription_list:
        if identity == instructor_id:
            continue
        if identity == hearing_participant_1_IBM:
            elan_obj.add_annotation('B2-P2 Label Every Word Spoken', int(float(caption[1] * 1000)),
                                    int(float(caption[2] * 1000)), caption[0])
        if identity == hearing_participant_2_IBM:
            elan_obj.add_annotation('B3-P3 Label Every Word Spoken', int(float(caption[1] * 1000)),
                                    int(float(caption[2] * 1000)), caption[0])


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Adds marked up annotations to the "Words Marked Up" tier (markup value set at 750/1000 (75%))
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def add_marked_up_words(transcription_list, posted_time, duration_time, identity):
    for i in range(0, len(transcription_list)):
        conf = int(float(list(transcription_list[i].items())[0][1].replace("}", "").strip()))
        times = relative_excel_time_to_hmsms(posted_time, duration_time)
        if conf < 750 and (
                        str(identity) == hearing_participant_1_app or str(identity) == hearing_participant_2_app):
            elan_obj.add_annotation('G-Words Marked Up', convert_hms_to_milliseconds(times[0]),
                                    convert_hms_to_milliseconds(times[1]), list(transcription_list[i].items())[0][0])

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Adds dictation and typing period annotations to the "Dictating into App" and "Typing into App" tiers
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def add_dictation_typing_periods_to_annotation():
    for key in phrase_dict.keys():
        typed = True
        for confidence_levels in phrase_dict[key]['content']:
            for confidence_value in confidence_levels.values():
                value = int(float(confidence_value.strip().replace("}", "")))
                if value != 1000:
                    typed = False
        if str(phrase_dict[key]['userId']) == dhh_participant_app:
            user_id = '1'
        elif str(phrase_dict[key]['userId']) == hearing_participant_1_app:
            user_id = '2'
        elif str(phrase_dict[key]['userId']) == hearing_participant_2_app:
            user_id = '3'
        if typed:
            times = relative_excel_time_to_hmsms(phrase_dict[key]['posted_at'], phrase_dict[key]['duration'])
            elan_obj.add_annotation("H" + str(user_id) + "-P" + str(user_id) + " Typing Into App",
                                    convert_hms_to_milliseconds(times[0]),
                                    convert_hms_to_milliseconds(times[1]), "P" + str(user_id))
        if not typed:
            times = relative_excel_time_to_hmsms(phrase_dict[key]['posted_at'], phrase_dict[key]['duration'])
            elan_obj.add_annotation("C" + str(user_id) + "-P" + str(user_id) + " Dictating Into App",
                                    convert_hms_to_milliseconds(times[0]),
                                    convert_hms_to_milliseconds(times[1]), "P" + str(user_id))


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Adds error markup annotations to the "Typed Error", "Dication Error" tiers
# Also adds to the "Typing to Fix Dictated Error", "Uses Dictation to Fix Error" "Typing to Fix Typed Error"
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def mark_dictated_typed_errors(marked_up_line, line_num):
    conversation_line = []
    for word_key in phrase_dict[line_num]['content']:
        for word in word_key.keys():
            if len(word) > 0 and not word.__contains__(" "):
                conversation_line.append(word)
            if word.__contains__(" "):
                for subword in word.split(" "):
                    conversation_line.append(subword)
    typed = True
    for confidence_levels in phrase_dict[line_num]['content']:
        for confidence_value in confidence_levels.values():
            value = int(float(confidence_value.strip().replace("}", "")))
            if value != 1000:
                typed = False

    error_id = str(phrase_dict[line_num]['userId'])
    if error_id == dhh_participant_app:
        error_id = '1'
    elif error_id == hearing_participant_1_app:
        error_id = '2'
    elif error_id == hearing_participant_2_app:
        error_id = '3'
    times = relative_excel_time_to_hmsms(phrase_dict[line_num]['posted_at'], phrase_dict[line_num]['duration'])
    # print(times)
    # print(phrase_dict[line_num]['content'])
    marked_up_line = marked_up_line[3:].split(" ")
    for i in range(0, len(conversation_line)):
        if conversation_line[i] != marked_up_line[i]:
            if marked_up_line[i][0] == "*":
                if typed:
                    elan_obj.add_annotation("I" + str(error_id) + "-P" + str(error_id) + " Typed Error",
                                            convert_hms_to_milliseconds(times[0]),
                                            convert_hms_to_milliseconds(times[1]), "P" + str(error_id))
                if not typed:
                    elan_obj.add_annotation("D" + str(error_id) + "-P" + str(error_id) + " Dictation Error",
                                            convert_hms_to_milliseconds(times[0]),
                                            convert_hms_to_milliseconds(times[1]), "P" + str(error_id))
            if marked_up_line[i][:2] == "d#":
                if typed:
                    elan_obj.add_annotation(
                        "F" + str(error_id) + "-P" + str(error_id) + " Typing to Fix Dictated Error",
                        convert_hms_to_milliseconds(times[0]),
                        convert_hms_to_milliseconds(times[1]), "P" + str(error_id))
                if not typed:
                    elan_obj.add_annotation("E" + str(error_id) + "-P" + str(error_id) + " Uses Dictation to Fix Error",
                                            convert_hms_to_milliseconds(times[0]),
                                            convert_hms_to_milliseconds(times[1]), "P" + str(error_id))
            if marked_up_line[i][:2] == "t#":
                elan_obj.add_annotation("J" + str(error_id) + "-P" + str(error_id) + " Typing to Fix Typed Error",
                                        convert_hms_to_milliseconds(times[0]),
                                        convert_hms_to_milliseconds(times[1]), "P" + str(error_id))


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


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Clears lines that are automatically filled so that no old annotations stay on.
# Doesn't clear any of the hand-entered annotations
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def clear_dictated_lines():
    for tier in ["B1-P1 Label Every Word Spoken", "B2-P2 Label Every Word Spoken", 'B3-P3 Label Every Word Spoken',
                 'C1-P1 Dictating Into App', 'C2-P2 Dictating Into App', 'C3-P3 Dictating Into App',
                 'D1-P1 Dictation Error', 'D2-P2 Dictation Error', 'D3-P3 Dictation Error',
                 'E1-P1 Uses Dictation to Fix Error', 'E2-P2 Uses Dictation to Fix Error',
                 'E3-P3 Uses Dictation to Fix Error',
                 'F1-P1 Typing to Fix Dictated Error', 'F2-P2 Typing to Fix Dictated Error',
                 'F3-P3 Typing to Fix Dictated Error',
                 'G-Words Marked Up', 'H1-P1 Typing Into App', 'H2-P2 Typing Into App', 'H3-P3 Typing Into App',
                 'I1-P1 Typed Error', 'I2-P2 Typed Error', 'I3-P3 Typed Error', 'J1-P1 Typing to Fix Typed Error',
                 'J2-P2 Typing to Fix Typed Error', 'J3-P3 Typing to Fix Typed Error']:
        elan_obj.remove_all_annotations_from_tier(tier)


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

# with open("Trial_" + str(trial_num) +"_"+ str(trial_date) + '/Trial_' + str(trial_num) + '_IBM_Transcript.pkl',
#           'rb') as handle:
#     transcript = pickle.load(handle)

# with open("Trial_" + str(trial_num) +"_"+ str(trial_date) + '/Trial_' + str(
#         trial_num) + '_IBM_Speaker_Data.pkl', 'rb') as handle:
#     speaker_data = pickle.load(handle)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Loads "complete transcript" (the error checked IBM transcript created by the researchers)
# NOTE: Have this commented out when you run this code the first time
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

# with open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(
#         trial_num) + '_Complete_Transcript.txt', 'r') as handle:
#     complete_transcript = handle.readlines()

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Loads "error markup" (the error markup-ed app transcript created by the researchers)
# NOTE: Have this commented out when you run this code the first time
# ///////////////////////////////////////////////////////////////////////////////////////////////////////


# with open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(
#         trial_num) + '_Error_Markup.txt', 'r') as handle:
#     checked_app_transcript = handle.readlines()

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
# This will be the file that the researchers make corrections to to get the final tanscript
# WARNING: Only have this uncommented the first time the code is run, so that the IBM transcript is created
# Comment it out immediately afterwards so you don't accidentally overwrite the corrected IBM Trancscript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////


# e = "Instructor # = " + instructor_id + "\nHearing Participant 1 #= " + hearing_participant_1_IBM + "\nHearing Participant 2 #= " + hearing_participant_2_IBM + "\n"
# for line in IBM_conversation:
#     e += line + "\n "
#
# f = open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(trial_num) + '_Complete_Transcript.txt', 'w')
# f.write(e)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# This creates the initial "Error Markup" file from the raw app data
# This will be the file that the researchers make corrections to to get the error markup data
# WARNING: Only have this uncommented the first time the code is run, so that the IBM transcript is created
# Comment it out immediately afterwards so you don't accidentally overwrite the corrected IBM Trancscript
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

# e = "Deaf/ Hard of Hearing Participant # = " + dhh_participant_app + "\nHearing Participant 1 #= " + hearing_participant_1_app + "\nHearing Participant 2 #= " + hearing_participant_2_app + "\n"
# for line in app_conversation:
#     e += line + "\n "
#
# f = open("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_' + str(trial_num) + '_Error_Markup.txt', 'w')
# f.write(e)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes the IBM completed transcript in and parses out the timestamps and first 4 lines of information
# Have this commented out when you run this code the first time
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

# complete_transcript = complete_transcript[4:]
# complete_speaker_data = []
# i = 0
# for c in complete_transcript.copy():
#     complete_transcript.remove(c)
#     c = c.replace("\n", "")
#     c = c.replace("\t", "")
#     c = c.strip()
#     timestamps = re.findall(r'(...:.., ..:...)', c)
#     if len(timestamps) > 0:
#         if timestamps[0] in time_list:
#             c = c.replace(timestamps[0], "")
#             timestamps = timestamps[0][1:-1].split(",")
#     if len(c) > 0:
#         complete_transcript.insert(i, c)
#         complete_speaker_data.insert(i, timestamps)
#         i += 1


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Loads ELAN file as an ELAN object
# Use MasterTemplateFinal if starting new annotation,
# otherwise load pre-processed file with hand-entered annotations
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

#elan_file = "MasterTemplateFinal.etf"
elan_file = "Trial_" + str(trial_num) + "_" + str(trial_date) + '/Trial_'+ str(trial_num) +".eaf"
elan_obj = pympi.Eaf(elan_file)
pympi.Elan.parse_eaf(elan_file, elan_obj)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Make sure the lines are clear and fix the timestamps to the correct time
# Convert the IBM transcript to the error-checked version
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

clear_dictated_lines()
correct_app_time(complete_speaker_data)
transcript = correct_IBM_to_error_checked(transcript, complete_transcript)

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Fill in tiers, starting with Dictated/Typed errors and Corrections
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
for i in range(1, len(app_conversation)):
    mark_dictated_typed_errors(checked_app_transcript[3:][i].strip(), i)

add_dictation_typing_periods_to_annotation()
for t in transcript:
    add_transcription_to_annotation(t[1],t[2][0])

for p in phrase_dict.keys():
    add_marked_up_words(phrase_dict[p]['content'],phrase_dict[p]['posted_at'],phrase_dict[p]['duration'],phrase_dict[p]['userId'])

# //////////////////////////////////////////////////////////////////////////////////////////////////////
# Load all annotations into an easy-to-display list
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
all_annotations = get_all_annotations(sorted(list(elan_obj.get_tier_names())))
print(*all_annotations, sep="\n")

# //////////////////////////////////////////////////////////////////////////////////////////////////////
# Write ELAN file with added annotations to file
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
elan_obj.to_file("Trial_" + str(trial_num) + "_" + str(trial_date) + '/Vid' + str(
    trial_num) + '.eaf')



# prints error data for easier data entry
# for i in range(1, len(app_conversation)):
#     output_errors(checked_app_transcript[3:][i].strip(), i)
