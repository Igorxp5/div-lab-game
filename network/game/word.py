import hashlib

from utils.data_structure import JsonSerializable

class Word(JsonSerializable):
    ENCODING = 'utf-8'

    def __init__(self, wordStr, syllables, hashSyllables=False):
        self.wordStr    = wordStr
        self.syllables  = syllables
        self.hashSyllables = hashSyllables

    def __repr__(self):
        return repr(self.toJsonDict())

    def __eq__(self, other):
        if not isinstance(other, Word):
            raise TypeError('expected a Word')
        return self.syllables == other.syllables and self.wordStr == other.wordStr

    def setWordStr(self, wordStr):
        self.wordStr = wordStr

    def setSyllables(self, syllables):
        self.syllables = syllables

    def getWordStr(self):
        return self.wordStr

    def getSyllables(self):
        return self.syllables

    def _dictKeyProperty(self):
        syllables = self.syllables if not self.hashSyllables else Word._hashStr(self.syllables)
        return {
            'wordStr': self.wordStr,
            'syllables': syllables
        }

    @staticmethod
    def _parseJson(jsonDict):
        wordStr = jsonDict['wordStr']
        syllables = jsonDict['syllables']
        return Word(wordStr, syllables)

    @staticmethod
    def _hashStr(string):
        encodedSyllables = string.encode(Word.ENCODING)
        return hashlib.sha1(encodedSyllables).hexdigest()