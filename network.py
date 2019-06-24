import socket

from network_discovery_service import DiscoveryService
from network_packet import Packet, PacketRequest, PacketResponse, PacketType

from threading import Thread, Event

class Network(Thread):
	MAX_LISTEN = 30
	DISCOVERY_TIMEOUT = 3

	def __init__(self, discoveryAddress, tcpAddress):
		super().__init__(daemon=True)
		self._discoveryAddress = discoveryAddress
		self._tcpAddress = tcpAddress

		self._discoveryService = DiscoveryService(discoveryAddress, tcpAddress)
		self._tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.shutdownFlag = Event()

		self._connections = {}
		self._listenThreads = {}


	def run(self):
		self._discoveryService.start()

		self._discoveryAndConnectPeers()
		self._bindTcpServer()

	def _discoveryAndConnectPeers(self):
		addresses = self._discoveryService.discover(Network.DISCOVERY_TIMEOUT)
		addresses.append(('25.8.118.125', 8401))
		print(f'Descoberto {len(addresses)} endereços IP. Tentando contactá-los...')
		for address in addresses:
			Thread(target=self._connectToPeer, args=(address,), daemon=True).start()

	def _connectToPeer(self, address):
		tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			tcpClient.connect(address)

			conn_client = tcpClient, address
			
			self._connections[client] = tcpClient
			thread = Thread(target=self.listenConnection, args=conn_client, daemon=True)
			self._listenThreads[client] = thread
			thread.start()
		except TimeoutError:
			print(f'Não foi possível conectar-se a {address}')

	def _bindTcpServer(self):
		self._tcpServer.bind(self._tcpAddress)
		self._tcpServer.listen(Network.MAX_LISTEN)

		while not self.shutdownFlag.is_set():
			conn_client = self._tcpServer.accept()
			connection, client = conn_client
			self._connections[client] = connection
			thread = Thread(target=self.listenConnection, args=conn_client)
			self._listenThreads[client] = thread
			thread.start()

	def listenConnection(self, connection, client):
		print('Conectado a', client)


discoveryAddress = '25.8.61.75', 8400
tcpAddress = '25.8.61.75', 8401
network = Network(discoveryAddress, tcpAddress)
network.start()

while True: pass