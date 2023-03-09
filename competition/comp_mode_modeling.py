from typing import Tuple
import hgtk
from sklearn.metrics.pairwise import cosine_similarity


# get similarity between answer word and comparing word
def getSimilarity(simModel, ansWord: str, cmpWord: str) -> float:
    def _jamo(word):
        def __tokenize(jamo):
            return jamo if jamo else "-"
        decomposed_token = ''
        for char in word:
            try:
                cho, jung, jong = hgtk.letter.decompose(char)
                cho = __tokenize(cho)
                jung = __tokenize(jung)
                jong = __tokenize(jong)
                decomposed_token = decomposed_token + cho + jung + jong
            except Exception as exception:
                if type(exception).__name__ == 'NotHangulException':
                    decomposed_token += char
        return decomposed_token
    ansVector, cmpVector \
        = map(lambda word: simModel.get_word_vector(_jamo(word)), [ansWord, cmpWord])
    return cosine_similarity([ansVector], [cmpVector])


# get similar words with similarity greater than standard value
# TODO: modify standard value and length of simWords
def getSimWords(simModel, wordList: list, answer: str) -> list:
    simData = list()
    simWords = list()
    MIN = 0.4

    # get similar words with similarity greater or equal than MIN
    for word in wordList:
        sim = getSimilarity(simModel, answer, word)
        if sim > MIN:
            simData.append((float(sim), word))
    
    # no words with minimum similarity
    if not simData:
        return []
    simData.sort(key = lambda x: -x[0])
    simWords = list(word[1] for word in simData)

    return simWords
