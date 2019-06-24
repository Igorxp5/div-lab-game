import socket as sock
import time

from network.network import Network
from network.packet import PacketRequest
from network.action import Action, ActionGroup, ActionParam
from utils.data_structure import IdTable

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
		self._network.setListenPacketCallback(self.listenPacketCallback)
		self._rooms = []

		self._sharedGameData = None

		self._receiverGroupIps = {}

	def listenPacketCallback(self, socket, packet):
		print(socket.ip, socket.port, packet)
		if packet.action == Action.CREATE_ROOM:
			name = packet.params[ActionParam.ROOM_NAME]
			limit = packet.params[ActionParam.PLAYERS_LIMIT]
			print(socket.ip, f'tentou criar uma sala - Nome: {name} | Limite: {limit}')

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

		time.sleep(5)

		# Somente Igor criar a sala
		if self._tcpAddress[0] == '25.8.61.75':
			self.createRoom('Sala de Teste', 30)

		while True:
			pass

	def _sendPacket(self, packet):
		self._network.sendPacket(packet, self._receiverGroupIps)


if __name__ == '__main__':
	interfaces = sock.gethostbyname_ex(sock.gethostname())[2]
<<<<<<< HEAD
	print('Selecione interface: ')
=======
	print('Interface disponíveis: ')
>>>>>>> p2p
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('Selecione a interface: '))
	game = Game(interfaces[number_interface])
	game.start()

	while True: pass
