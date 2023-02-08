import json
from wordTable import *
# functions in wordTable
# def initWordTable(dataBase: dict, height: int, width: int) -> dict:
# 	return wordTable

# def setAnswerTable(dataBase: dict, wordTable: dict, answerTable: dict, height: int, width: int,
#                    rowFrom: int = None, rowTo: int = None, colFrom: int = None, colTo: int = None) -> dict:
# 	return answerTable

# def checkAnswer(answer: str, dataBase: dict, wordTable: dict, answerTable: dict, answerList: dict,
#                     height: int, width: int) -> dict:
# 	return moveInfo, wordTable, answerTable, answerList


from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

filePath = "./ko_word.json"
with open(filePath, 'r', encoding="utf8") as file:
    dataBase = json.load(file)

height, width = 0, 0
wordTable = dict()
answerTable = dict()
answerList = list()


@app.get("/init/{size}")
def init(size: int):
    global dataBase, wordTable, answerTable, answerList, height, width
    height, width = size, size

    wordTable = initWordTable(dataBase, height, width)
    answerTable = setAnswerTable(dataBase, wordTable, answerTable, height, width)
    answerList = list(answerTable.keys())

    return wordTable


@app.get("/check/{answer}")
def check(answer: str):
    global dataBase, wordTable, answerTable, answerList, height, width

    moveInfo, wordTable, answerTable, answerList = checkAnswer(answer, dataBase, wordTable, answerTable, answerList, height, width)

    return moveInfo


# # ------------------------- sample -------------------------
# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}
# # ------------------------- sample -------------------------
