import hashlib

from utils.data_structure import JsonSerializable

class Word(JsonSerializable):
    ENCODING = 'utf-8'

    def __init__(self, wordStr, syllables, hashSyllables=False):
        self.wordStr    = wordStr.title()
        self._syllables  = syllables.lower()
        self.hashSyllables = hashSyllables

    def __repr__(self):
        return repr(self.toJsonDict())

    def __eq__(self, other):
        if not isinstance(other, Word):
            raise TypeError('expected a Word')
        return (self.getNoHashSyllables().lower() == other.getNoHashSyllables().lower() and 
                    self.wordStr == other.wordStr)

    @property
    def syllables(self):
        return self._syllables if not self.hashSyllables else Word.hashStr(self._syllables)
    
    def setWordStr(self, wordStr):
        self.wordStr = wordStr

    def setSyllables(self, syllables):
        self.syllables = syllables

    def getWordStr(self):
        return self.wordStr

    def getSyllables(self):
        return self.syllables

    def getNoHashSyllables(self):
        return self._syllables

    def _dictKeyProperty(self):
        return {
            'wordStr': self.wordStr,
            'syllables': self.syllables
        }

    @staticmethod
    def _parseJson(jsonDict):
        wordStr = jsonDict['wordStr']
        syllables = jsonDict['syllables']
        return Word(wordStr, syllables)

    @staticmethod
    def hashStr(string):
        encodedSyllables = string.encode(Word.ENCODING)
        return hashlib.sha1(encodedSyllables).hexdigest()