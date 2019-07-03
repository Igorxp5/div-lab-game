import json
import uuid

from enum import Enum

from .player import Player, PlayerStatus

from utils.data_structure import JsonSerializable

class RoomStatus(JsonSerializable, Enum):
    IN_GAME = 1
    ON_HOLD = 2

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def _basicValue(self):
        return self.value

    @staticmethod
    def getByValue(value):
        for action in RoomStatus:
            if value == action.value:
                return action
        raise NotImplementedError

class GamePhase(JsonSerializable, Enum):
    ELECTING_ROUND_MASTER = 'Eleição do Organizador da Rodada'
    RELECTING_ROUND_MASTER = 'Releição do Organizador da Rodada'
    CHOOSING_ROUND_WORD = 'Escolha da Palavra da Rodada'
    WAITING_ANSWERS = 'Aguardando Respostas dos Jogadores'
    WAITING_CORRECT_ANSWER = 'Aguardando Resposta do Organizador da Rodada'
    WAITING_CONTESTS = 'Aguardando Contestações'
    ELECTING_CORRECT_ANSWER = 'Eleição da Resposta Correta'
    RESULT_ROUND = 'Resultado da Rodada'
    FINISHED = 'Fim do Jogo'

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def __str__(self):
        return self.value

    def _basicValue(self):
        return self.value

    @staticmethod
    def getByValue(value):
        for action in RoomStatus:
            if value == action.value:
                return action
        raise NotImplementedError

class Room(JsonSerializable):
    
    def __init__(self, id_, name, limitPlayers, owner, players, status):
        self.id             = id_
        self.name           = name
        self.limitPlayers   = limitPlayers
        self.owner          = owner
        self.players        = players
        self.status         = status

        self.bannedSockets  = {}

    def __repr__(self):
        return repr(self.toJsonDict())

    def setId(self, id):
        self.id = id

    def setName(self, name):
        self.name = name
    
    def setLimitPlayers(self, limitPlayers):
        self.limitPlayers = limitPlayers
    
    def setOwner(self, owner):
        self.owner = owner

    def setPlayers(self, players):
        self.players = players

    def setStatus(self, status):
        self.status = status

    def getId(self):
        return self.id

    def getName(self):
        return self.name
    
    def getLimitPlayers(self):
        return self.limitPlayers
    
    def getOwner(self):
        return self.owner
    
    def getPlayers(self):
        return self.players
    
    def getStatus(self):
        return self.status

    def getPlayer(self, socket):
        for player in self.players:
            if player.socket is socket:
                return player
        return None

    def getBannedSockets(self):
        return self.bannedSockets

    def isPlayerInRoom(self, socket):
        return self.getPlayer(socket) is not None

    def playerNameInRoom(self, playerName):
        for player in self.players:
            if player.nickname == playerName:
                return True
        return False

    def joinPlayer(self, socket, nickname):
        player = Player(nickname, socket, PlayerStatus.ON_HOLD)
        self.players.append(player)
        return player

    def removePlayer(self, socket):
        player = [p for p in self.players if p.socket is socket][0]
        self.players.remove(player)

    def banSocket(self, socket):
        self.bannedSockets[socket.ip] = socket

    def _dictKeyProperty(self):
        return {
            'id': self.id,
            'name': self.name,
            'limitPlayers': self.limitPlayers,
            'owner': self.owner,
            'players': self.players,
            'status': self.status
        }

    @staticmethod
    def createRoom(name, limitPlayers, owner):
        id_ = str(uuid.uuid1())
        players = []
        status = RoomStatus.ON_HOLD
        return Room(id_, name, limitPlayers, owner, players, status)

    @staticmethod
    def _parseJson(jsonDict, sockets):
        id_ = jsonDict['id']
        name = jsonDict['name']
        limitPlayers = jsonDict['limitPlayers']
        owner = sockets[jsonDict['owner']]
        players = jsonDict['players']
        players = [Player.parseJson(json.dumps(player), sockets) for player in players]
        status = RoomStatus.getByValue(jsonDict['status'])
        return Room(id_, name, limitPlayers, owner, players, status)
