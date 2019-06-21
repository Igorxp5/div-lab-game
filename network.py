import socket
from threading import Thread

class DiscoveryService(Thread):
	HEADER_FIRST_LINE = b'DIVLABGAME-DISCOVERY\r\n'

	def __init__(self, discoveryAddress, tcpAddress):
		Thread.__init__(self, daemon=True)
		self._discoveryAddress = discoveryAddress
		self._tcpAddress = tcpAddress
		self._server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def run(self):
		self._server.bind(self._discoveryAddress)
		print(f'Serviço de Descoberta em {self._discoveryAddress}...')
		while True:
			message, client = self._server.recvfrom(1024)

			if message[:len(DiscoveryService.HEADER_FIRST_LINE)] == DiscoveryService.HEADER_FIRST_LINE:
				headers = DiscoveryService.discoveryParser(message)

				if headers['TYPE'] == 'DISCOVERY':
					response = self._discoveryResponse()
					self._server.sendto(response, client)

	def _discoveryResponse(self):
		response = DiscoveryService.HEADER_FIRST_LINE
		ip, port = self._tcpAddress
		response += f'TYPE: RUNNING-APP\r\nHOST: {ip}:{port}\r\n\r\n'.encode('ascii')
		return response

	@staticmethod
	def discoveryParser(message):
		message = message[len(DiscoveryService.HEADER_FIRST_LINE):]
		headers = message.decode('utf-8').split('\r\n')
		headers = [header for header in headers if header]
		headers = [header.split(': ') for header in headers]
		headers = {header: value for header, value in headers}

		return headers

discoveryAddress = '25.8.61.75', 8400
tcpAddress = '25.8.61.75', 8401

discoveryService = DiscoveryService(discoveryAddress, tcpAddress)
discoveryService.start()

while True: pass