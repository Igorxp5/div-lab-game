class Player:
    def __init__(self, nickname, socket, status, chosenWords, successfulWords, wordsAnswered, score):
        self.nickname           = nickname
        self.socket             = socket        
        self.status             = status
        self.chosenWords        = chosenWords
        self.successfulWords    = successfulWords
        self.wordsAnswered      = wordsAnswered
        self.score              = score

    def setNickname(self, nickname):
        self.nickname = nickname
    
    def getNickname(self):
        return self.nickname

    def setSocket(self, socket):
        self.socket = socket
    
    def getSocket(self):
        return self.socket

    def setStatus(self, status):
        self.status = status
    
    def getStatus(self):
        return self.status
    
    def setChosenWords(self, chosenWords):
        self.chosenWords = chosenWords
    
    def getChosenWords(self):
        return self.chosenWords

    def setSuccessfulWords(self, successfulWords):
        self.successfulWords = successfulWords
    
    def getSuccessfulWords(successfulWords):
        return self.successfulWords
    
    def setWordsAnswered(self, wordsAnswered):
        self.wordsAnswered = wordsAnswered
    
    def getWordsAnswered(self):
        return self.wordsAnswered

    def setScore(self, score):
        self.score = score
    
    def getScore(self):
        return self.score
    