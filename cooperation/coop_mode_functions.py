from typing import Optional


# global variables
EMPTY: str = "  "


# row = loc // width
def getRow(loc: int, width: int) -> int:
    return loc // width


# get downwards distance to wall or filled cell
def getDownDist(gameTable: dict, loc: int, height: int, width: int) -> int:
    dist = 1
    while getRow(loc, width) + dist < height:
        if gameTable[loc + dist * width] != EMPTY:
            break
        dist += 1

    return dist - 1


# init word table with empty cells
def initWordTable(gameTable: dict, height: int, width: int) -> None:
    SIZE = height * width

    for loc in range(-width, SIZE):
        gameTable[loc] = EMPTY

    return


# fall word to bottom or top of words and update room information
# new word if parameter left got, else existed word falls down
def fallWord(gameTable: dict, wordMap: dict, rowMap: dict, 
             height: int, width: int, word: str, 
             left: Optional[int] = None) -> int:
    # word starting location
    loc = left - width if left else wordMap[word]

    # get distance to fall
    fall = height
    for i in range(len(word)):
        fall = min(fall, getDownDist(gameTable, loc + i, height, width))
    
    # update gameTable
    for i in range(len(word)):
        gameTable[loc + i + fall * width] = gameTable[loc + i]
        if fall != 0:
            gameTable[loc + i] = EMPTY
    
    # update wordMap
    wordMap[word] += fall * width

    # update rowMap
    rowMap[getRow(loc, width)].remove(word)
    rowMap[getRow(loc, width) + fall].append(word)

    return fall


# remove words and update room information
def removeWords(gameTable: dict, wordMap: dict, rowMap: dict, 
                height: int, width: int, words: list) -> None:
    for word in words:
        # remove a word from gameTable
        loc = wordMap[word]
        for i in range(len(word)):
            gameTable[loc + i] = EMPTY
        
        # remove a word from wordMap
        del(wordMap[word])
        # remove a word from rowMap
        rowMap[getRow(loc, width)].remove(word)

    return


# print gameTable in terminal(for test)
def printWordTable(gameTable: dict, height: int, width: int) -> None:
    print("=" * (width * 3 - 1))
    # for row in range(-1, height):
    for row in range(height):
        for col in range(width):
            loc = row * width + col
            cell = gameTable[loc]
            # cell = gameTable[loc].replace(" ", "_")
            # # print location
            # DIGIT = len(str(height * width))
            # cell = str(loc).zfill(DIGIT) + cell
            print(cell, end=" ")
        print()

    return
