import socket as sock

from .game._socket import Socket
from .action import ActionGroup
from .discovery_service import DiscoveryService
from .packet import Packet, PacketRequest, PacketResponse, PacketType

from threading import Thread, Event, Lock

class Network(Thread):
	MAX_LISTEN = 30
	DISCOVERY_TIMEOUT = 3
	TCP_RECEIVE_BYTES = 2**16

	def __init__(self, discoveryAddress, tcpAddress):
		super().__init__(daemon=True)
		self._discoveryAddress = discoveryAddress
		self._tcpAddress = tcpAddress

		self._discoveryService = DiscoveryService(discoveryAddress, tcpAddress)
		self._tcpServer = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

		self._socket = Socket(self._tcpAddress[0], self._tcpAddress[1], self._tcpServer)

		self._blockUntilConnectToNetwork = Lock()

		self._connections = {}
		self._listenThreads = {}

		self._listenPacketCallback = None

		self._blockUntilConnectToNetwork.acquire()

	@property
	def socket(self):
		return self._socket

	@property
	def peers(self):
		return {ip: socket for ip, socket in self._connections.items()}
	
	def run(self):
		self._discoveryService.start()

		self._discoveryAndConnectPeers()
		self._bindTcpServer()

	def setListenPacketCallback(self, listenCallback):
		self._listenPacketCallback = listenCallback

	def blockUntilConnectToNetwork(self):
		self._blockUntilConnectToNetwork.acquire()
		self._blockUntilConnectToNetwork.release()

	def sendPacket(self, packet, receiverGroupIps):
		if packet.action.receiverGroup == ActionGroup.ALL_NETWORK:
			for ip, socket in self._connections.items():
				Thread(target=self._sendPacketToPeer, args=(socket, packet), daemon=True).start()
		else:
			for ip, socket in receiverGroupIps[packet.action.receiverGroup].items():
				Thread(target=self._sendPacketToPeer, args=(socket, packet), daemon=True).start()

	def _discoveryAndConnectPeers(self):
		addresses = self._discoveryService.discover(Network.DISCOVERY_TIMEOUT)
		print(f'Descoberto {len(addresses)} endereços IP. Tentando contactá-los...')
		for address in addresses:
			Thread(target=self._connectToPeer, args=(address,), daemon=True).start()
		self._blockUntilConnectToNetwork.release()

	def _connectToPeer(self, address):
		tcpClient = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
		try:
			tcpClient.connect(address)

			conn_client = tcpClient, address
			ip, port = address
			self._connections[ip] = Socket(ip, port, tcpClient)
			thread = Thread(target=self._listenConnection, args=(self._connections[ip],), daemon=True)
			self._listenThreads[ip] = thread
			thread.start()
		except TimeoutError:
			print(f'Não foi possível conectar-se a {address}')

	def _bindTcpServer(self):
		self._tcpServer.bind(self._tcpAddress)
		self._tcpServer.listen(Network.MAX_LISTEN)

		while True:
			conn_client = self._tcpServer.accept()
			connection, client = conn_client
			ip, port = client
			self._connections[ip] = Socket(ip, port, connection)
			thread = Thread(target=self._listenConnection, args=(self._connections[ip],), daemon=True)
			self._listenThreads[ip] = thread
			thread.start()

	def _listenConnection(self, socket):
		print('Conectado a', socket.ip, socket.port)

		while True:
			try:
				data = socket.connection.recv(Network.TCP_RECEIVE_BYTES)
			except ConnectionResetError:
				data = None

			if not data:
				break
			
			packet = Packet.parse(data)

			if self._listenPacketCallback:
				self._listenPacketCallback(socket, packet)

		self._disconnectFromSocket(socket)

	def _disconnectFromSocket(self, socket):
		socket.connection.close()
		del self._connections[socket.ip]
		del self._listenThreads[socket.ip]
		print(f'Desconectado de {socket}')

	def _sendPacketToPeer(self, socket, packet):
		socket.connection.send(packet.toBytes())

if __name__ == '__main__':
	discoveryAddress = '25.8.61.75', 8400
	tcpAddress = '25.8.61.75', 8401
	network = Network(discoveryAddress, tcpAddress)
	network.start()

	while True: pass