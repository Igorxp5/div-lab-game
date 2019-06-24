from network.network import Network
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
		self._rooms = []

		self._sharedGameData = None

	def run(self):
		self._network.start()


if __name__ == '__main__':
	game = Game('25.8.61.75')
	game.start()

	while True: pass
