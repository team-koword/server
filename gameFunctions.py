from random import choice


# loc = row * width + col
def getLoc(row: int, col: int, width: int) -> int:
    return row * width + col


# row = loc // width
def getRow(loc: int, width: int) -> int:
    return loc // width


# col = loc % width
def getCol(loc: int, width: int) -> int:
    return loc % width


def getRightDist(wordTable: dict, loc: int, height: int, width: int) -> int:
    EMPTY = "  "
    dist = 0
    while getCol(loc, width) + dist < width:
        if wordTable[loc + dist] != EMPTY:
            break
        dist += 1
    return dist


def getDownDist(wordTable: dict, loc: int, height: int, width: int) -> int:
    EMPTY = "  "
    dist = 0
    while getRow(loc, width) + dist < height:
        if wordTable[loc + dist * width] != EMPTY:
            break
        dist += 1
    return dist


# get a random character
def getRandChar(wordData: dict) -> str:
    return choice(list(wordData))


# get a random word with startChar, with length less or equal than distance
def getRandWord(wordData: dict, startChar: str, dist: int) -> str:
    try:
        lenList = list(wordData[startChar].keys())
        availLen = list(len for len in lenList if int(len) <= dist)
        randLen = choice(availLen)
        randWord = choice(wordData[startChar][randLen].split(","))
    except:
        randWord = getRandChar(wordData)
    # return random character if no word start with startChar or available in dist
    if startChar not in wordData.keys() or not availLen:
        return getRandChar(wordData)

    randLen = choice(availLen)
    randWord = choice(wordData[startChar][randLen].split(","))

    return randWord


# initialize word table with size(height * width)
# and also use to update word table
def getWordTable(wordData: dict, wordTable: dict,
                 height: int, width: int, updateInfo=None) -> dict:
    # put word at word table start from loc in the dir
    # CAUTION: returning word starts with 2nd letter if word isn't single char
    def _put(wordTable: dict, word: str, loc: int, dir: int,
             updateInfo=None) -> None:
        for i in range(len(word)):
            locTo = loc + i * dir
            # when updating word table
            if updateInfo:
                charRow = getRow(locTo, width)
                charBelow = 0
                while wordTable[locTo + charBelow * width] == "  ":
                    charBelow += 1
                locFrom = locTo - (charRow + charBelow) * width
                updateInfo.append([locFrom, locTo, word[i]])
            wordTable[locTo] = word[i]
        # print(f"put word: {word}")

    SIZE = height * width
    EMPTY = "  "
    RIGHT, DOWN = 1, width
    FIRST = 1
    loc = 0

    # set words in wordTable
    while loc < SIZE:
        # skip if cell filled
        if wordTable[loc] != EMPTY:
            loc += 1
            continue
        # set random direction
        dir = choice([RIGHT, DOWN])
        # calculate distance to wall or filled cell
        dist = getRightDist(wordTable, loc, height, width) if dir == RIGHT \
            else getDownDist(wordTable, loc, height, width)
        # start with random character if rightwards at left or downwards at top
        if (dir == RIGHT and getCol(loc, width) < FIRST) \
            or (dir == DOWN and getRow(loc, width) < FIRST):
            startChar = getRandChar(wordData)
            randWord = getRandWord(wordData, startChar, dist)
        # follow-up
        else:
            startChar = wordTable[loc - 1]
            randWord = getRandWord(wordData, startChar, dist)
            if len(randWord) >= 2:
                randWord = randWord[1:]
        _put(wordTable, randWord, loc, dir, updateInfo)
        loc += 1

    if updateInfo is None:
        return wordTable
    else:
        return wordTable, updateInfo


# get words and their locations in word table
def getWordMap(wordData: dict, wordTable: dict, wordMap: dict,
               height: int, width: int):
    # get word in row
    def _rightwards(wordData: dict, wordTable: dict, wordMap: dict,
                    height, width, row, rightCnt) -> None:
        for colStart in range(width - 1):
            tempWord = wordTable[getLoc(row, colStart, width)]
            tempLocs = [getLoc(row, colStart, width)]
            for colEnd in range(colStart + 1, width):
                tempWord += wordTable[getLoc(row, colEnd, width)]
                tempLocs.append(getLoc(row, colEnd, width))
                tempChar, tempLen = tempWord[0], str(len(tempWord))
                if tempChar in wordData.keys() \
                    and tempLen in wordData[tempChar].keys() \
                        and tempWord in wordData[tempChar][tempLen].split(","):
                    if not tempWord in wordMap.keys():
                        wordMap[tempWord] = list()
                    wordMap[tempWord].append(tempLocs[:])
                    rightCnt += 1
        return rightCnt
    # get word in column
    def _downwards(wordData: dict, wordTable: dict, wordMap: dict,
                   height: int, width: int, col: int, downCnt) -> None:
        for rowStart in range(height - 1):
            tempWord = wordTable[getLoc(rowStart, col, width)]
            tempLocs = [getLoc(rowStart, col, width)]
            for rowEnd in range(rowStart + 1, height):
                tempWord += wordTable[getLoc(rowEnd, col, width)]
                tempLocs.append(getLoc(rowEnd, col, width))
                tempChar, tempLen = tempWord[0], str(len(tempWord))
                if tempChar in wordData.keys() \
                    and tempLen in wordData[tempChar].keys() \
                        and tempWord in wordData[tempChar][tempLen].split(","):
                    if not tempWord in wordMap.keys():
                        wordMap[tempWord] = list()
                    wordMap[tempWord].append(tempLocs[:])
                    downCnt += 1
        return downCnt

    wordMap = dict()
    rightCnt, downCnt = 0, 0
    for row in range(0, height):
        rightCnt = _rightwards(wordData, wordTable, wordMap,
                               height, width, row, rightCnt)
    for col in range(0, width):
        downCnt = _downwards(wordData, wordTable, wordMap,
                             height, width, col, downCnt)

    # return wordMap, rightCnt, downCnt
    return wordMap


# check if the answer or relative words in word table
# if the answer in word table, remove only the answer(includes duplicated)
def updateWordTable(wordData: dict, wordTable: dict, wordMap: dict,
                    removeWords: list, height: int, width: int):
    # remove the answer(s) or relative words
    def _remove(wordTable: dict, wordMap: dict, updateInfo: list,
                removeWords: list, height: int, width: int) -> list:
        BREAK = height * width
        EMPTY = "  "
        for removeWord in removeWords:
            if removeWord in wordMap:
                removeLocs = wordMap[removeWord]
                for locs in removeLocs:
                    for loc in locs:
                        if wordTable[loc] != EMPTY:
                            updateInfo.append([loc, BREAK, wordTable[loc]])
                            wordTable[loc] = EMPTY
        return updateInfo
    # cells above empty cells fall
    def _fall(wordTable: dict, updateInfo: list) -> list:
        SIZE = height * width
        EMPTY = "  "
        for loc in range(SIZE - 1, width - 1, -1):
            if wordTable[loc] == EMPTY:
                locFrom = loc - width
                while locFrom >= 0:
                    if wordTable[locFrom] != EMPTY:
                        updateInfo.append([locFrom, locFrom + width, wordTable[locFrom]])
                        wordTable[loc] = wordTable[locFrom]
                        wordTable[locFrom] = EMPTY
                        break
                    locFrom -= width
        return updateInfo
    # add new words in empty cells
    def _add(wordData: dict, wordTable: dict, updateInfo: list,
             height: int, width: int):
        wordTable, updateInfo = \
            getWordTable(wordData, wordTable, height, width, updateInfo)
        return wordTable, updateInfo

    updateInfo = list()

    # remove
    updateInfo = _remove(wordTable, wordMap, updateInfo,
                         removeWords, height, width)
    # fall
    updateInfo = _fall(wordTable, updateInfo)
    # add
    wordTable, updateInfo = _add(
        wordData, wordTable, updateInfo, height, width)
    # update wordMap
    wordMap = getWordMap(wordData, wordTable, wordMap, height, width)

    return wordTable, wordMap, updateInfo
