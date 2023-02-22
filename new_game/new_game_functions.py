from typing import Optional


# global variables
EMPTY: str = "  "


# row = loc // width
def getRow(loc: int, width: int) -> int:
    return loc // width


# get downwards distance to wall or filled cell
def getDownDist(wordTable: dict, loc: int, height: int, width: int) -> int:
    dist = 1
    while getRow(loc, width) + dist < height:
        if wordTable[loc + dist * width] != EMPTY:
            break
        dist += 1
    return dist - 1


# init word table with empty cells
def initWordTable(wordTable: dict, height: int, width: int) -> None:
    SIZE = height * width

    for loc in range(-width, SIZE):
        wordTable[loc] = EMPTY

    return


# fall word to bottom or top of words and update room information
# new word if parameter left got, else existed word falls down
def fallWord(wordTable: dict, wordMap: dict, wordRows: dict, 
             height: int, width: int, word: str, 
             left: Optional[int] = None) -> int:
    # word starting location
    loc = left - width if left else wordMap[word]

    # get distance to fall
    fall = height
    for i in range(len(word)):
        fall = min(fall, getDownDist(wordTable, loc + i, height, width))
    
    # update wordTable
    for i in range(len(word)):
        wordTable[loc + i + fall * width] = wordTable[loc + i]
        if fall != 0:
            wordTable[loc + i] = EMPTY
    
    # update wordMap
    wordMap[word] += fall * width

    # update wordRows
    wordRows[getRow(loc, width)].remove(word)
    wordRows[getRow(loc, width) + fall].append(word)

    return fall


# remove words and update room information
def removeWords(wordTable: dict, wordMap: dict, wordRows: dict, 
                 height: int, width: int, words: list) -> None:
    for word in words:
        # remove a word from wordTable
        loc = wordMap[word]
        for i in range(len(word)):
            wordTable[loc + i] = EMPTY
        
        # remove a word from wordMap
        del(wordMap[word])
        # remove a word from wordRows
        wordRows[getRow(loc, width)].remove(word)

    return


# print wordTable in terminal(for test)
def printWordTable(wordTable: dict, height: int, width: int) -> None:
    for row in range(-1, height):
        for col in range(width):
            loc = row * width + col
            cell = wordTable[loc].replace(" ", "_")
            # print location
            DIGIT = len(str(height * width))
            cell = str(loc).zfill(DIGIT) + cell
            print(cell, end=" ")
        print()
