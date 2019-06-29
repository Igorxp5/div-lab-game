import time

from network.network import Network
from network.packet import PacketRequest, PacketResponse, PacketType, InvalidPacketError
from network.action import Action, ActionGroup, ActionParam

from utils.data_structure import JsonSerializable
from utils.network_interfaces import getAllIpAddress

from network.game.room import Room, RoomStatus, GamePhase
from network.game.player import Player, PlayerStatus, PlayerAnswer
from network.game.word import Word

from threading import Thread
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

		self._rooms = []
		self._sharedGameData = None
		self._receiverGroupIps = {}

		# Adicionando callbacks para os tipos de pacotes
		self._listenPacketCallbackByAction = {action: [] for action in Action}
		self._listenPacketCallbackByAction[Action.CREATE_ROOM].append(self._createRoomCallback)

		self._packetWaitingApprovation = {}

	def createRoom(self, name, limit):
		params = {
			ActionParam.ROOM_NAME: name,
			ActionParam.PLAYERS_LIMIT: limit
		}
		packet = PacketRequest(Action.CREATE_ROOM, params)
		self._sendPacketRequest(packet)

	def run(self):
		self._network.start()
		self._network.blockUntilConnectToNetwork()

		while True:
			input('Tecle Enter para recarregar o Game Controller...\n')
			try:
				reload(_game_controller_test)
				_game_controller_test.gameController(self)
			except Exception as exception:
				print(exception)

	def setListenPacketCallbackByAction(self, action, callback):
		if not is_instance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].append(callback)

	def removeListenPacketCallbackByAction(self, action, callback):
		if not is_instance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].remove(callback)


	def _listenPacketCallback(self, socket, packet):
		self._waiterHandler(socket, packet)

	def _packetApprovedCallback(self, socket, packet):
		if packet.action in self._listenPacketCallbackByAction:
			for callback in self._listenPacketCallbackByAction[packet.action]:
				callback(socket, packet.params)

	def _createRoomCallback(self, socket, params):
		name = params[ActionParam.ROOM_NAME]
		limit = params[ActionParam.PLAYERS_LIMIT]
		print(f'O {socket} criou a sala {repr(name)} (Limite: {limit})')
			

	def _sendPacketRequest(self, packet):
		self._sendPacket(packet)
		self._createPacketWaiter(packet)
		self._savePacketRequestWaiter(self._network.socket, packet)

	def _sendPacket(self, packet):
		self._network.sendPacket(packet, self._receiverGroupIps)

	def _createPacketWaiter(self, packet):
		if packet.uuid not in self._packetWaitingApprovation:
			self._packetWaitingApprovation[packet.uuid] = {
				'request_socket': None,
				'request_packet': None,
				'agreements_list': [],
				'disagreements_list': [],
				'first_packet_time': datetime.now()
			}

	def _savePacketRequestWaiter(self, socket, packet):
		self._packetWaitingApprovation[packet.uuid]['request_socket'] = socket
		self._packetWaitingApprovation[packet.uuid]['request_packet'] = packet
		self._packetWaitingApprovation[packet.uuid]['agreements_list'].append(
			socket
		)

	def _waiterHandler(self, socket, packet):
		if packet.action.approvationGroup == ActionGroup.ONE_PLAYER:
			self._callback(socket, packet)
			return

		self._createPacketWaiter(packet)

		packetResponse = None
		approvationSocket  = None
		if packet.packetType == PacketType.REQUEST:
			self._savePacketRequestWaiter(socket, packet)
			approvation = self._testPacketConditions(socket, packet)
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
			request_socket = self._packetWaitingApprovation[packet.uuid]['request_socket']
			self._packetApprovedCallback(request_socket, requestPacket)

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
			totalApprovation = len([socket for socket in self._network.peers.values() if socket in agreementsList])
		
		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			if (not self._sharedGameData.room or 
					self._sharedGameData.room.id != packet.params[ActionParam.ROOM_ID]):
				totalNeeded, totalApprovation = invalidPacket()
			else:
				roomPlayers  =self._sharedGameData.room.players
				totalNeeded = len(roomPlayers) // 2 + 1
				totalApprovation = len([player for player in self._network.peers.values() if player.socket in agreementsList])
		
		elif approvationGroup == ActionGroup.ONE_PLAYER:
			totalNeeded = 1
			totalApprovation = 1 if packet.params[ActionParam.SOCKET_IP] in agreementsList else 0

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
