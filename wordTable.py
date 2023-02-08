import json
from random import *


# calculate location with row, col (and width)
# loc = row * width + col
def getLoc(row: int, col: int, width: int) -> int:
    # global width
    return row * width + col

# recalculate row from loc, width
# row = loc // width
def getRow(loc: int, width: int) -> int:
    return loc // width

# recalculate col from loc, width
# col = loc % width
def getCol(loc: int, width: int) -> int:
    return loc % width

# get randChar
# random.choice used
def getRandChar(dataBase: dict) -> str:
    return choice(list(dataBase))

# get randWord start with startChar and wordLen
# if randWord is not char, return randWord start with 2nd letter
def getRandWord(dataBase: dict, startChar: str, wordLen: int) -> str:
    if wordLen > 5:
        wordLen = 5
    randWord = getRandChar(dataBase)

    if startChar in dataBase and wordLen >= 2:
        tryCnt = 0
        while tryCnt < 4:
            try:
                randLen = str(randint(2, wordLen))
                randWord = choice(list(dataBase[startChar][randLen]))[1:]
                break
            except:
                tryCnt += 1
                continue
    return randWord

# put word at wordTable start from loc, in the dir
def putWordInTable(wordTable: dict, word: str, loc: int, dir: int) -> None:
    for i in range(len(word)):
        wordTable[loc + i * dir] = word[i]


# init wordTable with size height * width
def initWordTable(dataBase: dict, height: int, width: int) -> dict:
    wordTable = dict()
    size = height * width
    loc = 0

    # init wordTable
    for row in range(height):
        for col in range(width):
            initLoc = row * width + col
            wordTable[initLoc] = " "

    # get first word
    randChar = getRandChar(dataBase)
    while True:
        try:
            randLen = choice(list(dataBase[randChar]))
            randWord = choice(list(dataBase[randChar][randLen]))
            break
        except:
            continue

    # set first word in wordTable
    for i in range(len(randWord)):
        wordTable[loc + i] = randWord[i]
    loc += i + 1

    # set words in first row
    while loc < width:
        # set word start with lastChar, randLen(<= restHorizontal)
        lastChar = wordTable[loc - 1]
        restHorizontal = width - getCol(loc, width) + 1
        randWord = getRandWord(dataBase, lastChar, restHorizontal)
        for i in range(len(randWord)):
            wordTable[loc + i] = randWord[i]
        loc += i + 1

    # set words in rest rows, in the wordDir
    # wordDir = 1 for "horizontal" or width for "vertical", step val when increase loc
    while loc < size:
        restHorizontal = width - getCol(loc, width) + 1
        restVertical = height - getRow(loc, width) + 1
        wordDir = 1
        # escape if cell filled
        if wordTable[loc] != " ":
            loc += 1
            continue
        # unable to put word, put randChar
        elif restHorizontal < 2 and restVertical < 2:
            wordTable[loc] = getRandChar(dataBase)
        # put horizontal
        elif restVertical == 0 or restHorizontal > restVertical:
            wordDir = 1
            lastChar = wordTable[loc - wordDir]
            randWord = getRandWord(dataBase, lastChar, restHorizontal)
            if len(randWord) == 1 and restVertical >= 2:
                wordDir = width
                lastChar = wordTable[loc - wordDir]
                randWord = getRandWord(dataBase, lastChar, restVertical)
        # put vertical
        elif restHorizontal == 0 or restHorizontal < restVertical:
            wordDir = width
            lastChar = wordTable[loc - wordDir]
            randWord = getRandWord(dataBase, lastChar, restVertical)
            if len(randWord) == 1 and restHorizontal >= 2:
                wordDir = 1
                lastChar = wordTable[loc - wordDir]
                randWord = getRandWord(dataBase, lastChar, restHorizontal)
        # put random
        else:
            wordDir = choice([1, width])
            lastChar = wordTable[loc - wordDir]
            restDist = restHorizontal if wordDir == 1 else restVertical
            randWord = getRandWord(dataBase, lastChar, restDist)

        putWordInTable(wordTable, randWord, loc, wordDir)
        loc += 1

    return wordTable


# set answerTable with words in wordTable
# option: rowFrom <= row <= rowTo, colFrom <= col <= colTo
def setAnswerTable(dataBase: dict, wordTable: dict, answerTable: dict, height: int, width: int,
                   rowFrom: int = None, rowTo: int = None, colFrom: int = None, colTo: int = None) -> dict:
    def findInHorizontal(wordTable: dict, answerTable: dict, height: int, width: int, row: int) -> None:
        for colStart in range(width - 1):
            tempWord = wordTable[getLoc(row, colStart, width)]
            tempLocs = [getLoc(row, colStart, width)]
            for colEnd in range(colStart + 1, width):
                tempWord += wordTable[getLoc(row, colEnd, width)]
                tempLocs.append(getLoc(row, colEnd, width))
                if tempWord[0] in dataBase and 2 <= len(tempWord) <= 5:
                    if tempWord in dataBase[tempWord[0]][str(len(tempWord))]:
                        if not tempWord in answerTable:
                            answerTable[tempWord] = list()
                        answerTable[tempWord].append(tempLocs[:])

    def findInVertical(wordTable: dict, answerTable: dict, height: int, width: int, col: int) -> None:
        for rowStart in range(height - 1):
            tempWord = wordTable[getLoc(rowStart, col, width)]
            tempLocs = [getLoc(rowStart, col, width)]
            for rowEnd in range(rowStart + 1, height):
                tempWord += wordTable[getLoc(rowEnd, col, width)]
                tempLocs.append(getLoc(rowEnd, col, width))
                if tempWord[0] in dataBase and 2 <= len(tempWord) <= 5:
                    if tempWord in dataBase[tempWord[0]][str(len(tempWord))]:
                        if not tempWord in answerTable:
                            answerTable[tempWord] = list()
                        answerTable[tempWord].append(tempLocs[:])

    if not rowFrom:
        rowFrom = 0
    if not rowTo:
        rowTo = height - 1
    if not colFrom:
        colFrom = 0
    if not colTo:
        colTo = width - 1

    answerTable = dict()
    for row in range(rowFrom, rowTo + 1):
        findInHorizontal(wordTable, answerTable, height, width, row)
    for col in range(colFrom, colTo + 1):
        findInVertical(wordTable, answerTable, height, width, col)
    return answerTable


# check answer and return moveInfo and updated wordTable, answerTable, answerList
# moveInfo = [[moveFrom, moveTo, char], ...] ([empty list] if answer is wrong)
def checkAnswer(answer: str, dataBase: dict, wordTable: dict, answerTable: dict, answerList: dict,
                height: int, width: int) -> dict:
    # if answer is wrong
    if answer not in answerList:
        return [], wordTable, answerTable, answerList

    moveInfo = []
    # if answer is right
    answerLocs = answerTable[answer][0][:]
    answerDepth = getRow(answerLocs[0], width)
    answerDir = 1 if answerLocs[1] - answerLocs[0] == 1 else width
    answerHeight = len(answerLocs) if answerDir == width else 1
    answerWidth = len(answerLocs) if answerDir == 1 else 1

    rowFrom = getRow(answerLocs[0], width)
    rowTo = getRow(answerLocs[-1], width)
    colFrom = getCol(answerLocs[0], width)
    colTo = getCol(answerLocs[-1], width)

    # 1. add newWord at loc before fall down
    while True:
        try:
            newChar = getRandChar(dataBase)
            newWord = getRandWord(dataBase, newChar, len(answer))
            if dataBase[newChar][str(len(newChar+newWord))] and len(newChar+newWord) == len(answer):
                break
        except:
            continue
    newWordLoc = answerLocs[0] - (answerDepth + answerHeight) * width
    wordTable[newWordLoc] = newChar
    putWordInTable(wordTable, newWord, newWordLoc + answerDir, answerDir)

    # 2. set moveInfo and update wordTable
    delLoc = height * width
    for rowCnt in range(answerDepth + answerHeight * 2):
        for colCnt in range(1, answerWidth + 1):
            moveFrom = answerLocs[-colCnt]
            moveTo = delLoc if moveFrom in answerTable[answer][0] else moveFrom + \
                width * answerHeight
            moveInfo.append([moveFrom, moveTo, wordTable[moveFrom]])
            wordTable[moveTo] = wordTable[moveFrom]
            answerLocs[-colCnt] -= width
            print(f"moveInfo: {moveInfo}")
    # delete cells in temp location
    del wordTable[delLoc]
    for i in range(len(answer)):
        del wordTable[newWordLoc + i * answerDir]

    # 3. reset answerTable, answerList
    answerTable = setAnswerTable(dataBase, wordTable, answerTable, height, width,
                                 rowFrom, rowTo, colFrom, colTo)

    return moveInfo, wordTable, answerTable, answerList


# print wordTable in Terminal
def printWordTable(wordTable: dict, height: int, width: int) -> None:
    for col in range(height):
        line = list()
        for row in range(width):
            loc = col * width + row
            cell = wordTable[loc]
            line.append(cell)
        print(*line)


