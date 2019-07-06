import logging
import socket as sock

import network.config as CONFIG

from .game._socket import Socket
from .discovery_service import DiscoveryService
from .action import ActionGroup, InvalidActionParams
from .packet import Packet, PacketRequest, PacketResponse, PacketType, InvalidPacketError

from datetime import datetime
from threading import Thread, Event, Lock, current_thread

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

		self._connectingPeerThreads = []
		self._blockUntilConnectToNetwork = Event()

		self._connections = {}
		self._listenThreads = {}

		self._listenPacketCallback = None
		self._disconnectSocketCallback = None

	@property
	def socket(self):
		return self._socket
	
	@property
	def peers(self):
		return {ip: socket for ip, socket in self._connections.items()}

	@property
	def allNetwork(self):
		return {**self.peers, self.socket.ip: self.socket}
	
	def run(self):
		self._discoveryService.start()

		self._discoveryAndConnectPeers()
		self._bindTcpServer()

	def setListenPacketCallback(self, listenCallback):
		self._listenPacketCallback = listenCallback

	def removeListenPacketCallback(self):
		self._listenPacketCallback = None		

	def setDisconnectCallback(self, callback):
		self._disconnectSocketCallback = callback

	def removeDisconnectCallback(self):
		self._disconnectSocketCallback = None

	def blockUntilConnectToNetwork(self):
		self._blockUntilConnectToNetwork.wait()

	def sendPacket(self, packet, toSocket=None, receiverGroupIps=tuple()):
		destination = []

		if toSocket:
			destination.append(toSocket)

		else:
			if packet.action.receiverGroup == ActionGroup.ALL_NETWORK:
				for ip, socket in self.allNetwork.items():
					destination.append(socket)
			else:
				group = receiverGroupIps.get(packet.action.receiverGroup, {})
				for ip, socket in group.items():
					destination.append(socket)

		for socket in destination:
			Thread(target=self._sendPacketToPeer, args=(socket, packet), daemon=True).start()		

		return len(destination)


	def _discoveryAndConnectPeers(self):
		addresses = self._discoveryService.discover(Network.DISCOVERY_TIMEOUT)

		logging.info(f'Descoberto {len(addresses)} endereços IP. Tentando contactá-los...')

		self._connectingPeerThreads = [None] * len(addresses)
		for address in addresses:
			thread = Thread(target=self._connectToPeer, args=(address,), daemon=True)
			thread.start()
			self._connectingPeerThreads.append(thread)
		
		if len(addresses) == 0:
			self._blockUntilConnectToNetwork.set()

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

		except (TimeoutError, ConnectionRefusedError):
			logging.warning(f'Não foi possível conectar-se a {address}!')

			if (any([not t.is_alive() for t in self._connectingPeerThreads if t]) and
					len(self._connections) > 0) and self._blockUntilConnectToNetwork.is_set():
				self._blockUntilConnectToNetwork.set()

		if current_thread() in self._connectingPeerThreads:
			self._connectingPeerThreads.remove(current_thread())

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
		logging.info(f'Conectado a {socket}.')

		if not self._blockUntilConnectToNetwork.is_set():
			self._blockUntilConnectToNetwork.set()

		while True:
			try:
				data = socket.connection.recv(Network.TCP_RECEIVE_BYTES)
			except ConnectionResetError:
				data = None

			if not data:
				break

			self._handleRecvData(socket, data)
			

		self._disconnectFromSocket(socket)

	def _handleRecvData(self, socket, data):
		try:
			packet = Packet.parse(data)

			if self._listenPacketCallback:
				self._listenPacketCallback(socket, packet)

		except InvalidPacketError:
			logging.error(f'Invalid Packet arrived from {socket} was ignored.')
			if CONFIG.SAVE_LOG_INVALID_PACKETS:
				self._saveLogPacket(socket, packet)
		except InvalidActionParams:
			logging.error(f'A Packet arrived with wrong ActionParams from {socket} was ignored.')
			if CONFIG.SAVE_LOG_INVALID_PACKETS:
				self._saveLogPacket(socket, packet)

	def _disconnectFromSocket(self, socket):
		socket.connection.close()
		del self._connections[socket.ip]
		del self._listenThreads[socket.ip]

		logging.info(f'Desconectado de {socket}.')

		if self._disconnectSocketCallback:
			self._disconnectSocketCallback(socket)

	def _sendPacketToPeer(self, socket, packet):
		if socket is self.socket:
			self._handleRecvData(socket, packet.toBytes())
		else:
			socket.connection.send(packet.toBytes())

	def _saveLogPacket(self, socket, packet):
		with open(CONFIG.LOG_INVALID_PACKETS_FILENAME, 'a') as file:
			file.write(f'From socket {socket} to {self.socket} at ({datetime.now()})\n')
			file.write(str(packet))


if __name__ == '__main__':
	discoveryAddress = '25.8.61.75', 8400
	tcpAddress = '25.8.61.75', 8401
	network = Network(discoveryAddress, tcpAddress)
	network.start()

	while True: pass