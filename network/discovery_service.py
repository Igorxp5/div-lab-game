import sys
import time
import socket
import logging

from threading import Thread, Lock

class DiscoveryService(Thread):
	ENCODING = 'ascii'
	HEADER_FIRST_LINE = b'DIVLABGAME-DISCOVERY\r\n'
	MULTICAST_IP = '224.0.0.1'
	DEFAULT_DISCOVER_TIMEOUT = 7

	def __init__(self, discoveryAddress, tcpAddress):
		Thread.__init__(self, daemon=True)
		self._discoveryAddress = discoveryAddress
		self._tcpAddress = tcpAddress
		self._server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		multicast = socket.inet_aton(DiscoveryService.MULTICAST_IP) + socket.inet_aton(self._discoveryAddress[0])
		self._server.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast)

		self._waitServerStartLock = Lock()
		self._waitServerStartLock.acquire()

	def run(self):
		self._bindSocket()
		
		logging.info(f'Serviço de Descoberta incializado em {self._discoveryAddress}...')
		
		self._waitServerStartLock.release()
		
		while True:
			message, client = self._server.recvfrom(1024)
			if client[0] != self._discoveryAddress[0]:
				if message[:len(DiscoveryService.HEADER_FIRST_LINE)] == DiscoveryService.HEADER_FIRST_LINE:
					headers = DiscoveryService._discoveryParser(message)

					if headers['TYPE'] == 'DISCOVERY':
						response = self._discoveryResponse()
						self._server.sendto(response, client)

		self._server.close()

	def discover(self, timeout=DEFAULT_DISCOVER_TIMEOUT):
		self._waitServerStartLock.acquire()
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		client.bind((self._discoveryAddress[0], 0))
		address = DiscoveryService.MULTICAST_IP, self._discoveryAddress[1]
		message = self._discoveryRequest()
		client.sendto(message, address)
		
		addresses = []
		start_time = time.clock()
		while time.clock() - start_time < timeout:
			client.settimeout(timeout)
			try:
				message, from_ = client.recvfrom(1024)
			except socket.timeout:
				client.settimeout(None)
				return addresses
			headers = self._discoveryParser(message)
			address = tuple(headers['HOST'].split(':'))
			address = address[0], int(address[1])
			addresses.append(address)

		client.close()

		# Remover próprio endereço
		return addresses

	def _bindSocket(self):
		if sys.platform.startswith('win'):
			self._server.bind(self._discoveryAddress)
		else:
			self._server.bind(('0.0.0.0', self._discoveryAddress[1]))

	def _discoveryRequest(self):
		request = DiscoveryService.HEADER_FIRST_LINE
		ip, port = self._tcpAddress
		request += f'TYPE: DISCOVERY\r\nHOST: {ip}:{port}\r\n\r\n'.encode(DiscoveryService.ENCODING)
		return request

	def _discoveryResponse(self):
		response = DiscoveryService.HEADER_FIRST_LINE
		ip, port = self._tcpAddress
		response += f'TYPE: RUNNING-APP\r\nHOST: {ip}:{port}\r\n\r\n'.encode(DiscoveryService.ENCODING)
		return response

	@staticmethod
	def _discoveryParser(message):
		message = message[len(DiscoveryService.HEADER_FIRST_LINE):]
		headers = message.decode(DiscoveryService.ENCODING).split('\r\n')
		headers = [header for header in headers if header]
		headers = [header.split(': ') for header in headers]
		headers = {header: value for header, value in headers}

		return headers

if __name__ == '__main__':
	discoveryAddress = '25.8.61.75', 8400
	tcpAddress = '25.8.61.75', 8401

	discoveryService = DiscoveryService(discoveryAddress, tcpAddress)
	discoveryService.start()

	discovers = discoveryService.discover()
	print(discovers)

	while True: pass