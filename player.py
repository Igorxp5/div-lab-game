from enum import Enum

class UserStatus(Enum):
    WATCHING                                            = 1
    VOTING_ON_THE_ROUND_ORGANIZER                       = 2
    AWAITING_THE_END_OF_ORGANIZER_VOTE                  = 3
    CHOOSING_THE_WORD_OF_THE_ROUND                      = 4
    OUTSTANDING_ORGANIZER_CHOOSES_THE_WORD_OF_THE_ROUND = 5
    RESPONDING_TO_SILABIC_DIVISION                      = 6
    AWAITING_THE_END_OF_THE_SILABIC_DIVISION_PHASE      = 7
    VOTING_IN_CONTEST_OF_THE_CORRECT_WORD               = 8
    AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST       = 9
    WAITING_FOR_NEXT_ROUND                              = 10
    ELIMINATED                                          = 11

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
    
    def getSuccessfulWords(self, successfulWords):
        return self.successfulWords
    
    def setWordsAnswered(self, wordsAnswered):
        self.wordsAnswered = wordsAnswered
    
    def getWordsAnswered(self):
        return self.wordsAnswered

    def setScore(self, score):
        self.score = score
    
    def getScore(self):
        return self.score

class PlayerAnswer:
    def __init__(self, elector, vote):
        self.elector    = elector
        self.vote  = vote

    def setElector(self, elector):
        self.elector = elector

    def setVote(self, vote):
        self.vote = vote

    def getElector(self):
        return self.elector

    def getVote(self):
        return self.vote