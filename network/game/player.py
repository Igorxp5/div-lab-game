from enum import Enum

from utils.data_structure import JsonSerializable

class PlayerStatus(JsonSerializable, Enum):
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

    def _basicValue(self):
        return self.value

class Player(JsonSerializable):
    def __init__(self, nickname, socket, status):
        self.nickname           = nickname
        self.socket             = socket        
        self.status             = status

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

    def setScore(self, score):
        self.score = score
    
    def getScore(self):
        return self.score

    def _dictKeyProperty(self):
        return {
            'nickname': self.nickname,
            'socket': self.socket,
            'status': self.status
        }

class PlayerAnswer(JsonSerializable):
    def __init__(self, owner, word):
        self.owner    = owner
        self.word  = word

    def setElector(self, owner):
        self.owner = owner

    def setWord(self, word):
        self.word = word

    def getElector(self):
        return self.owner

    def getWord(self):
        return self.word

    def _dictKeyProperty(self):
        return {
            'owner': self.owner,
            'word': self.word
        }