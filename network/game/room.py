import json
import uuid

from enum import Enum

from .player import Player

from utils.data_structure import JsonSerializable

class RoomStatus(JsonSerializable, Enum):
    IN_GAME = 1
    ON_HOLD = 2

    def _basicValue(self):
        return self.value

    @staticmethod
    def getByValue(value):
        for action in RoomStatus:
            if value == action.value:
                return action
        raise NotImplementedError

class GamePhase(JsonSerializable, Enum):
    ELECTING_MASTER_ROOM = 1
    CHOOSING_ROUND_WORD = 2
    WAITING_ANSWERS = 3
    WAITING_CONTESTS = 4
    ELECTING_CORRECT_ANSWER = 5
    RESULT_ROUND = 6

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
