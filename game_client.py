import time

from network.network import Network
from network.packet import PacketRequest, PacketResponse, PacketType
from network.action import Action, ActionGroup, ActionParam

from utils.data_structure import IdTable
from utils.network_interfaces import getAllIpAddress

from threading import Thread
from datetime import datetime

class SharedGameData:
	def __init__(self):
		self.room 				= None
		self.masterRoom 		= None
		self.roundWord 			= None
		self.gamePhase 			= None

		self.players 			= IdTable()
		self.chosenWords 		= []
		self.masterRoomVotes 	= []
		self.contestAnswerVotes = []
		self.roundAnswers 		= []
		
		self.roundNumber 		= 0
		self.timePhase 			= 0


	@staticmethod
	def parseJson(json_data):
		sharedGameData = SharedGameData()
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
			from _game_controller_test import gameController
			gameController(self)

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

		if packet.packetType == PacketType.REQUEST:
			self._savePacketRequestWaiter(socket, packet)
			approvation = self._testPacket(socket, packet)
			packetResponse = PacketResponse(packet.action, approvation, uuid=packet.uuid)
			self._sendPacket(packetResponse)

		elif packet.packetType == PacketType.RESPONSE:
			approved_list = self._packetWaitingApprovation[packet.uuid]['agreements_list']
			if not packet.approved:
				approved_list = self._packetWaitingApprovation[packet.uuid]['disagreements_list']
			approved_list.append(socket)

		agreements_list = self._packetWaitingApprovation[packet.uuid]['agreements_list']
		if len(agreements_list) >= (len(self._network.peers) // 2) + 1:
			requestPacket = self._packetWaitingApprovation[packet.uuid]['request_packet']
			self._packetApprovedCallback(socket, requestPacket)

	def _testPacket(self, socket, packet):
		for conditions in packet.action.conditions:
			if not conditions(self._network, socket, self._rooms, self._sharedGameData, packet.params):
				return False
		return True


if __name__ == '__main__':
	interfaces = getAllIpAddress()
	print('Interface disponíveis: ')
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('\nSelecione a interface: '))
	game = Game(interfaces[number_interface])
	game.start()

	while True: pass
