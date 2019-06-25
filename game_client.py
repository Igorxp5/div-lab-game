import time

from network.network import Network
from network.packet import PacketRequest
from network.action import Action, ActionGroup, ActionParam

from utils.data_structure import IdTable
from utils.network_interfaces import getAllIpAddress

from threading import Thread

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

	def __init__(self, address):
		super().__init__(daemon=True)
		self._discoveryAddress = address, Game.DISCOVERY_PORT
		self._tcpAddress = address, Game.TCP_SERVER_PORT

		self._network = Network(self._discoveryAddress, self._tcpAddress)
		self._network.setListenPacketCallback(self._listenPacketCallback)
		self._listenPacketCallbackByAction = {}

		self._rooms = []

		self._sharedGameData = None
		self._receiverGroupIps = {}

	def createRoom(self, name, limit):
		params = {
			ActionParam.ROOM_NAME: name,
			ActionParam.PLAYERS_LIMIT: str(limit)
		}
		packet = PacketRequest(Action.CREATE_ROOM, params)
		self._sendPacket(packet)

	def run(self):
		self._network.start()
		self._network.blockUntilConnectToNetwork()

		while True:
			input('Tecle Enter para recarregar o Packet Sender...\n')
			from _game_controller_test import gameController
			gameController(self)

	def setListenPacketCallbackByAction(self, action, callback):
		if not is_instance(action, Action):
			raise TypeError('action must be a Action Enum.')
		
		if not action in self._listenPacketCallbackByAction:
			self._listenPacketCallbackByAction[action] = []

		self._listenPacketCallbackByAction[action].append(callback)

	def removeListenPacketCallbackByAction(self, action, callback):
		if not is_instance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].remove(callback)


	def _listenPacketCallback(self, socket, packet):
		if packet.action == Action.CREATE_ROOM:
			name = packet.params[ActionParam.ROOM_NAME]
			limit = packet.params[ActionParam.PLAYERS_LIMIT]
			print(socket.ip, f'tentou criar uma sala - Nome: {name} | Limite: {limit}')
		
		if packet.action in self._listenPacketCallbackByAction:
			for callback in self._listenPacketCallbackByAction[packet.action]:
				callback() 
			

	def _sendPacket(self, packet):
		self._network.sendPacket(packet, self._receiverGroupIps)


if __name__ == '__main__':
	interfaces = getAllIpAddress()
	print('Interface disponíveis: ')
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('\nSelecione a interface: '))
	game = Game(interfaces[number_interface])
	game.start()

	while True: pass
