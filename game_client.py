import json
import time
import traceback # TODO: Remover no final do projeto

from network.network import Network
from network.packet import PacketRequest, PacketResponse, PacketType, InvalidPacketError
from network.action import Action, ActionGroup, ActionParam, ActionRw

from utils.data_structure import JsonSerializable
from utils.network_interfaces import getAllIpAddress

from network.game.room import Room, RoomStatus, GamePhase
from network.game.player import Player, PlayerStatus, PlayerAnswer
from network.game.word import Word

from threading import Thread, Event
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
		self.phaseTime 			= 0

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

		self._packetWaitingApprovation = {}

		self._waitDownloadListRooms = Event()

	@property
	def _receiverGroupIps(self):
		receiverGroupIps = {
			ActionGroup.ROOM_PLAYERS: {},
			ActionGroup.ROOM_OWNER: {}
		}
		if self._sharedGameData.room:
			receiverGroupIps[ActionGroup.ROOM_PLAYERS] = (
				{player.soscket.ip: player.socket for player in self._sharedGameData.room.players}
			)
			receiverGroupIps[ActionGroup.ROOM_OWNER] = {
				self._sharedGameData.room.owner.ip: self._sharedGameData.room.owner
			}
		return receiverGroupIps

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

	def createRoom(self, name, limitPlayers):
		room = Room.createRoom(name, limitPlayers, self._network._socket)
		params = {
			ActionParam.ROOM_ID: room.id,
			ActionParam.ROOM_NAME: room.name,
			ActionParam.PLAYERS_LIMIT: room.limitPlayers
		}
		packet = PacketRequest(Action.CREATE_ROOM, params)
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

	def _packetApprovedCallback(self, socket, packet):
		if packet.action in self._listenPacketCallbackByAction:
			for callback in self._listenPacketCallbackByAction[packet.action]:
				callback(socket, packet.params)

	def _actionReadPacketCallback(self, socket, packet):
		if packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketRequest):
			content = {id_: room.toJsonDict() for id_, room in self._rooms.items()}
			packet = PacketResponse(packet.action, True, content, uuid=packet.uuid)
			self._sendPacket(packet, toSocket=socket)	
		
		elif packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketResponse):
			self._getListRoomsCallback(socket, packet.content)

	def _createRoomCallback(self, socket, params):
		id_ = params[ActionParam.ROOM_ID]
		name = params[ActionParam.ROOM_NAME]
		limitPlayers = params[ActionParam.PLAYERS_LIMIT]
		room = Room(
			id_, name, limitPlayers, socket, [], RoomStatus.ON_HOLD
		)
		self._rooms[id_] = room
		print(f'O {socket} criou a sala {repr(name)} (Limite: {limitPlayers})')

	def _getListRoomsCallback(self, socket, content):
		if content is not None:
			for id_, room in content.items():
				roomJsonData = json.dumps(room)
				sockets = {**self._network.peers, self._network._socket.ip: self._network._socket}
				self._rooms[id_] = Room.parseJson(roomJsonData, sockets)
		else:
			print(f'Não foi possível obter a lista de salas!')

	def _sendPacketRequest(self, packet, toSocket=None):
		self._sendPacket(packet, toSocket)
		self._createPacketWaiter(packet)
		self._savePacketRequestWaiter(self._network.socket, packet)

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
				'agreements_list': [],
				'disagreements_list': [],
				'first_packet_time': datetime.now()
			}

	def _savePacketRequestWaiter(self, socket, packet, checkApprovation=True):
		self._packetWaitingApprovation[packet.uuid]['request_socket'] = socket
		self._packetWaitingApprovation[packet.uuid]['request_packet'] = packet
		self._packetWaitingApprovation[packet.uuid]['agreements_list'].append(
			socket
		)

		if checkApprovation and self._isPacketApproved(packet):
			requestPacket = self._packetWaitingApprovation[packet.uuid]['request_packet']
			requestSocket = self._packetWaitingApprovation[packet.uuid]['request_socket']
			self._packetApprovedCallback(requestSocket, requestPacket)

	def _waiterHandler(self, socket, packet):
		self._createPacketWaiter(packet)

		packetResponse = None
		approvationSocket  = None
		if packet.packetType == PacketType.REQUEST:
			self._savePacketRequestWaiter(socket, packet)
			approvation = self._testPacketConditions(socket, packet, False)
			packetResponse = PacketResponse(packet.action, approvation, uuid=packet.uuid)
			approvationSocket = self._network._socket
			self._sendPacket(packetResponse)

		elif packet.packetType == PacketType.RESPONSE:
			packetResponse = packet
			approvationSocket = socket

		approvationList = self._packetWaitingApprovation[packet.uuid]['agreements_list']
		if not packetResponse.approved:
			approvationList = self._packetWaitingApprovation[packet.uuid]['disagreements_list']
		approvationList.append(approvationSocket)

		if self._isPacketApproved(packet):
			requestPacket = self._packetWaitingApprovation[packet.uuid]['request_packet']
			requestSocket = self._packetWaitingApprovation[packet.uuid]['request_socket']
			self._packetApprovedCallback(requestSocket, requestPacket)

	def _testPacketConditions(self, socket, packet):
		for conditions in packet.action.conditions:
			if not conditions(self._network, socket, self._rooms, self._sharedGameData, packet.params):
				return False
		return True

	def _isPacketApproved(self, packet):
		agreementsList = self._packetWaitingApprovation[packet.uuid]['agreements_list']
		approvationGroup = packet.action.approvationGroup
		totalNeeded = None
		totalApprovation = None

		def invalidPacket():
			print(f'Game Packet invalid arrived from {packet.socket} was ignored.')
			return float('inf'), 0

		if approvationGroup == ActionGroup.ALL_NETWORK:
			totalNeeded = len(self._network.peers) // 2 + 1
			totalApprovation = [socket for socket in self._network.peers.values() if socket in agreementsList]
			totalApprovation += [self._network._socket]
			totalApprovation = len(totalApprovation)

		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			if (not self._sharedGameData.room or 
					self._sharedGameData.room.id != packet.params[ActionParam.ROOM_ID]):
				totalNeeded, totalApprovation = invalidPacket()
			else:
				roomPlayers  =self._sharedGameData.room.players
				totalNeeded = len(roomPlayers) // 2 + 1
				totalApprovation = len([player for player in self._network.peers.values() if player.socket in agreementsList])
		
		elif approvationGroup == ActionGroup.NONE:
			totalNeeded = 2
			totalApprovation = len(agreementsList)

		elif approvationGroup == ActionGroup.ROOM_OWNER:
			if (not self._sharedGameData.room or 
					self._sharedGameData.room.id != packet.params[ActionParam.ROOM_ID]):
				totalNeeded, totalApprovation = invalidPacket()
			totalNeeded = 1
			totalApprovation = 1 if self._sharedGameData.roomMaster.socket.ip in agreementsList else 0

		return totalApprovation >= totalNeeded


if __name__ == '__main__':
	interfaces = getAllIpAddress()
	print('Interface disponíveis: ')
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('\nSelecione a interface: '))
	game = Game(interfaces[number_interface])
	game.start()

	while True: pass
