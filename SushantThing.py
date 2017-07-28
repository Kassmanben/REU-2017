f = open("/Users/Ben/PycharmProjects/REU2017/Trial_9_07_07_17/T9_Scenario Transcript", "r")
lines = f.readlines()
final = []
for line in lines:
    line += " // "
    split_line = line.split()
    for word in split_line:
        final.append(word.replace("d#","").replace("t#","").replace("*","").lower())
print(*final, sep="\n")