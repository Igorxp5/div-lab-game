import json
import time
import traceback # TODO: Remover no final do projeto

import network.config as CONFIG

from network.network import Network
from network.packet import PacketRequest, PacketResponse, PacketType, InvalidPacketError
from network.action import Action, ActionGroup, ActionParam, ActionRw, ActionError

from utils.data_structure import JsonSerializable
from utils.network_interfaces import getAllIpAddress

from network.game.room import Room, RoomStatus, GamePhase
from network.game.player import Player, PlayerStatus, PlayerAnswer
from network.game.word import Word

from threading import Thread, Event, Lock
from datetime import datetime
from importlib import reload

import _game_controller_test

class SharedGameData(JsonSerializable):
	def __init__(self):
		self.room 				= None
		self.roomMaster 		= None
		self.roundWord 			= None
		self.gamePhase 			= None

		self.chosenWords 		= []
		self.masterRoomVotes 	= {}
		self.contestAnswerVotes = {}
		self.roundAnswers 		= {}
		
		self.roundNumber 		= 0

		self._phaseTimeStart 	= None
		self._phaseTimeDesired  = 0

	@property
	def phaseTime(self):
		return self._phaseTimeDesired - ((datetime.now() - self._phaseTimeStart).seconds)

	@phaseTime.setter
	def phaseTime(self, countdown):
		self._phaseTimeDesired = countdown
		self._phaseTimeStart = datetime.now()

	def _dictKeyProperty(self):
		return {
			'room': self.room,
			'roomMaster': self.roomMaster,
			'roundWord': self.roundWord,
			'gamePhase': self.gamePhase,
			'chosenWords': self.chosenWords,
			'masterRoomVotes': {ip: votePlayer.socket for ip, votePlayer in self.masterRoomVotes.items()},
			'contestAnswerVotes': {ip: votePlayer.socket for ip, votePlayer in self.contestAnswerVotes.items()},
			'roundAnswers': self.roundAnswers,
			'roundNumber': self.roundNumber,
			'phaseTime': self.phaseTime
		}

	@staticmethod
	def _parseJson(jsonDict, sockets):
		sharedGameData = SharedGameData()
		
		roomJsonData = json.dumps(jsonDict['room'])
		sharedGameData.room = Room.parseJson(roomJsonData, sockets)

		roomMasterJsonData = json.dumps(jsonDict['roomMaster'])
		sharedGameData.roomMaster = Player.parseJson(roomMasterJsonData, sockets)

		roundWordJsonData = json.dumps(jsonDict['roundWord'])
		sharedGameData.roundWord = Word.parseJson(roundWordJsonData)

		sharedGameData.gamePhase = GamePhase.getByValue(jsonDict['gamePhase'])

		for wordDict in jsonDict['chosenWords']:
			wordJsonData = json.dumps(wordDict)
			word = Word.parseJson(wordJsonData)
			sharedGameData.chosenWords.append(word)

		for ip, voteIp in jsonDict['masterRoomVotes']:
			sharedGameData.masterRoomVotes[ip] = sharedGameData.room.players[voteIp]

		for ip, voteIp in jsonDict['contestAnswerVotes']:
			sharedGameData.masterRoomVotes[ip] = sharedGameData.room.players[voteIp]
		
		for ip, playerAnswerDict in jsonDict['roundAnswers']:
			playerAnswerJsonData = json.dumps(playerAnswerDict)
			playerAnswer = PlayerAnswer.parseJson(
				playerAnswerJsonData, sharedGameData.room.players
			)
			sharedGameData.roundAnswers[ip] = playerAnswer

		sharedGameData.roundNumber = jsonDict['roundNumber']
		sharedGameData.phaseTime = jsonDict['phaseTime']
		
		return sharedGameData


class Game(Thread):
	DISCOVERY_PORT = 8400
	TCP_SERVER_PORT = 8401
	PACKET_WAITING_APPROVATION_QUEUE_SIZE = 30

	def __init__(self, address):
		super().__init__(daemon=True)
		self._discoveryAddress = address, Game.DISCOVERY_PORT
		self._tcpAddress = address, Game.TCP_SERVER_PORT

		self._network = Network(self._discoveryAddress, self._tcpAddress)
		self._network.setListenPacketCallback(self._listenPacketCallback)

		self._rooms = {}
		self._sharedGameData = SharedGameData()

		# Adicionando callbacks para os tipos de pacotes
		self._listenPacketCallbackByAction = {action: [] for action in Action}
		self._listenPacketCallbackByAction[Action.CREATE_ROOM].append(self._createRoomCallback)
		self._listenPacketCallbackByAction[Action.GET_LIST_ROOMS].append(self._getListRoomsCallback)
		self._listenPacketCallbackByAction[Action.JOIN_ROOM_PLAY].append(self._joinRoomToPlayCallback)
		self._listenPacketCallbackByAction[Action.QUIT_ROOM].append(self._quitRoomCallback)
		self._listenPacketCallbackByAction[Action.START_ROOM_GAME].append(self._startGameCallback)

		self._packetWaitingApprovation = {}
		self._donePacketHandler = set()

		self._waitDownloadListRooms = Event()

	@property
	def _receiverGroupIps(self):
		receiverGroupIps = {
			ActionGroup.ROOM_PLAYERS: {},
			ActionGroup.ROOM_OWNER: {}
		}
		if self._sharedGameData.room:
			receiverGroupIps[ActionGroup.ROOM_PLAYERS] = (
				{player.socket.ip: player.socket for player in self._sharedGameData.room.players}
			)
			receiverGroupIps[ActionGroup.ROOM_OWNER] = {
				self._sharedGameData.room.owner.ip: self._sharedGameData.room.owner
			}
		return receiverGroupIps

	@property
	def socket(self):
		return self._network.socket

	def run(self):
		self._network.start()
		self._network.blockUntilConnectToNetwork()

		if len(self._network.peers) > 0:
			self._waitDownloadListRooms.set()
			self.downloadListRooms()
			self._waitDownloadListRooms.wait()

		while True:
			input('Tecle Enter para recarregar o Game Controller...\n')
			try:
				reload(_game_controller_test)
				_game_controller_test.gameController(self)
			except Exception as exception:
				traceback.print_exc()

	def downloadListRooms(self):
		packet = PacketRequest(Action.GET_LIST_ROOMS)
		socketIp = list(self._network.peers)[0]
		socket = self._network.peers[socketIp]
		self._sendPacketRequest(packet, toSocket=socket)

	def createRoom(self, name, limitPlayers, playerName):
		room = Room.createRoom(name, limitPlayers, self.socket)
		params = {
			ActionParam.ROOM_ID: room.id,
			ActionParam.ROOM_NAME: room.name,
			ActionParam.PLAYERS_LIMIT: room.limitPlayers,
			ActionParam.PLAYER_NAME: playerName
		}
		packet = PacketRequest(Action.CREATE_ROOM, params)
		self._sendPacketRequest(packet)
		return room

	def joinRoomToPlay(self, roomId, playerName):
		params = {
			ActionParam.ROOM_ID: roomId,
			ActionParam.PLAYER_NAME: playerName
		}
		packet = PacketRequest(Action.JOIN_ROOM_PLAY, params)
		self._sendPacketRequest(packet)

	def quitRoom(self):
		if not self._sharedGameData.room:
			raise RuntimeError(1, 'Player not in a room to quit.')
		params = {
			ActionParam.ROOM_ID: self._sharedGameData.room.id,
		}
		packet = PacketRequest(Action.QUIT_ROOM, params)
		self._sendPacketRequest(packet)

	def startGame(self):
		if not self._sharedGameData.room:
			raise RuntimeError(2, 'Player not in a room to start game.')

		if self._sharedGameData.room.owner is not self.socket:
			raise RuntimeError(3, 'Player is not room owner to start game.')

		if len(self._sharedGameData.room.players) < CONFIG.MIN_PLAYERS_TO_START:
			raise RuntimeError(4, 'Room has not min players to start game.')

		params = {
			ActionParam.ROOM_ID: self._sharedGameData.room.id,
		}
		packet = PacketRequest(Action.START_ROOM_GAME, params)
		self._sendPacketRequest(packet)		


	def setListenPacketCallbackByAction(self, action, callback):
		if not isinstance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].append(callback)

	def removeListenPacketCallbackByAction(self, action, callback):
		if not isinstance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].remove(callback)

	def _listenPacketCallback(self, socket, packet):
		if packet.action.rw == ActionRw.READ:
			self._actionReadPacketCallback(socket, packet)

		elif packet.action.rw == ActionRw.WRITE:
			self._waiterHandler(socket, packet)

	def _packetApprovedCallback(self, socket, packet, responses):
		listResponses = list(responses.values())
		mostCommonPacketResponse = max(set(listResponses), key=listResponses.count)
		actionError = mostCommonPacketResponse.actionError

		if packet.action in self._listenPacketCallbackByAction:
			for callback in self._listenPacketCallbackByAction[packet.action]:
				callback(socket, packet.params, actionError)

		if actionError != ActionError.NONE:
			print(f'From {socket}: Erro #{actionError.code} - {actionError}')

	def _actionReadPacketCallback(self, socket, packet):
		if packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketRequest):
			content = {id_: room.toJsonDict() for id_, room in self._rooms.items()}
			packet = PacketResponse(packet.action, content=content, uuid=packet.uuid)
			self._sendPacket(packet, toSocket=socket)	
		
		elif packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketResponse):
			self._getListRoomsCallback(socket, packet.content)

	def _getListRoomsCallback(self, socket, content):
		if content is not None:
			for id_, room in content.items():
				roomJsonData = json.dumps(room)
				self._rooms[id_] = Room.parseJson(roomJsonData, self._network.allNetwork)

	def _createRoomCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			id_ = params[ActionParam.ROOM_ID]
			name = params[ActionParam.ROOM_NAME]
			limitPlayers = params[ActionParam.PLAYERS_LIMIT]
			playerName = params[ActionParam.PLAYER_NAME]
			room = Room(
				id_, name, limitPlayers, socket, [], RoomStatus.ON_HOLD
			)
			room.joinPlayer(socket, playerName)
			self._rooms[id_] = room
			print(f'O {socket} \'{playerName}\' criou a sala {repr(name)}({limitPlayers})')

			if socket is self.socket:
				self._sharedGameData.room = room

	def _joinRoomToPlayCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			roomId = params[ActionParam.ROOM_ID]
			playerName = params[ActionParam.PLAYER_NAME]
			player = Player(playerName, socket, PlayerStatus.ON_HOLD)
			self._rooms[roomId].players.append(player)
			self._sharedGameData.room = self._rooms[roomId]
			print(f'O {socket} entrou na sala \'{self._rooms[roomId].name}\' como \'{playerName}\'')

	def _quitRoomCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			roomId = params[ActionParam.ROOM_ID]
			room = self._rooms[roomId]
			player = room.getPlayer(socket)
			room.removePlayer(socket)

			print(f'O jogador {player.nickname} saiu da sala \'{room.name}\'.')

			if self._sharedGameData.room and self._sharedGameData.room.id == roomId:
				self._sharedGameData.room = None

			if len(room.players) == 0:
				del self._rooms[roomId]

	def _startGameCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			roomId = params[ActionParam.ROOM_ID]
			room = self._rooms[roomId]
			if room.isPlayerInRoom(self.socket):
				self._sharedGameData.room.status = RoomStatus.IN_GAME
				self._sharedGameData.room.gamePhase = GamePhase.ELECTING_MASTER_ROOM
				self._sharedGameData.roundNumber = 1
				self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			print(f'O {socket} iniciou o jogo da sala \'{room.name}\'')


	def _sendPacketRequest(self, packet, toSocket=None):
		self._sendPacket(packet, toSocket)
		self._createPacketWaiter(packet)
		self._savePacketRequestWaiter(self.socket, packet)

	def _sendPacket(self, packet, toSocket=None):
		if not toSocket:
			self._network.sendPacket(packet, receiverGroupIps=self._receiverGroupIps)
		else:
			self._network.sendPacket(packet, toSocket=toSocket)

	def _createPacketWaiter(self, packet):
		if packet.uuid not in self._packetWaitingApprovation:
			self._packetWaitingApprovation[packet.uuid] = {
				'request_socket': None,
				'request_packet': None,
				'responses': {},
				'agreements_list': [],
				'disagreements_list': [],
				'first_packet_time': datetime.now(),
				'lock': Lock()
			}

	def _deletePacketWaiter(self, packet):
		if packet.uuid in self._packetWaitingApprovation:
			del self._packetWaitingApprovation[packet.uuid]

	def _savePacketRequestWaiter(self, socket, packet):
		self._packetWaitingApprovation[packet.uuid]['request_socket'] = socket
		self._packetWaitingApprovation[packet.uuid]['request_packet'] = packet

	def _waiterHandler(self, socket, packet):
		self._createPacketWaiter(packet)

		packetWaiter = self._packetWaitingApprovation[packet.uuid]

		packetWaiter['lock'].acquire()

		# Ignorar pacotes de ações já aprovadas ou desaprovadas
		if packet.uuid in self._donePacketHandler:
			self._deletePacketWaiter(packet)
			packetWaiter['lock'].release()
			return

		if packet.packetType == PacketType.REQUEST:
			if not self._isValidPacket(socket, packet):
				self._deletePacketWaiter(packet)
				packetWaiter['lock'].release()
				return

			self._savePacketRequestWaiter(socket, packet)

			if self._isSocketInApprovationGroup(self.socket, packet):
				actionError = self._testPacketConditions(socket, packet)
				packetResponse = PacketResponse(packet.action, actionError, uuid=packet.uuid)
				self._sendPacket(packetResponse)

		elif packet.packetType == PacketType.RESPONSE:
			packetWaiter['responses'][socket.ip] = packet
			
			approvationList = packetWaiter['agreements_list']
			if not packet.approved:
				approvationList = packetWaiter['disagreements_list']
			approvationList.append(socket)


		isPacketApproved = self._isPacketApproved(socket, packet)
		isPacketDisapproved = self._isPacketDisapproved(socket, packet)

		if isPacketApproved or isPacketDisapproved:
			requestSocket = packetWaiter['request_socket']
			requestPacket = packetWaiter['request_packet']
			responses = packetWaiter['responses']
			Thread(
				target=self._packetApprovedCallback, 
				args=(requestSocket, requestPacket, responses)
			).start()

		if isPacketApproved or isPacketDisapproved:
			self._donePacketHandler.add(packet.uuid)
			del self._packetWaitingApprovation[packet.uuid]

		packetWaiter['lock'].release()

	def _isValidPacket(self, socket, packet):
		valid = True
		approvationGroup = packet.action.approvationGroup
		if ((approvationGroup == ActionGroup.ROOM_PLAYERS or
				approvationGroup == ActionGroup.ROOM_OWNER) and  
				packet.params[ActionParam.ROOM_ID] not in self._rooms):
			valid = False
		
		if not valid:
			print(f'Game Packet invalid arrived from {socket} was ignored.')
		
		return valid	

	def _isSocketInApprovationGroup(self, socket, packet):
		result = None
		approvationGroup = packet.action.approvationGroup
		if approvationGroup == ActionGroup.NONE:
			result = False
		elif approvationGroup == ActionGroup.ALL_NETWORK:
			result = True
		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			room = self._rooms.get(packet.params[ActionParam.ROOM_ID], None)
			result = bool(room and socket.ip in room.players)
		elif approvationGroup == ActionGroup.ROOM_OWNER:
			result = room = self._rooms.get(packet.params[ActionParam.ROOM_ID], None)
			result = bool(room and socket is room.owner)
		return result

	def _testPacketConditions(self, socket, packet):
		for conditions in packet.action.conditions:
			actionError = conditions(self._network, socket, self._rooms, self._sharedGameData, packet.params)
			if actionError != ActionError.NONE:
				return actionError
		return ActionError.NONE

	def _approvationRequirement(self, socket, packet):
		totalNeeded = None
		fullGroup = set()
		approvationGroup = packet.action.approvationGroup

		if approvationGroup == ActionGroup.ALL_NETWORK:
			totalNeeded = len(self._network.allNetwork) // 2 + 1
			fullGroup = {socket for socket in self._network.allNetwork.values()}

		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			roomPlayers = self._rooms[packet.params[ActionParam.ROOM_ID]].players
			totalNeeded = len(roomPlayers) // 2 + 1
			fullGroup = {socket for socket in roomPlayers.values()}

		elif approvationGroup == ActionGroup.NONE:
			totalNeeded = 2
			fullGroup = {socket for socket in self._network.allNetwork.values()}

		elif approvationGroup == ActionGroup.ROOM_OWNER:
			room = self._rooms[packet.params[ActionParam.ROOM_ID]]
			totalNeeded = 1
			fullGroup = {room.owner}

		return totalNeeded, fullGroup


	def _isPacketApproved(self, socket, testPacket):
		packet = self._packetWaitingApprovation[testPacket.uuid]['request_packet']

		if not packet:
			return False 

		agreementsList = self._packetWaitingApprovation[packet.uuid]['agreements_list']
		totalNeeded, fullGroup = self._approvationRequirement(socket, packet)
		totalApprovation = {socket for socket in agreementsList if socket in fullGroup}

		return len(totalApprovation) >= totalNeeded

	def _isPacketDisapproved(self, socket, testPacket):
		packet = self._packetWaitingApprovation[testPacket.uuid]['request_packet']

		if not packet:
			return False 

		disagreementsList = self._packetWaitingApprovation[packet.uuid]['disagreements_list']
		totalNeeded, fullGroup = self._approvationRequirement(socket, packet)
		totalDisaprovation = {socket for socket in disagreementsList if socket in fullGroup}

		return len(fullGroup) - len(totalDisaprovation) < totalNeeded 



if __name__ == '__main__':
	interfaces = getAllIpAddress()
	print('Interface disponíveis: ')
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('\nSelecione a interface: '))
	game = Game(interfaces[number_interface])
	game.start()

	while True: pass
