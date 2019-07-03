import json
import time
import traceback # TODO: Remover no final do projeto

import network.config as CONFIG

from network.network import Network
from network.packet import PacketRequest, PacketResponse, PacketType, InvalidPacketError
from network.action import Action, ActionGroup, ActionParam, ActionRw, ActionError

from utils.data_structure import JsonSerializable
from utils.network_interfaces import getAllIpAddress
from utils.countdown import Countdown

from network.game.room import Room, RoomStatus, GamePhase
from network.game.player import Player, PlayerStatus, PlayerAnswer
from network.game.word import Word

from threading import Thread, Event, Lock
from datetime import datetime
from importlib import reload

import _game_controller_test

class GameActionError(RuntimeError):
	def __init__(self, actionError):
		self.actionError = actionError
		super().__init__(actionError.message)

class SharedGameData(JsonSerializable):
	def __init__(self):
		self.room 					= None
		self.roundMaster 			= None
		self.roundWord 				= None
		self.gamePhase 				= None

		self.wantedRoundMasterWord	= None 
		self.wantedPlayerWord 		= None 

		self.chosenWords 			= []
		self.roundMasterVotes 		= {}
		self.electingOut 			= {}
		self.contestingVotes 		= {}
		self.roundAnswers 			= {}
		self.contestingPlayer 		= None
		self.roundPlayersEliminated = []
		
		self.roundNumber 			= 0
		self._phaseTimeStart 		= None
		self._phaseTimeDesired  	= 0

		self._changingGamePhaseCallback = None

		self._countdowns = {}

	@property
	def phaseTime(self):
		return self._phaseTimeDesired - ((datetime.now() - self._phaseTimeStart).seconds)

	@phaseTime.setter
	def phaseTime(self, countdown):
		self._phaseTimeDesired = countdown
		self._phaseTimeStart = datetime.now()

	def setGamePhase(self, gamePhase):
		self.gamePhase = gamePhase
		if self._changingGamePhaseCallback:
			startThread(self._changingGamePhaseCallback, gamePhase)
		self._setRoomPlayersStatus(gamePhase)

	def setChangingGamePhaseCallback(self, callback):
		self._changingGamePhaseCallback = callback

	def _setRoomPlayersStatus(self, gamePhase):
		room = self.room
		roomPlayers = room.players
		for player in roomPlayers:
			if player.status not in (PlayerStatus.WATCHING, PlayerStatus.ELIMINATED):
				if gamePhase in (GamePhase.ELECTING_ROUND_MASTER, GamePhase.RELECTING_ROUND_MASTER):
					player.status = PlayerStatus.VOTING_ON_THE_ROUND_ORGANIZER
				elif gamePhase == GamePhase.CHOOSING_ROUND_WORD:
					if player is self.roundMaster:
						player.status = PlayerStatus.CHOOSING_THE_WORD_OF_THE_ROUND
					else:
						player.status = PlayerStatus.OUTSTANDING_ORGANIZER_CHOOSES_THE_WORD_OF_THE_ROUND
				elif gamePhase == GamePhase.WAITING_ANSWERS:
					if player is self.roundMaster:
						player.status = PlayerStatus.AWAITING_THE_END_OF_THE_SILABIC_DIVISION_PHASE
					else:
						player.status = PlayerStatus.RESPONDING_TO_SILABIC_DIVISION
				elif gamePhase == GamePhase.WAITING_CONTESTS:
					player.status = PlayerStatus.AWAITING_CONTESTATIONS
				elif gamePhase == GamePhase.ELECTING_CORRECT_ANSWER:
					if player is self.roundMaster or player is self.contestingPlayer:
						player.status = PlayerStatus.AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST
					else:
						player.status = PlayerStatus.VOTING_IN_CONTEST_OF_THE_CORRECT_WORD
				elif gamePhase == GamePhase.RESULT_ROUND:
					player.status = PlayerStatus.WAITING_FOR_NEXT_ROUND

	def _dictKeyProperty(self):
		return {
			'room': self.room,
			'roundMaster': self.roundMaster,
			'roundWord': self.roundWord,
			'gamePhase': self.gamePhase,
			'chosenWords': self.chosenWords,
			'electingOut': self.electingOut,
			'roundMasterVotes': {ip: votePlayer.socket for ip, votePlayer in self.roundMasterVotes.items()},
			'contestingVotes': {ip: votePlayer.socket for ip, votePlayer in self.contestingVotes.items()},
			'roundAnswers': self.roundAnswers,
			'roundNumber': self.roundNumber,
			'phaseTime': self.phaseTime
		}

	@staticmethod
	def _parseJson(jsonDict, sockets):
		sharedGameData = SharedGameData()
		
		roomJsonData = json.dumps(jsonDict['room'])
		sharedGameData.room = Room.parseJson(roomJsonData, sockets)

		roundMasterJsonData = json.dumps(jsonDict['roundMaster'])
		sharedGameData.roundMaster = Player.parseJson(roundMasterJsonData, sockets)

		roundWordJsonData = json.dumps(jsonDict['roundWord'])
		sharedGameData.roundWord = Word.parseJson(roundWordJsonData)

		sharedGameData.gamePhase = GamePhase.getByValue(jsonDict['gamePhase'])

		for ip, playerDict in jsonDict['electingOut']:
			playerJsonData = json.dumps(playerDict)
			player = Player.parseJson(
				playerAnswerJsonData, self._network.allNetwork
			)
			sharedGameData.electingOut[ip] = player

		for wordDict in jsonDict['chosenWords']:
			wordJsonData = json.dumps(wordDict)
			word = Word.parseJson(wordJsonData)
			sharedGameData.chosenWords.append(word)

		for ip, voteIp in jsonDict['roundMasterVotes']:
			sharedGameData.roundMasterVotes[ip] = sharedGameData.room.players[voteIp]

		for ip, voteIp in jsonDict['contestingVotes']:
			sharedGameData.roundMasterVotes[ip] = sharedGameData.room.players[voteIp]
		
		for ip, playerAnswerDict in jsonDict['roundAnswers']:
			playerAnswerJsonData = json.dumps(playerAnswerDict)
			playerAnswer = PlayerAnswer.parseJson(
				playerAnswerJsonData, sharedGameData.room.players
			)
			sharedGameData.roundAnswers[ip] = playerAnswer

		sharedGameData.roundNumber = jsonDict['roundNumber']
		sharedGameData.phaseTime = jsonDict['phaseTime']
		
		return sharedGameData


class GameClient(Thread):
	DISCOVERY_PORT = CONFIG.DISCOVERY_PORT
	TCP_SERVER_PORT = CONFIG.TCP_SERVER_PORT
	PACKET_WAITING_APPROVATION_QUEUE_SIZE = 30

	def __init__(self, address):
		super().__init__(daemon=True)
		self._discoveryAddress = address, GameClient.DISCOVERY_PORT
		self._tcpAddress = address, GameClient.TCP_SERVER_PORT

		self._network = Network(self._discoveryAddress, self._tcpAddress)
		self._network.setListenPacketCallback(self._listenPacketCallback)
		self._network.setDisconnectCallback(self._disconnectCallback)

		self._rooms = {}
		self._sharedGameData = None
		self._initSharedGameData()

		# Adicionando callbacks para os tipos de pacotes
		self._listenPacketCallbackByAction = {action: [] for action in Action}
		self._listenChangingGamePhaseCallback = None
		self._listenDisconnectSocketCallback = None
		self._registerDefaultListenCallbacks()

		self._packetWaitingApprovation = {}
		self._donePacketHandler = set()

		self._waitDownloadListRooms = Event()
		self._removePlayerFromRoomLock = Lock()

	@property
	def _receiverGroupIps(self):
		receiverGroupIps = {
			ActionGroup.ROOM_PLAYERS: {},
			ActionGroup.ROOM_OWNER: {}
		}
		if self._sharedGameData.room:
			receiverGroupIps[ActionGroup.ROOM_PLAYERS] = (
				{player.socket.ip: player.socket for player in self._sharedGameData.room.players}
			)
			receiverGroupIps[ActionGroup.ROOM_OWNER] = {
				self._sharedGameData.room.owner.ip: self._sharedGameData.room.owner
			}
		return receiverGroupIps

	@property
	def socket(self):
		return self._network.socket

	def run(self):
		self._network.start()
		self._network.blockUntilConnectToNetwork()

		if len(self._network.peers) > 0:
			self._waitDownloadListRooms.set()
			self.downloadListRooms()
			self._waitDownloadListRooms.wait()

		while True:
			input('Tecle Enter para recarregar o Game Controller...\n')
			try:
				reload(_game_controller_test)
				_game_controller_test.gameController(self)
			except Exception as exception:
				traceback.print_exc()

	def downloadListRooms(self):
		packet = PacketRequest(Action.GET_LIST_ROOMS)
		socketIp = list(self._network.peers)[0]
		socket = self._network.peers[socketIp]
		self._sendPacketRequest(packet, toSocket=socket)

	def createRoom(self, name, limitPlayers, playerName):
		room = Room.createRoom(name, limitPlayers, self.socket)
		params = {
			ActionParam.ROOM_ID: room.id,
			ActionParam.ROOM_NAME: room.name,
			ActionParam.PLAYERS_LIMIT: room.limitPlayers,
			ActionParam.PLAYER_NAME: playerName
		}

		self._raiseActionIfNotCondictions(Action.CREATE_ROOM, params)

		packet = PacketRequest(Action.CREATE_ROOM, params)
		self._sendPacketRequest(packet)
		return room

	def kickPlayerFromRoom(self, player):
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.SOCKET_IP: player.socket.ip,
		}

		self._raiseActionIfNotCondictions(Action.KICK_PLAYER_ROOM, params)
		packet = PacketRequest(Action.KICK_PLAYER_ROOM, params)
		self._sendPacketRequest(packet)


	def joinRoomToPlay(self, roomId, playerName):
		params = {
			ActionParam.ROOM_ID: roomId,
			ActionParam.PLAYER_NAME: playerName
		}

		self._raiseActionIfNotCondictions(Action.JOIN_ROOM_PLAY, params)

		packet = PacketRequest(Action.JOIN_ROOM_PLAY, params)
		self._sendPacketRequest(packet)

	def quitRoom(self):
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
		}

		self._raiseActionIfNotCondictions(Action.QUIT_ROOM, params)

		packet = PacketRequest(Action.QUIT_ROOM, params)
		self._sendPacketRequest(packet)

	def startGame(self):
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
		}

		self._raiseActionIfNotCondictions(Action.START_ROOM_GAME, params)

		packet = PacketRequest(Action.START_ROOM_GAME, params)
		self._sendPacketRequest(packet)

	def voteRoundMaster(self, votePlayer):
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.SOCKET_IP: votePlayer.socket.ip,
		}
		
		self._raiseActionIfNotCondictions(Action.CHOOSE_VOTE_ELECTION_ROUND_MASTER, params)
		
		packet = PacketRequest(Action.CHOOSE_VOTE_ELECTION_ROUND_MASTER, params)
		self._sendPacketRequest(packet)

	def chooseRoundWord(self, wordString, wordDivision):
		word = Word(wordString, wordDivision, True)

		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.WORD_STRING: word.wordStr,
			ActionParam.WORD_DIVISION: word.syllables
		}

		self._raiseActionIfNotCondictions(Action.CHOOSE_ROUND_WORD, params)

		packet = PacketRequest(Action.CHOOSE_ROUND_WORD, params)
		self._sendPacketRequest(packet)
		self._sharedGameData.wantedRoundMasterWord = word
		return word

	def answerRoundWord(self, wordDivision):
		roundWord = self._sharedGameData.roundWord
		answerWord = Word(getattr(roundWord, 'wordStr', ''), wordDivision, True)

		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.WORD_DIVISION: answerWord.syllables
		}

		self._raiseActionIfNotCondictions(Action.SEND_PLAYER_ANSWER, params)

		packet = PacketRequest(Action.SEND_PLAYER_ANSWER, params)
		self._sendPacketRequest(packet)
		self._sharedGameData.wantedPlayerWord = answerWord 
		return answerWord

	def contestCorrectAnswer(self):
		word = getattr(self._sharedGameData, 'wantedPlayerWord', None)
		wordGetNoHashSyllables = getattr(word, 'getNoHashSyllables', None)
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.WORD_DIVISION: wordGetNoHashSyllables() if callable(wordGetNoHashSyllables) else None
		}

		self._raiseActionIfNotCondictions(Action.CONTEST_WORD, params)

		packet = PacketRequest(Action.CONTEST_WORD, params)
		self._sendPacketRequest(packet)

	def voteCorrectAnswer(self, word):
		socketIp = None
		if word:
			if word is self.getRoundWord():
				socketIp = self.getRoundMaster().socket.ip
			elif word is self.getContestingWord():
				socketIp = self.getContestingPlayer().socket.ip
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.SOCKET_IP: socketIp
		}
		
		self._raiseActionIfNotCondictions(Action.CHOOSE_VOTE_CONTEST_ANSWER, params)
		
		packet = PacketRequest(Action.CHOOSE_VOTE_CONTEST_ANSWER, params)
		self._sendPacketRequest(packet)

	def getSocket(self, ip):
		return self._network.allNetwork.get(ip, None)

	def getAvailableRooms(self):
		return self._rooms

	def getRoom(self, roomId):
		return self._rooms.get(roomId, None)

	def getCurrentRoom(self):
		return self._sharedGameData.room

	def getCurrentPlayer(self):
		room = self.getCurrentRoom()
		if room:
			return room.getPlayer(self.socket)
		return None

	def getGamePhase(self):
		return self._sharedGameData.gamePhase

	def getPhaseTime(self):
		return self._sharedGameData.phaseTime

	def getRoundMaster(self):
		return self._sharedGameData.roundMaster

	def getContestingPlayer(self):
		return self._sharedGameData.contestingPlayer

	def getRoundNumber(self):
		return self._sharedGameData.roundNumber

	def getRoundWord(self):
		return self._sharedGameData.roundWord

	def getContestingWord(self):
		if self.getContestingPlayer():
			contestingPlayerSocketIp = self.getContestingPlayer().socket.ip
			return self._sharedGameData.roundAnswers.get(contestingPlayerSocketIp, None)
		return None

	def getElectingPlayers(self):
		if (self.getCurrentRoom() and 
				(self.getCurrentRoom().status == GamePhase.ELECTING_ROUND_MASTER or
				self.getCurrentRoom().status == GamePhase.RELECTING_ROUND_MASTER)):
			room = self.getCurrentRoom()
			roomPlayers = room.players
			return [p for p in roomPlayers if p.socket.ip not in self._sharedGameData.electingOut]
		return None

	def getMasterRoomVotes(self):
		room = self.getCurrentRoom()
		if room:
			return {room.getPlayer(self.getSocket(ip)): voterPlayer for ip, voterPlayer in self._sharedGameData.roundMasterVotes.items()}
		return None

	def isRoundMaster(self):
		return self._sharedGameData.room and self._sharedGameData.room.owner is self.socket

	def isEliminatedPlayer(self, player):
		return player.status == PlayerStatus.ELIMINATED

	def isWatchingPlayer(self, player):
		return player.status == PlayerStatus.WATCHING

	def isEliminatedOrWatchingPlayer(self, player):
		return player.status in (PlayerStatus.ELIMINATED, PlayerStatus.WATCHING)

	def setListenPacketCallbackByAction(self, action, callback):
		if not isinstance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].append(callback)

	def removeListenPacketCallbackByAction(self, action, callback):
		if not isinstance(action, Action):
			raise TypeError('action must be a Action Enum.')

		self._listenPacketCallbackByAction[action].remove(callback)

	def setChangingGamePhaseCallback(self, callback):
		self._listenChangingGamePhaseCallback = callback

	def removeChangingGamePhaseCallback(self):
		self._listenChangingGamePhaseCallback = None

	def setDisconnectCallback(self, callback):
		self._listenDisconnectSocketCallback = callback

	def removeDisconnectCallback(self):
		self._listenDisconnectSocketCallback = None

	def _initSharedGameData(self):
		self._sharedGameData = SharedGameData()
		self._sharedGameData.setChangingGamePhaseCallback(self._changingGamePhaseCallback)

	def _registerDefaultListenCallbacks(self):
		defaultListPacketCallbacks = {
			Action.GET_LIST_ROOMS: self._getListRoomsCallback,
			Action.CREATE_ROOM: self._createRoomCallback,
			Action.JOIN_ROOM_PLAY: self._joinRoomToPlayCallback,
			Action.KICK_PLAYER_ROOM: self._kickPlayerFromRoomCallback,
			Action.QUIT_ROOM: self._quitRoomCallback,
			Action.START_ROOM_GAME: self._startGameCallback,
			Action.CHOOSE_VOTE_ELECTION_ROUND_MASTER: self._chooseVoteElectionRoundMasterCallback,
			Action.CHOOSE_ROUND_WORD: self._chooseRoundWordCallback,
			Action.SEND_PLAYER_ANSWER: self._answerRoundWordCallback,
			Action.CONTEST_WORD: self._contestAnswerWordCallback,
			Action.SEND_MASTER_ANSWER: self._correctAnswerCallback,
			Action.CHOOSE_VOTE_CONTEST_ANSWER: self._chooseVoteContestAnswerCallback,
		}
		for action, callback in defaultListPacketCallbacks.items():
			self._listenPacketCallbackByAction[action].append(callback)

	def _listenPacketCallback(self, socket, packet):
		if packet.action.rw == ActionRw.READ:
			self._actionReadPacketCallback(socket, packet)

		elif packet.action.rw == ActionRw.WRITE:
			self._waiterHandler(socket, packet)

	def _packetApprovedCallback(self, socket, packet, responses):
		listResponses = list(responses.values())
		mostCommonPacketResponse = max(set(listResponses), key=listResponses.count)
		actionError = mostCommonPacketResponse.actionError

		if packet.action in self._listenPacketCallbackByAction:
			for callback in self._listenPacketCallbackByAction[packet.action]:
				callback(socket, packet.params, actionError)

		if actionError != ActionError.NONE:
			print(f'From {socket}: Erro #{actionError.code} - {actionError}')

	def _actionReadPacketCallback(self, socket, packet):
		if packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketRequest):
			content = {id_: room.toJsonDict() for id_, room in self._rooms.items()}
			packet = PacketResponse(packet.action, content=content, uuid=packet.uuid)
			self._sendPacket(packet, toSocket=socket)	
		
		elif packet.action == Action.GET_LIST_ROOMS and isinstance(packet, PacketResponse):
			self._getListRoomsCallback(socket, packet.content)

	def _getListRoomsCallback(self, socket, content):
		if content is not None:
			for id_, room in content.items():
				roomJsonData = json.dumps(room)
				self._rooms[id_] = Room.parseJson(roomJsonData, self._network.allNetwork)

	def _raiseActionIfNotCondictions(self, action, params):
		for condition in action.conditions:
			actionError = condition(
				self._network, self.socket, self._rooms, self._sharedGameData, params
			)
			if actionError != ActionError.NONE:
				raise GameActionError(actionError)


	def _createRoomCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			roomId = params[ActionParam.ROOM_ID]
			name = params[ActionParam.ROOM_NAME]
			limitPlayers = params[ActionParam.PLAYERS_LIMIT]
			playerName = params[ActionParam.PLAYER_NAME]
			room = Room(
				roomId, name, limitPlayers, socket, [], RoomStatus.ON_HOLD
			)
			room.joinPlayer(socket, playerName)
			self._rooms[roomId] = room
			print(f'O {socket} \'{playerName}\' criou a sala {repr(name)}({limitPlayers}). ({repr(roomId)})')

			if socket is self.socket:
				self._sharedGameData.room = room

	def _joinRoomToPlayCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			playerName = params[ActionParam.PLAYER_NAME]
			player = Player(playerName, socket, PlayerStatus.ON_HOLD)
			room.players.append(player)
			self._sharedGameData.room = room
			print(f'O {socket} entrou na sala \'{room.name}\' como \'{playerName}\'.')

			if len(room.players) == room.limitPlayers and room.owner is self.socket:
				self.startGame()

	def _kickPlayerFromRoomCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			bannedPlayer = room.getPlayer(self.getSocket(params[ActionParam.SOCKET_IP]))
			ownerPlayer = room.getPlayer(room.owner)
			room.banSocket(bannedPlayer.socket)
			self._roomPrint(f'\'{ownerPlayer.nickname}\' baniu \'{bannedPlayer.nickname}\' desta sala.')
			self._removeSocketFromRoom(room, bannedPlayer.socket)

	def _quitRoomCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			self._removeSocketFromRoom(room, socket)

	def _startGameCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			room.status = RoomStatus.IN_GAME
			if room.isPlayerInRoom(self.socket):
				print(f'O {socket} iniciou o jogo da sala \'{room.name}\'')

				self._nextRound()

	def _nextRound(self):
		self._sharedGameData.roundNumber 			+= 1

		self.wantedRoundMasterWord					= None 
		self.wantedPlayerWord 						= None 
		self._sharedGameData.roundWord 				= None
		self._sharedGameData.chosenWords 			= []
		self._sharedGameData.roundMasterVotes 		= {}
		self._sharedGameData.electingOut 			= {}
		self._sharedGameData.contestingVotes 		= {}
		self._sharedGameData.roundAnswers 			= {}
		self._sharedGameData.roundPlayersEliminated = []

		self._roomPrint(f'Rodada {self.getRoundNumber()}')

		self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
		self._sharedGameData.setGamePhase(GamePhase.ELECTING_ROUND_MASTER)

		self._setCountdown(
			GamePhase.ELECTING_ROUND_MASTER, CONFIG.TIME_PHASE, 
			self._electingMasterRoomPhaseTimeIsUpCallback
		)

	def _changingGamePhaseCallback(self, gamePhase):
		self._roomPrint(f'Fase - {gamePhase}')
		if self._listenChangingGamePhaseCallback:
			self._listenChangingGamePhaseCallback(gamePhase)

	def _electingMasterRoomPhaseTimeIsUpCallback(self):
		if self.getPhaseTime() == 0:
			self._roomPrint('Acabou o tempo para votar no Organizador da Rodada')

		totalVotes, moreVotesPlayers = self._getMoreVotesPlayers(self._sharedGameData.roundMasterVotes)

		if len(moreVotesPlayers) > 1:
			for player in self._sharedGameData.room.players:
				if self.isEliminatedOrWatchingPlayer(player):
					if player not in moreVotesPlayers:
						self._sharedGameData.electingOut[player.socket.ip] = player
					if player.socket.ip not in self._sharedGameData.roundMasterVotes:
						self._roomPrint(f'\'{player.nickname}\' não votou. Seu voto foi anulado.')

			playersNickname = [player.nickname for player in moreVotesPlayers]
			self._roomPrint(f'Eleição - Houveram empates. Ocorrerá outra rodada de votação com os jogadores: {", ".join(playersNickname)}.')
			
			self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			self._sharedGameData.setGamePhase(GamePhase.RELECTING_ROUND_MASTER)

			self._setCountdown(
				GamePhase.RELECTING_ROUND_MASTER, CONFIG.TIME_PHASE, 
				self._electingMasterRoomPhaseTimeIsUpCallback
			)

		else:
			self._sharedGameData.roundMaster = moreVotesPlayers[0]
			self._roomPrint(f'Eleição - \'{self._sharedGameData.roundMaster.nickname}\' venceu a eleição de Organizador da Rodada.')

			self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			self._sharedGameData.setGamePhase(GamePhase.CHOOSING_ROUND_WORD)
			self._sharedGameData.electingOut = {}

			self._setCountdown(
				GamePhase.CHOOSING_ROUND_WORD, CONFIG.TIME_PHASE, 
				self._chooseRoundWordTimeIsUpCallback
			)

		self._sharedGameData.roundMasterVotes = {}

	def _chooseRoundWordTimeIsUpCallback(self):
		if not self._sharedGameData.roundWord:
			self._sharedGameData.roundMaster.status = PlayerStatus.ELIMINATED
			self._roomPrint(f'\'{self._sharedGameData.roundMaster.nickname}\' não escolheu a palavra da rodada e foi eliminado.')
			self._nextRound()

	def _chooseVoteElectionRoundMasterCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			playerSocket = room.getPlayer(socket)
			chosenPlayer = room.getPlayer(self.getSocket(params[ActionParam.SOCKET_IP]))
			self._sharedGameData.roundMasterVotes[socket.ip] = chosenPlayer
			playerSocket.status = PlayerStatus.AWAITING_THE_END_OF_ORGANIZER_VOTE
			self._roomPrint(f'Eleição - \'{playerSocket.nickname}\' votou em \'{chosenPlayer.nickname}\'.')

			isAllPlayersVoted = self._isAllPlayersVoted(
				self._sharedGameData.roundMasterVotes, 
				{self.getRoundMaster().socket.ip} if self.getRoundMaster() else set()
			)

			if isAllPlayersVoted:
				if self.getGamePhase() == GamePhase.ELECTING_ROUND_MASTER:
					self._finishCountdown(GamePhase.ELECTING_ROUND_MASTER)
				elif self.getGamePhase() == GamePhase.RELECTING_ROUND_MASTER:
					self._finishCountdown(GamePhase.RELECTING_ROUND_MASTER)

	def _isAllPlayersVoted(self, electionVote, exceptions, ignoreOnlyWacthing=False):
		group = (PlayerStatus.WATCHING, PlayerStatus.ELIMINATED)
		if ignoreOnlyWacthing:
			(PlayerStatus.WATCHING,)

		for player in self.getCurrentRoom().players:
			if (player.status not in group and
					player.socket.ip not in exceptions and 
					player.socket.ip not in electionVote):
				return False
		return True

	def _chooseRoundWordCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			playerSocket = room.getPlayer(socket)
			word = Word(params[ActionParam.WORD_STRING], params[ActionParam.WORD_DIVISION])

			self._sharedGameData.roundWord = word
			
			self._sharedGameData.chosenWords.append({'player': playerSocket, 'word': word})

			self._roomPrint(f'{playerSocket.nickname} escolhou a palavra da rodada: {word.wordStr}.')

			self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			self._sharedGameData.setGamePhase(GamePhase.WAITING_ANSWERS)

			self._setCountdown(
				GamePhase.WAITING_ANSWERS, CONFIG.TIME_PHASE, 
				self._watingAnswersTimeIsUpCallback
			)

	def _watingAnswersTimeIsUpCallback(self):
		if self.getPhaseTime() == 0:
			self._roomPrint('Acabou o tempo para responder a Divisão Silábica.')

		self._sharedGameData.setGamePhase(GamePhase.WAITING_CORRECT_ANSWER)

		if self.getCurrentPlayer() is self.getRoundMaster():
			self._sendCorrectAnswer()

	def _sendCorrectAnswer(self):
		params = {
			ActionParam.ROOM_ID: getattr(self.getCurrentRoom(), 'id', None),
			ActionParam.WORD_DIVISION: self._sharedGameData.wantedRoundMasterWord.getNoHashSyllables()
		}

		self._raiseActionIfNotCondictions(Action.SEND_MASTER_ANSWER, params)

		packet = PacketRequest(Action.SEND_MASTER_ANSWER, params)
		self._sendPacketRequest(packet)

	def _correctAnswerCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			wordDivision = params[ActionParam.WORD_DIVISION]
			wordStr = self._sharedGameData.roundWord.wordStr
			self._sharedGameData.wantedRoundMasterWord = Word(wordStr, wordDivision)

			self._roomPrint(f'A resposta correta era {wordDivision}')

			room = self.getCurrentRoom()
			roomPlayers = room.players
			for player in roomPlayers:
				if (player is not self._sharedGameData.roundMaster and 
						not self.isEliminatedOrWatchingPlayer(player)):
					if player.socket.ip not in self._sharedGameData.roundAnswers:
						player.status = PlayerStatus.ELIMINATED
						self._sharedGameData.roundPlayersEliminated.append(player)
						self._roomPrint(f'\'{player.nickname}\' foi eliminado por não responder a divisão silábica.')
					else:
						word = self._sharedGameData.roundAnswers[player.socket.ip]
						if word != self._sharedGameData.roundWord:
							player.status = PlayerStatus.ELIMINATED
							self._sharedGameData.roundPlayersEliminated.append(player)
							self._roomPrint(f'\'{player.nickname}\' errou a divisão silábica e foi eliminado.')
						else:
							self._roomPrint(f'\'{player.nickname}\' respondeu corretamente divisão silábica.')

			self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			if len(self._sharedGameData.roundPlayersEliminated) == 0:
				self._roomPrint('Nenhum jogador errou a divisão silábica.')
				self._goToResultPhase()
			else:
				self._sharedGameData.setGamePhase(GamePhase.WAITING_CONTESTS)

				self._setCountdown(
					GamePhase.WAITING_CONTESTS, CONFIG.TIME_PHASE, 
					self._watingContestTimeIsUpCallback
				)

	def _answerRoundWordCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			playerSocket = room.getPlayer(socket)
			roundWord = self._sharedGameData.roundWord
			word = Word(roundWord.wordStr, params[ActionParam.WORD_DIVISION])
			self._sharedGameData.roundAnswers[socket.ip] = word
			playerSocket.status = PlayerStatus.AWAITING_THE_END_OF_THE_SILABIC_DIVISION_PHASE
			self._roomPrint(f'\'{playerSocket.nickname}\' respondeu a divisão silábica.')

			isAllPlayersVoted = self._isAllPlayersVoted(
				self._sharedGameData.roundAnswers,
				{self.getRoundMaster().socket.ip}
			)

			if isAllPlayersVoted:
				self._finishCountdown(GamePhase.WAITING_ANSWERS)


	def _contestAnswerWordCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			self._cancelCountdown(GamePhase.WAITING_CONTESTS)

			room = self.getRoom(params[ActionParam.ROOM_ID])
			wordDivision = params[ActionParam.WORD_DIVISION]
			wordStr = self._sharedGameData.roundAnswers[socket.ip].wordStr
			self._sharedGameData.roundAnswers[socket.ip] = Word(wordStr, wordDivision)

			playerSocket = room.getPlayer(socket)

			self._sharedGameData.contestingPlayer = playerSocket

			self._roomPrint(f'\'{playerSocket.nickname}\' contestou a resposta correta. '
							f'Sua resposta foi {wordDivision}')

			self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
			self._sharedGameData.setGamePhase(GamePhase.ELECTING_CORRECT_ANSWER)

			self._setCountdown(
				GamePhase.ELECTING_CORRECT_ANSWER, CONFIG.TIME_PHASE, 
				self._electingCorrectAnswerPhaseTimeIsUpCallback
			)

	def _chooseVoteContestAnswerCallback(self, socket, params, actionError):
		if actionError == ActionError.NONE:
			room = self.getRoom(params[ActionParam.ROOM_ID])
			playerSocket = room.getPlayer(socket)

			chosenPlayer = room.getPlayer(self.getSocket(params[ActionParam.SOCKET_IP]))
			
			if not chosenPlayer:
				self._roomPrint(f'Eleição da Contestação - \'{playerSocket.nickname}\' votou nulo.')
			else:
				self._sharedGameData.contestingVotes[socket.ip] = chosenPlayer
				word = self._wordOfContestingByPlayer(chosenPlayer)
				self._roomPrint(f'Eleição da Contestação - \'{playerSocket.nickname}\' votou para '
								f'{word.getNoHashSyllables()}')

			if not self.isEliminatedOrWatchingPlayer(playerSocket):
				playerSocket.status = PlayerStatus.AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST

			isAllPlayersVoted = self._isAllPlayersVoted(
				self._sharedGameData.contestingVotes, 
				{self.getRoundMaster().socket.ip, self.getContestingPlayer().socket.ip}, True
			)

			if isAllPlayersVoted:
				self._finishCountdown(GamePhase.ELECTING_CORRECT_ANSWER)

	def _electingCorrectAnswerPhaseTimeIsUpCallback(self):
		if self.getPhaseTime() == 0:
			self._roomPrint('Acabou o tempo para votar na Resposta Correta')

		totalVotes, moreVotesPlayers = self._getMoreVotesPlayers(self._sharedGameData.contestingVotes)

		if len(moreVotesPlayers) > 1:
			self._roomPrint(f'Eleição da Contestação - Houveram empates. Portanto ninguém será elimando nesta rodada.')

			for player in self._sharedGameData.roundPlayersEliminated:
				player.status = PlayerStatus.AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST

		else:
			word = self._wordOfContestingByPlayer(moreVotesPlayers[0])

			if moreVotesPlayers[0] is self.getRoundMaster():
				self._roomPrint(f'Eleição da Contestação - A divisão silábica que venceu foi {word.getNoHashSyllables()}. '
								f'Portanto o jogadores que erraram continuam eliminados.')

			elif moreVotesPlayers[0] is self.getContestingPlayer():
				self._roomPrint(f'Eleição da Contestação - A divisão silábica que venceu foi {word.getNoHashSyllables()}. '
								f'Portanto somente o Organizador da Rodada será eliminado nesta rodada.')

				for player in self._sharedGameData.roundPlayersEliminated:
					player.status = PlayerStatus.AWAITING_THE_END_OF_THE_VOTING_OF_THE_CONTEST

				self.getRoundMaster().status = PlayerStatus.ELIMINATED

		self._goToResultPhase()

	def _watingContestTimeIsUpCallback(self):
		self._goToResultPhase()

	def _goToResultPhase(self):
		self._sharedGameData.phaseTime = CONFIG.TIME_PHASE
		self._sharedGameData.setGamePhase(GamePhase.RESULT_ROUND)

		if not self._hasOnlyOnePlayerAlive():
			self._setCountdown(
				GamePhase.RESULT_ROUND, CONFIG.TIME_PHASE, 
				self._nextRound
			)
		else:
			self._cancelAllCoutdown()
			self._sharedGameData.setGamePhase(GamePhase.FINISHED)
			winnerPlayer = self._getAlivePlayer()
			if winnerPlayer:
				winnerPlayer.status = PlayerStatus.WINNER
				self._roomPrint(f'O jogador {winnerPlayer.nickname} venceu a partida.')
			else:
				self._roomPrint(f'Não houveram vencedores na partida.')

	def _wordOfContestingByPlayer(self, player):
		if player is self.getRoundMaster():
			return self._sharedGameData.wantedRoundMasterWord
		elif player is self.getContestingPlayer():
			contestingPlayerSocketIp = self.getContestingPlayer().socket.ip
			return self._sharedGameData.roundAnswers[contestingPlayerSocketIp]
		return None

	def _hasOnlyOnePlayerAlive(self):
		room = self.getCurrentRoom()
		roomPlayers = room.players

		alivePlayers = 0
		for player in roomPlayers:
			if player.status not in (PlayerStatus.ELIMINATED, PlayerStatus.WATCHING):
				alivePlayers += 1
		return alivePlayers <= 1

	def _getAlivePlayer(self):
		room = self.getCurrentRoom()
		roomPlayers = room.players
		for player in roomPlayers:
			if not self.isEliminatedOrWatchingPlayer(player):
				return player
		return None

	def _getMoreVotesPlayers(self, electionVotes):
		votesByPlayer = {player.socket.ip: [player, 0] for player in self.getCurrentRoom().players}
		for player in electionVotes.values():
			votesByPlayer[player.socket.ip][1] += 1
		playerByVotes = {}
		totalVotes = 0
		for ip, votesPlayer in votesByPlayer.items():
			player, votes = votesPlayer
			if not votes in playerByVotes:
				totalVotes = votes if votes > totalVotes else totalVotes
				playerByVotes[votes] = []
			playerByVotes[votes].append(player)

		return totalVotes, playerByVotes[totalVotes]

	def _setCountdown(self, id_, time, callback):
		countdown = Countdown(
			time, callback, daemon=True
		)
		self._sharedGameData._countdowns[id_] = countdown
		countdown.start()

	def _cancelCountdown(self, id_):
		if id_ in self._sharedGameData._countdowns:
			self._sharedGameData._countdowns[id_].cancel()
			del self._sharedGameData._countdowns[id_]

	def _cancelAllCoutdown(self):
		for id_ in self._sharedGameData._countdowns:
			self._sharedGameData._countdowns[id_].cancel()
		self._sharedGameData._countdowns[id_] = {}

	def _finishCountdown(self, id_):
		if id_ in self._sharedGameData._countdowns:
			self._sharedGameData._countdowns[id_].finish()
			del self._sharedGameData._countdowns[id_]

	def _roomPrint(self, message):
		print(f'Sala \'{self.getCurrentRoom().name}\': {message}')

	def _disconnectCallback(self, socket):
		self._removeSocketFromRooms(socket)

		if self._listenDisconnectSocketCallback:
			self._listenDisconnectSocketCallback(socket)

	def _removeSocketFromRoom(self, room, socket):
		player = room.getPlayer(socket)

		if player:
			room.removePlayer(socket)

			print(f'O jogador \'{player.nickname}\' saiu da sala \'{room.name}\'.')

			if room is self.getCurrentRoom():
				# Remover jogador de possíves votações que pode ter realizado
				participations = (
					self._sharedGameData.roundMasterVotes,
					self._sharedGameData.electingOut, 
					self._sharedGameData.contestingVotes,
					self._sharedGameData.roundAnswers
				)

				for participation in participations:
					if socket.ip in participation:
						del participation[socket.ip]

				if player in self._sharedGameData.roundPlayersEliminated:
					self._sharedGameData.roundPlayersEliminated.remove(player)

			if socket is self.socket:
				self._initSharedGameData()

			if room.owner is socket and len(room.players) > 0:
				room.owner = room.players[0].socket

			if (room.status == RoomStatus.IN_GAME and room.isPlayerInRoom(self.socket)
					and len(room.players) == 1):
				self._goToResultPhase()

			if len(room.players) == 0:
				del self._rooms[room.id]

	def _removeSocketFromRooms(self, socket):
		self._removePlayerFromRoomLock.acquire()
		
		for room in self._rooms.values():
			if room.getPlayer(socket):
				self._removeSocketFromRoom(room, socket)
				break

		self._removePlayerFromRoomLock.release()

	def _sendPacketRequest(self, packet, toSocket=None):
		self._sendPacket(packet, toSocket)
		self._createPacketWaiter(packet)
		self._savePacketRequestWaiter(self.socket, packet)

	def _sendPacket(self, packet, toSocket=None):
		if not toSocket:
			self._network.sendPacket(packet, receiverGroupIps=self._receiverGroupIps)
		else:
			self._network.sendPacket(packet, toSocket=toSocket)

	def _createPacketWaiter(self, packet):
		if packet.uuid not in self._packetWaitingApprovation:
			self._packetWaitingApprovation[packet.uuid] = {
				'request_socket': None,
				'request_packet': None,
				'responses': {},
				'agreements_list': [],
				'disagreements_list': [],
				'first_packet_time': datetime.now(),
				'lock': Lock()
			}

	def _deletePacketWaiter(self, packet):
		if packet.uuid in self._packetWaitingApprovation:
			del self._packetWaitingApprovation[packet.uuid]

	def _savePacketRequestWaiter(self, socket, packet):
		self._packetWaitingApprovation[packet.uuid]['request_socket'] = socket
		self._packetWaitingApprovation[packet.uuid]['request_packet'] = packet

	def _waiterHandler(self, socket, packet):
		self._createPacketWaiter(packet)

		packetWaiter = self._packetWaitingApprovation[packet.uuid]

		packetWaiter['lock'].acquire()

		# Ignorar pacotes de ações já aprovadas ou desaprovadas
		if packet.uuid in self._donePacketHandler:
			self._deletePacketWaiter(packet)
			packetWaiter['lock'].release()
			return

		if packet.packetType == PacketType.REQUEST:
			if not self._isValidPacket(socket, packet):
				self._deletePacketWaiter(packet)
				packetWaiter['lock'].release()
				return

			self._savePacketRequestWaiter(socket, packet)

			if self._isSocketInApprovationGroup(self.socket, packet):
				actionError = self._testPacketConditions(socket, packet)
				packetResponse = PacketResponse(packet.action, actionError, uuid=packet.uuid)
				self._sendPacket(packetResponse)

		elif packet.packetType == PacketType.RESPONSE:
			packetWaiter['responses'][socket.ip] = packet
			
			approvationList = packetWaiter['agreements_list']
			if not packet.approved:
				approvationList = packetWaiter['disagreements_list']
			approvationList.append(socket)


		isPacketApproved = self._isPacketApproved(socket, packet)
		isPacketDisapproved = self._isPacketDisapproved(socket, packet)

		if isPacketApproved or isPacketDisapproved:
			requestSocket = packetWaiter['request_socket']
			requestPacket = packetWaiter['request_packet']
			responses = packetWaiter['responses']
			startThread(
				self._packetApprovedCallback, 
				requestSocket, requestPacket, responses
			)

		if isPacketApproved or isPacketDisapproved:
			self._donePacketHandler.add(packet.uuid)
			del self._packetWaitingApprovation[packet.uuid]

		packetWaiter['lock'].release()

	def _isValidPacket(self, socket, packet):
		valid = True
		approvationGroup = packet.action.approvationGroup
		if ((approvationGroup == ActionGroup.ROOM_PLAYERS or
				approvationGroup == ActionGroup.ROOM_OWNER) and  
				packet.params[ActionParam.ROOM_ID] not in self._rooms):
			valid = False
		
		if not valid:
			print(f'Game Packet invalid arrived from {socket} was ignored.')
		
		return valid	

	def _isSocketInApprovationGroup(self, socket, packet):
		result = None
		approvationGroup = packet.action.approvationGroup
		if approvationGroup == ActionGroup.NONE:
			result = False
		elif approvationGroup == ActionGroup.ALL_NETWORK:
			result = True
		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			room = self._rooms.get(packet.params[ActionParam.ROOM_ID], None)
			result = bool(room) and any(player.socket is socket for player in room.players)
		elif approvationGroup == ActionGroup.ROOM_OWNER:
			result = room = self._rooms.get(packet.params[ActionParam.ROOM_ID], None)
			result = bool(room and socket is room.owner)
		return result

	def _testPacketConditions(self, socket, packet):
		for condition in packet.action.conditions:
			actionError = condition(self._network, socket, self._rooms, self._sharedGameData, packet.params)
			if actionError != ActionError.NONE:
				return actionError
		return ActionError.NONE

	def _approvationRequirement(self, socket, packet):
		totalNeeded = None
		fullGroup = set()
		approvationGroup = packet.action.approvationGroup

		if approvationGroup == ActionGroup.ALL_NETWORK:
			totalNeeded = len(self._network.allNetwork) // 2 + 1
			fullGroup = {socket for socket in self._network.allNetwork.values()}

		elif approvationGroup == ActionGroup.ROOM_PLAYERS:
			roomPlayers = self._rooms[packet.params[ActionParam.ROOM_ID]].players
			totalNeeded = len(roomPlayers) // 2 + 1
			fullGroup = {player.socket for player in roomPlayers}

		elif approvationGroup == ActionGroup.NONE:
			totalNeeded = 2
			fullGroup = {socket for socket in self._network.allNetwork.values()}

		elif approvationGroup == ActionGroup.ROOM_OWNER:
			room = self._rooms[packet.params[ActionParam.ROOM_ID]]
			totalNeeded = 1
			fullGroup = {room.owner}

		return totalNeeded, fullGroup


	def _isPacketApproved(self, socket, testPacket):
		packet = self._packetWaitingApprovation[testPacket.uuid]['request_packet']

		if not packet:
			return False 

		agreementsList = self._packetWaitingApprovation[packet.uuid]['agreements_list']
		totalNeeded, fullGroup = self._approvationRequirement(socket, packet)
		totalApprovation = {socket for socket in agreementsList if socket in fullGroup}

		return len(totalApprovation) >= totalNeeded

	def _isPacketDisapproved(self, socket, testPacket):
		packet = self._packetWaitingApprovation[testPacket.uuid]['request_packet']

		if not packet:
			return False 

		disagreementsList = self._packetWaitingApprovation[packet.uuid]['disagreements_list']
		totalNeeded, fullGroup = self._approvationRequirement(socket, packet)
		totalDisaprovation = {socket for socket in disagreementsList if socket in fullGroup}

		return len(fullGroup) - len(totalDisaprovation) < totalNeeded

def startThread(target, *args):
	Thread(target=target, args=args, daemon=True).start()

if __name__ == '__main__':
	interfaces = getAllIpAddress()
	print('Interface disponíveis: ')
	for i, ip in enumerate(interfaces):
		print(f'{i} - {ip}')
	number_interface = int(input('\nSelecione a interface: '))
	game = GameClient(interfaces[number_interface])
	game.start()

	while True: pass
