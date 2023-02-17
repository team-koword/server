from typing import Optional, Union, Tuple
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


# get rightwards distance to wall or filled cell
def getRightDist(wordTable: dict, loc: int, height: int, width: int) -> int:
    EMPTY = "  "
    dist = 0
    while getCol(loc, width) + dist < width:
        if wordTable[loc + dist] != EMPTY:
            break
        dist += 1
    return dist


# get downwards distance to wall or filled cell
def getDownDist(wordTable: dict, loc: int, height: int, width: int) -> int:
    EMPTY = "  "
    dist = 0
    while getRow(loc, width) + dist < height:
        if wordTable[loc + dist * width] != EMPTY:
            break
        dist += 1
    return dist


# get a random character
def getRandChar(ToPut: dict) -> str:
    return choice(list(ToPut))


# get a random word with startChar, with length less or equal than distance
def getRandWord(ToPut: dict, startChar: str, dist: int) -> str:
    len_list = ToPut.get(startChar, {}).keys()
    avail_len = [len for len in len_list if int(len) <= dist]

    if not len_list or not avail_len:
        return getRandChar(ToPut)

    rand_len = choice(avail_len)
    rand_word = choice(ToPut[startChar][rand_len])
    return rand_word




# init word table with empty cells
def initWordTable(wordTable: dict, height: int, width: int) -> dict:
    SIZE = height * width
    EMPTY = "  "
    
    for loc in range(SIZE):
        wordTable[loc] = EMPTY
    
    return wordTable




# put random words in empty cells of word table
def getWordTable(ToPut: dict, wordTable: dict, height: int, width: int, 
                 moveInfo: Optional[list]=None) -> Union[dict, Tuple[dict, list]]:
    # put word at word table start from loc in the dir
    # CAUTION: returning word starts with 2nd letter if word isn't single char
    def _put(wordTable: dict, word: str, loc: int, dir: int,
             height: int, width: int, moveInfo=None) -> None:
        SIZE = height * width
        EMPTY = "  "
        for i, char in enumerate(word):
            locTo = loc + i * dir
            # when updating word table
            if moveInfo:
                charRow = getRow(locTo, width)
                charBelow = 0
                # calculate locFrom
                while locTo + charBelow * width < SIZE \
                    and wordTable[locTo + charBelow * width] == EMPTY:
                    charBelow += 1
                locFrom = locTo - (charRow + charBelow) * width
                moveInfo.append([locFrom, locTo, char])
            wordTable[locTo] = char

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
            startChar = getRandChar(ToPut)
            randWord = getRandWord(ToPut, startChar, dist)
        # follow-up
        else:
            startChar = wordTable[loc - dir]
            randWord = getRandWord(ToPut, startChar, dist + 1)
            if len(randWord) >= 2:
                randWord = randWord[1:]
        _put(wordTable, randWord, loc, dir, height, width, moveInfo)
        loc += 1

    if moveInfo is None:
        return wordTable
    else:
        return wordTable, moveInfo


# get words and their locations in word table
def getWordMap(ToFind: dict, wordTable: dict, wordMap: dict,
               height: int, width: int) -> dict:
    # get word in row
    def _rightwards(ToFind: dict, wordTable: dict, wordMap: dict,
                    height, width, row, rightCnt) -> None:
        for colStart in range(width - 1):
            tempWord = wordTable[getLoc(row, colStart, width)]
            tempLocs = [getLoc(row, colStart, width)]
            for colEnd in range(colStart + 1, width):
                tempWord += wordTable[getLoc(row, colEnd, width)]
                tempLocs.append(getLoc(row, colEnd, width))
                tempChar, tempLen = tempWord[0], str(len(tempWord))
                if 2 <= int(tempLen) <= 5 and tempChar in ToFind.keys() \
                    and tempLen in ToFind[tempChar].keys() \
                        and tempWord in ToFind[tempChar][tempLen]:
                    if not tempWord in wordMap.keys():
                        wordMap[tempWord] = list()
                    wordMap[tempWord].append(tempLocs[:])
                    rightCnt += 1
        return rightCnt
    # get word in column
    def _downwards(ToFind: dict, wordTable: dict, wordMap: dict,
                   height: int, width: int, col: int, downCnt) -> None:
        for rowStart in range(height - 1):
            tempWord = wordTable[getLoc(rowStart, col, width)]
            tempLocs = [getLoc(rowStart, col, width)]
            for rowEnd in range(rowStart + 1, height):
                tempWord += wordTable[getLoc(rowEnd, col, width)]
                tempLocs.append(getLoc(rowEnd, col, width))
                tempChar, tempLen = tempWord[0], str(len(tempWord))
                if 2 <= int(tempLen) <= 5 and tempChar in ToFind.keys() \
                    and tempLen in ToFind[tempChar].keys() \
                        and tempWord in ToFind[tempChar][tempLen]:
                    if not tempWord in wordMap.keys():
                        wordMap[tempWord] = list()
                    wordMap[tempWord].append(tempLocs[:])
                    downCnt += 1
        return downCnt

    wordMap = dict()
    rightCnt, downCnt = 0, 0
    for row in range(0, height):
        rightCnt = _rightwards(ToFind, wordTable, wordMap,
                               height, width, row, rightCnt)
    for col in range(0, width):
        downCnt = _downwards(ToFind, wordTable, wordMap,
                             height, width, col, downCnt)

    # return wordMap, rightCnt, downCnt
    return wordMap


# check if the answer or similar words in word table
# if the answer in word table, remove only the answer(includes duplicated)
def updateWordTable(ToPut: dict, ToFind: dict, wordTable: dict, wordMap: dict,
                    removeWords: list, height: int, width: int) \
                        -> Tuple[dict, dict, list]:
    # remove the answer(s) or similar words
    def _remove(wordTable: dict, wordMap: dict, moveInfo: list,
                removeWords: list, height: int, width: int) -> list:
        BREAK = height * width
        EMPTY = "  "
        for removeWord in removeWords:
            if removeWord in wordMap:
                removeLocs = wordMap[removeWord]
                for locs in removeLocs:
                    for loc in locs:
                        if wordTable[loc] != EMPTY:
                            moveInfo.append([loc, BREAK, wordTable[loc]])
                            wordTable[loc] = EMPTY
        return moveInfo
    # cells above empty cells fall
    def _fall(wordTable: dict, moveInfo: list) -> list:
        SIZE = height * width
        EMPTY = "  "
        for loc in range(SIZE - 1, width - 1, -1):
            if not wordTable[loc] == EMPTY:
                continue
            locFrom = loc - width
            while locFrom >= 0:
                if wordTable[locFrom] != EMPTY:
                    moveInfo.append([locFrom, locFrom + width, wordTable[locFrom]])
                    wordTable[loc] = wordTable[locFrom]
                    wordTable[locFrom] = EMPTY
                    break
                locFrom -= width
        return moveInfo
    # add new words in empty cells
    def _add(ToPut: dict, wordTable: dict, moveInfo: list,
             height: int, width: int) -> Tuple[dict, list]:
        wordTable, moveInfo = \
            getWordTable(ToPut, wordTable, height, width, moveInfo)
        return wordTable, moveInfo

    moveInfo = list()
    
    if not removeWords:
        return wordTable, wordMap, moveInfo

    # remove
    moveInfo = _remove(wordTable, wordMap, moveInfo,
                         removeWords, height, width)
    # fall
    moveInfo = _fall(wordTable, moveInfo)
    # add
    wordTable, moveInfo = _add(ToPut, wordTable, moveInfo, height, width)
    # update wordMap
    wordMap = getWordMap(ToFind, wordTable, wordMap, height, width)

    return wordTable, wordMap, moveInfo
