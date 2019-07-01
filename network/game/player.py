import json

from enum import Enum

from utils.data_structure import JsonSerializable

class PlayerStatus(JsonSerializable, Enum):
    ON_HOLD                                             = 'Aguardando começar o jogo'
    WATCHING                                            = 'Assistindo'
    VOTING_ON_THE_ROUND_ORGANIZER                       = 'Votando para Organizador da Rodada'
    AWAITING_THE_END_OF_ORGANIZER_VOTE                  = 'Esperando Fim da Votação do Organizador da Rodada'
    CHOOSING_THE_WORD_OF_THE_ROUND                      = 'Escolhendo Palavra da Rodada'
    OUTSTANDING_ORGANIZER_CHOOSES_THE_WORD_OF_THE_ROUND = 'Aguardando Escolha da Palavra da Rodada'
    RESPONDING_TO_SILABIC_DIVISION                      = 'Respondendo Divisão Silábica'
    AWAITING_THE_END_OF_THE_SILABIC_DIVISION_PHASE      = 'Aguardando Fim da Fase Divisão Silábica'
    VOTING_IN_CONTEST_OF_THE_CORRECT_WORD               = 'Votando na Contestação de Resposta Correta'
    AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST       = 'Aguardando Fim da Contestação de Resposta Correta'
    WAITING_FOR_NEXT_ROUND                              = 'Aguardando Fim da Rodada'
    ELIMINATED                                          = 'Eliminado'

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def _basicValue(self):
        return self.value

    @staticmethod
    def getByValue(value):
        for action in PlayerStatus:
            if value == action.value:
                return action
        raise NotImplementedError

class Player(JsonSerializable):
    def __init__(self, nickname, socket, status):
        self.nickname           = nickname
        self.socket             = socket
        self.status             = status

    def __repr__(self):
        return repr(self.toJsonDict())

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

    @staticmethod
    def _parseJson(jsonDict, sockets):
        nickname = jsonDict['nickname']
        socket = sockets[jsonDict['socket']]
        status = PlayerStatus.getByValue(jsonDict['status'])
        return Player(nickname, socket, status)

class PlayerAnswer(JsonSerializable):
    def __init__(self, owner, word):
        self.owner    = owner
        self.word  = word

    def __repr__(self):
        return repr(self.toJsonDict())

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

    @staticmethod
    def _parseJson(jsonDict, players):
        owner = [player for player in players if player.socket.ip == jsonDict['owner']['socket']][0]
        word = Word.parseJson(json.dumps(jsonDict['word']))
        return PlayerAnswer(owner, word)