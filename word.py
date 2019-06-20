class Word:
    def __init__(self, wordStr, syllables):
        self.wordStr    = wordStr
        self.syllables  = syllables

    def setWordStr(self, wordStr):
        self.wordStr = wordStr

     def setSyllables(self, syllables):
        self.syllables = syllables

    def getWordStr(self):
        return self.wordStr

    def getSyllables(self):
        return self.syllables