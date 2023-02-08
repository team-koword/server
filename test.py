from wordTable import *

# for TEST
# open file -> get dataBase
# TODO: convert file to DB
filePath = "./ko_word.json"
with open(filePath, "r", encoding="utf8") as file:
    dataBase = json.load(file)
HEIGHT, WIDTH = 7, 7
height, width = HEIGHT, WIDTH
wordTable = dict()
answerTable = dict()
answerList = list()


# test wordTable with words in dataBase
wordTable = initWordTable(dataBase, height, width)
print("\ninit table")
printWordTable(wordTable, height, width)

answerTable = setAnswerTable(dataBase, wordTable, answerTable, height, width)
print("\nanswerTable")
print(answerTable)

answerList = list(answerTable.keys())
print("\nanswerList")
print(len(answerList), answerList)

# answer = "없음"
# moveInfo, wordTable, answerTable, answerList = checkAnswer("없음", dataBase, wordTable, answerTable, answerList, height, width)
# print(f"\ncheckAnswer({answer})")
# print("\nmoveInfo")
# print(moveInfo)
# print("\nupdated wordTable")
# printWordTable(wordTable, height, width)
# print("\nanswerTable")
# print(answerTable)
# print("\nanswerList")
# print(len(answerList), answerList)

# answer = answerList[0]  # horizontal
answer = answerList[-1] # vertical
moveInfo, wordTable, answerTable, answerList = checkAnswer(
    answer, dataBase, wordTable, answerTable, answerList, height, width)
print(f"\ncheckAnswer({answer})")
print("\nmoveInfo")
print(moveInfo)
print("\nupdated wordTable")
printWordTable(wordTable, height, width)
# print(wordTable)
print("\nanswerTable")
print(answerTable)
print("\nanswerList")
print(len(answerList), answerList)
print("\nrandAnswer")


# # test with sample wordTable
# sampleWordTable = {0: "가", 1: "방", 2: "송", 3: "국", 4: "회", 5: "의", 6: "원", 7: "요", 8: "구", 9: "르", 10: "트", 11: "로", 12: "트", 13: "림", 14: "리", 15: "정", 16: "신", 17: "병", 18: "원", 19: "럭", 20: "각", 21: "사", 22: "진", 23: "관",
#                    24: "상", 25: "어", 26: "려", 27: "움", 28: "랑", 29: "시", 30: "기", 31: "상", 32: "조", 33: "력", 34: "자", 35: "바", 36: "황", 37: "하", 38: "루", 39: "살", 40: "이", 41: "율", 42: "퀴", 43: "제", 44: "초", 45: "제", 46: "인", 47: "간", 48: "성"}

# print("\nsampleWordTable")
# printWordTable(sampleWordTable, height, width)

# answerTable = setAnswerTable(dataBase, wordTable, answerTable, height, width)
# print("\nanswerTable from sampleWordTable")
# print(answerTable)

# answerList = list(answerTable.keys())
# print("\nanswerList")
# print(len(answerList), answerList)
