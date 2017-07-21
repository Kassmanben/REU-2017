from collections import Counter
import nltk

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Takes in a word as a string, converts to arpabet pronounciation (returns [[pronounciation1],...])
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
def arpabet_word(word):
    try:
        return arpabet[word.lower()]
    except KeyError:
        if word == "%HESITATION":
            return [["Filler"]]
        if word == "%OMISSION":
            return [[""]]
        else:
            return [["No arpabet available"]]


arpabet = nltk.corpus.cmudict.dict()

f = open("Error_Wordlist.txt", mode="r")
g = open("Correct_Wordlist.txt", mode="r")
error_wordlist = f.readlines()
correct_wordlist = g.readlines()

error_wordlist = list(map(lambda x: x.replace("\n", "").strip(), error_wordlist))
correct_wordlist = list(map(lambda x: x.replace("\n", "").strip(), correct_wordlist))

error_wordset = set(error_wordlist)
correct_wordset = set(correct_wordlist)

# print("Words in Error")
# error_wordcount = Counter(error_wordlist)
# print(*error_wordcount.most_common(),sep="\n")
#
# print("\n\n\n\n\n\nCorrect Words")
#
# correct_wordcount = Counter(correct_wordlist)
# print(*correct_wordcount.most_common(),sep="\n")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Creates two lists: err_word and corr_word for each pair of words
# These will be used to compare pronunciation
# The code for corr_word gets convoluted because I needed to account for situations where the word in error
# was actually multiple words with multiple possible pronunciations
# Corr_word may have many options since it is a list of
# all permutations of pronunciations of the correct word(s)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////

pronounciation_error_pairs = []
for i in range(0, len(error_wordlist)):
    err_word = arpabet_word(error_wordlist[i])
    if len(correct_wordlist[i].split(" ")) > 1:
        temp_list = []
        for subword in correct_wordlist[i].split(" "):
            pron = arpabet_word(subword)
            temp_list.append(pron)
        length_correct = 1
        for sub in temp_list:
            length_correct *=len(sub)
        corr_words = [[] for _ in range(length_correct)]
        for sub in temp_list:
            if len(sub) == 1:
                for elem in sub[0]:
                    for alt_pron in corr_words:
                        alt_pron.append(elem)
                    #print(corr_words)
            else:
                length_of_interval = int(len(corr_words)/len(sub))
                start=0
                for k in range(0, len(sub)):
                    for j in range(start,start+length_of_interval):
                        for elem in sub[k]:
                            corr_words[j].append(elem)
                        start += 1
    else:
        corr_words = arpabet_word(correct_wordlist[i])

    pronounciation_error_pairs.append(((error_wordlist[i], err_word), (correct_wordlist[i], corr_words)))

print(*pronounciation_error_pairs, sep="\n\n")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Compares pronunciation of word in error and correct word(s)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
for error_pairs in pronounciation_error_pairs:
    e_pron_list = error_pairs[0][1]
    c_pron_list = error_pairs[1][1]
    # print(e_pron_list,c_pron_list)
    for pron1 in e_pron_list:
        for pron2 in c_pron_list:
            if pron1 == pron2:
                #print(error_pairs[0][0], error_pairs[1][0], "Homophones")
                continue
            delta = abs(len(pron1) - len(pron2))
            # for i in range(0,min(len(pron1,pron2))):
