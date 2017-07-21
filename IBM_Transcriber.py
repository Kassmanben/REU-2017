import json
import pickle
from os.path import join, dirname
from watson_developer_cloud import SpeechToTextV1

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Get these from the Blumix service page. There are not your Bluemix username and password
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
speech_to_text = SpeechToTextV1(
    username='7f202b76-1946-4379-b826-63c9d775908d',
    password='6AY6L7ah4Npy',
    x_watson_learning_opt_out=False
)

print(json.dumps(speech_to_text.models(), indent=2))

print(json.dumps(speech_to_text.get_model('en-US_BroadbandModel'), indent=2))


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Enter this in.
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
trial_number = '9'
trial_date = '07_07_17'


input_file = "Trial_"+trial_number+"_"+trial_date+'/Trial_'+trial_number+"_"+trial_date+'.flac'
output_file = "Trial_"+trial_number+"_"+trial_date+'/Trial_'+trial_number+'_IBM_Transcript.json'


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Sends the .flac file to IBM Watson
# NOTE: The .flac file must be under 100 MB. I use ffmpeg to convert the .mov file to .flac
# then use Audacity to compress the .flac file to under 100 MB
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

with open(join(dirname(__file__), input_file), 'rb') as audio_file:
    data = speech_to_text.recognize(
        audio_file, content_type='audio/flac', timestamps=True,
        word_confidence=True, inactivity_timeout=-1, speaker_labels=True)
    print(json.dumps(data))

with open(output_file, 'w') as output:
    json.dump(data, output)

with open(output_file, 'r') as handle:
    data = json.load(handle)

print(json.dumps(data["speaker_labels"], indent=2))
print(json.dumps(data["results"], indent=2))


# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Creates a list with each line of the transcript represented in a list
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
transcript_list = []
for a in data["results"]:
    word_confidence = a['alternatives'][0]['word_confidence']
    timestamps = a['alternatives'][0]['timestamps']
    transcript = a['alternatives'][0]['transcript']
    transcript_list.append([word_confidence, timestamps, transcript])

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Speaker data is kept in another list with timestamps
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
speaker_data = []
for s in data["speaker_labels"]:
    speaker = s["speaker"]
    first_timestamp = s["from"]
    end_timestamp = s["to"]
    confidence = s["confidence"]
    speaker_data.append([speaker, first_timestamp, end_timestamp, confidence])
    print([speaker, first_timestamp, end_timestamp, confidence])

with open(output_file.replace(".json", ".pkl"), 'wb') as handle:
    pickle.dump(transcript_list, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open(output_file.replace("Transcript.json", "Speaker_Data.pkl"), 'wb') as handle:
    pickle.dump(speaker_data, handle, protocol=pickle.HIGHEST_PROTOCOL)