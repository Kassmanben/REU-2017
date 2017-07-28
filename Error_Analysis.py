from __future__ import division
from __future__ import print_function

from collections import Counter
import pandas as pd
import nltk
import csv



def normalize_for_lev(phone_list):
    new_p_list = []
    for p in phone_list.copy():
        if len(p) == 3:
            p = p[:-1]
        if p == "AA":
            p = "å"
            new_p_list.append(p)
            continue
        if p == "AE":
            p = "æ"
            new_p_list.append(p)
            continue
        if p == "AH":
            p = "á"
            new_p_list.append(p)
            continue
        if p == "AO":
            p = "â"
            new_p_list.append(p)
            continue
        if p == "AW":
            p = "à"
            new_p_list.append(p)
            continue
        if p == "AY":
            p = "ã"
            new_p_list.append(p)
            continue
        if p == "CH":
            p = 'ç'
            new_p_list.append(p)
            continue
        if p == "DH":
            p = "∂"
            new_p_list.append(p)
            continue
        if p == "EH":
            p = "é"
            new_p_list.append(p)
            continue
        if p == "ER":
            p = "ê"
            new_p_list.append(p)
            continue
        if p == "EY":
            p = "è"
            new_p_list.append(p)
            continue
        if p == "HH":
            p = "h"
            new_p_list.append(p)
            continue
        if p == "IH":
            p = "î"
            new_p_list.append(p)
            continue
        if p == "IY":
            p = "ì"
            new_p_list.append(p)
            continue
        if p == "JH":
            p = "j"
            new_p_list.append(p)
            continue
        if p == "NG":
            p = "¬"
            new_p_list.append(p)
            continue
        if p == "OW":
            p = "ø"
            new_p_list.append(p)
            continue
        if p == "OY":
            p = "ó"
            new_p_list.append(p)
            continue
        if p == "SH":
            p = "ß"
            new_p_list.append(p)
            continue
        if p == "TH":
            p = "†"
            new_p_list.append(p)
            continue
        if p == "UH":
            p = "ü"
            new_p_list.append(p)
            continue
        if p == "UW":
            p = "ù"
            new_p_list.append(p)
            continue
        if p == "ZH":
            p = "√"
            new_p_list.append(p)
            continue
        else:
            new_p_list.append(p)
    print(new_p_list)
    return (new_p_list)


def _edit_dist_init(len1, len2):
    lev = []
    for i in range(len1):
        lev.append([0] * len2)  # initialize 2D array to zero
    for i in range(len1):
        lev[i][0] = i  # column 0: 0,1,2,3,4,...
    for j in range(len2):
        lev[0][j] = j  # row 0: 0,1,2,3,4,...
    return lev


def _edit_dist_step(lev, i, j, s1, s2, substitution_cost=1, transpositions=False):
    c1 = s1[i - 1]
    c2 = s2[j - 1]

    # skipping a character in s1
    a = lev[i - 1][j] + 1
    # skipping a character in s2
    b = lev[i][j - 1] + 1
    # substitution
    c = lev[i - 1][j - 1] + (substitution_cost if c1 != c2 else 0)

    # transposition
    d = c + 1  # never picked by default
    if transpositions and i > 1 and j > 1:
        if s1[i - 2] == c2 and s2[j - 2] == c1:
            d = lev[i - 2][j - 2] + 1

    # pick the cheapest
    lev[i][j] = min(a, b, c, d)


def edit_distance(s1, s2, substitution_cost=1, transpositions=False):
    # set up a 2-D array
    len1 = len(s1)
    len2 = len(s2)
    lev = _edit_dist_init(len1 + 1, len2 + 1)

    # iterate over the array
    for i in range(len1):
        for j in range(len2):
            _edit_dist_step(lev, i + 1, j + 1, s1, s2,
                            substitution_cost=substitution_cost, transpositions=transpositions)
    return lev[len1][len2]


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
            length_correct *= len(sub)
        corr_words = [[] for _ in range(length_correct)]
        for sub in temp_list:
            if len(sub) == 1:
                for elem in sub[0]:
                    for alt_pron in corr_words:
                        alt_pron.append(elem)
                        # print(corr_words)
            else:
                length_of_interval = int(len(corr_words) / len(sub))
                start = 0
                for k in range(0, len(sub)):
                    for j in range(start, start + length_of_interval):
                        for elem in sub[k]:
                            corr_words[j].append(elem)
                        start += 1
    else:
        corr_words = arpabet_word(correct_wordlist[i])

    pronounciation_error_pairs.append(((error_wordlist[i], err_word), (correct_wordlist[i], corr_words)))

# print(*pronounciation_error_pairs, sep="\n\n")

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# Compares pronunciation of word in error and correct word(s)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
error_dict = {}
i = 0
for error_pairs in pronounciation_error_pairs:
    e_pron_list = error_pairs[0][1]
    c_pron_list = error_pairs[1][1]
    # print(e_pron_list,c_pron_list)
    max_phoneme_similarity = 0
    # noinspection PyRedeclaration
    final_similar_pairs_for_max_phoneme = []
    leftover_phoneme = []
    max_stress_similarity = 0
    # noinspection PyRedeclaration
    final_similar_pairs_for_max_stress = []
    final_short_stress = final_long_stress = final_long_phones = final_short_phones = 0

    min_levenshtein = float("inf")
    for pron1 in e_pron_list:
        pron1_string = ""
        p1 = normalize_for_lev(pron1)
        for phone in p1:
            pron1_string += phone
        for pron2 in c_pron_list:
            pron2_string = ""
            p2 = normalize_for_lev(pron2)
            for phone in p2:
                pron2_string += phone
            levenshtein = edit_distance(pron1_string, pron2_string)
            offset_range = abs(len(pron1) - len(pron2)) + 1
            closest_state = 0
            if len(pron1) < len(pron2):
                shorter_list = pron1
                longer_list = pron2
            else:
                shorter_list = pron2
                longer_list = pron1

            for num in range(0, offset_range):
                phoneme_similarity = 0
                stress_similarity = 0
                similar_pairs = []
                # noinspection PyRedeclaration
                stress_index = [None, None, None, None, None, None]
                for q in range(0, len(shorter_list)):
                    if shorter_list[q].__contains__("0"):
                        stress_index[0] = q
                    if shorter_list[q].__contains__("1"):
                        stress_index[1] = q
                    if shorter_list[q].__contains__("2"):
                        stress_index[2] = q
                    if longer_list[q + num].__contains__("0"):
                        stress_index[3] = q
                    if longer_list[q + num].__contains__("1"):
                        stress_index[4] = q
                    if longer_list[q + num].__contains__("2"):
                        stress_index[5] = q
                    if shorter_list[q] == longer_list[q + num]:
                        phoneme_similarity += 1
                    if shorter_list[q] != longer_list[q + num]:
                        similar_pairs.append((pron1[q], pron2[q]))
                if levenshtein < min_levenshtein:
                    min_levenshtein = levenshtein
                if phoneme_similarity > max_phoneme_similarity:
                    max_phoneme_similarity = phoneme_similarity
                    final_similar_pairs_for_max_phoneme = [x for x in similar_pairs]
                    final_long_phones = len(longer_list)
                    final_short_phones = len(shorter_list)

                stress_similarity += int(stress_index[0] == stress_index[3] is not None) + int(
                    stress_index[1] == stress_index[4] is not None) + int(
                    stress_index[2] == stress_index[5] is not None)
                if stress_similarity >= max_stress_similarity:
                    max_stress_similarity = stress_similarity
                    final_similar_pairs_for_max_stress = [x for x in similar_pairs]
                    final_long_stress = final_short_stress = 0
                    for phone in longer_list:
                        if len(phone) == 3:
                            final_long_stress += 1
                    for phone in shorter_list:
                        if len(phone) == 3:
                            final_short_stress += 1
    phone_evaluation = stress_evaluation=""

    print(error_pairs[0][0], error_pairs[1][0])
    print(error_pairs[0][1], error_pairs[1][1])
    print("\tNumber of Identical Phonemes:", max_phoneme_similarity)
    print("\tLong Phones:", final_long_phones, "\t Short Phones:", final_short_phones)
    print("\tSimilar Pairs:", final_similar_pairs_for_max_phoneme)
    print("\tNumber of Identical Stresses:", max_stress_similarity)
    print("\tLong Stress:", final_long_stress, "\t Short Stress:", final_short_stress)
    print("\tSimilar Pairs:", final_similar_pairs_for_max_stress)
    print("\tLevenshtein:", min_levenshtein)

    # noinspection PyRedeclaration
    phone_flag = stress_flag = False
    if min_levenshtein == 0:
        phone_evaluation += "HOMOPHONES"
        phone_flag = True
    if 1 <= min_levenshtein <= 2 < final_short_phones and not phone_flag:
        phone_evaluation += "MINOR LEXICAL"
        phone_flag = True
    if 3 <= min_levenshtein <= 4 or max_phoneme_similarity >= (final_short_phones * .5) > 0 and not phone_flag:
        phone_evaluation += "PHONETIC SIMILARITY"
        phone_flag = True
    if not phone_flag:
        phone_evaluation += "NO PHONETIC SIMILARITY"
        phone_flag = True
    if max_stress_similarity == final_short_stress is not 0 or max_stress_similarity == final_long_stress is not 0:
        stress_evaluation += "STRESS SIMILARITY"
        stress_flag = True
    if not stress_flag:
        stress_evaluation += "NO STRESS SIMILARITY"
        stress_flag = True
    #print()
    cell = {
        'a. Error Word': error_pairs[0][0],
        'b. Error Word Pronunciations': error_pairs[0][1],
        'c. Correct Word': error_pairs[1][0],
        'd. Correct Word Pronunciations': error_pairs[1][1],
        'e. Number of Identical Phonemes': max_phoneme_similarity,
        'f. Long Phones': final_long_phones,
        'g. Short Phones': final_short_phones,
        'h. Similar Pairs Phoneme': final_similar_pairs_for_max_phoneme,
        'i. Number of Identical Stresses': max_stress_similarity,
        'j. Long Stresses': final_long_stress,
        'k. Short Stresses': final_short_stress,
        'l. Similar Pairs Stress': final_similar_pairs_for_max_stress,
        'm. Phoneme Evaluation': phone_evaluation,
        'n. Stress Evaluation': stress_evaluation
    }
    error_dict[i] = cell
    i += 1

possible_phoneme_similarity = {}
for key, value in error_dict.items():
    for key2, value2 in error_dict[key].items():
        if (key2 == "h. Similar Pairs Phoneme") and len(error_dict[key][key2])>0:
            for item in error_dict[key][key2]:
                ph1 = item[0]
                ph2 = item[1]
                if len(item[0]) == 3:
                    ph1 = ph1[:-1]
                if len(item[1]) == 3:
                    ph2 = ph2[:-1]
                try:
                    possible_phoneme_similarity[ph1][ph2] += 1
                except KeyError:
                    try:
                        possible_phoneme_similarity[ph1][ph2] = 1
                    except KeyError:
                        possible_phoneme_similarity[ph1] = {ph2:1}
                try:
                    possible_phoneme_similarity[ph2][ph1] += 1
                except KeyError:
                    try:
                        possible_phoneme_similarity[ph2][ph1] = 1
                    except KeyError:
                        possible_phoneme_similarity[ph2] = {ph1: 1}




df = pd.DataFrame.from_dict(error_dict)
#print(df)
df.to_excel("data.xlsx")

phonemes = pd.DataFrame.from_dict(possible_phoneme_similarity)
phonemes = phonemes.fillna(0)
phonemes.to_excel("phonemes.xlsx")

s = open("stext.txt","r")
sline = s.readlines()
sset = set(sline)
print(*sset)

