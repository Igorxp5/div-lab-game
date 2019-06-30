from .game.room import RoomStatus, GamePhase

from enum import Enum

class InvalidActionParams(RuntimeError):
	def __init__(self, message=''):
		super().__init__(message)


class ActionGroup(Enum):
	NONE = 0
	ALL_NETWORK = 1
	ROOM_PLAYERS = 2
	ROOM_OWNER = 3


class ActionRw(Enum):
	READ = 'r'
	WRITE = 'w'


class ActionParam(Enum):
	ROOM_NAME = 'room_name', str
	PLAYERS_LIMIT = 'players_limit', int
	ROOM_ID = 'room_id', str
	PLAYER_NAME = 'player_name', str
	WORD_STRING = 'word_string', str
	WORD_DIVISION = 'word_division', str
	SOCKET_IP = 'socket_ip', str

	def __init__(self, key, type_):
		self.key = key
		self.type = type_

	def __str__(self):
		return self.key

	def __call__(self, value):
		return self.type(value)

	@staticmethod
	def getByValue(key):
		for action in ActionParam:
			if key == action.key:
				return action
		raise NotImplementedError


class ActionCondiction(Enum):
	ROOM_STATUS_IN_GAME = lambda network, socket, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).roomStatus is RoomStatus.IN_GAME
	)
	ROOM_STATUS_IN_WAIT = lambda network, socket, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).roomStatus is RoomStatus.IN_WAIT
	)
	PLAYER_NOT_IN_ROOM = lambda network, socket, rooms, game, params: (
		len(rooms) == 0 or all((socket.ip not in room.players for room in rooms))
	)
	PLAYER_INSIDE_ROOM = lambda network, socket, rooms, game, params: (
		socket in rooms.get(params[ActionParam.ROOM_ID]).players
	)
	PLAYER_IS_OWNER_ROOM = lambda network, socket, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).owner.socket.ip == socket
	)
	PLAYER_IS_MASTER_ROOM = lambda network, socket, rooms, game, params: (
		game and game.roundMaster and game.roundMaster.socket.ip == socket
	)
	PLAYER_IS_NOT_MASTER_ROOM = lambda network, socket, rooms, game, params: (
		game and game.roundMaster and game.roundMaster.socket.ip != socket
	)
	TIME_NOT_IS_UP = lambda network, socket, rooms, game, params: (
		game and game.phaseTime and game.phaseTime == 0
	)
	TIME_IS_UP = lambda network, socket, rooms, game, params: (
		game and game.phaseTime and game.phaseTime < 800
	)
	GAME_IS_WAITING_CONTESTS = lambda network, socket, rooms, game, params: (
		game and game.phase is GamePhase.WAITING_CONTESTS
	)
	GAME_IS_ELECTING_MASTER_ROOM = lambda network, socket, rooms, game, params: (
		game and game.phase is GamePhase.ELECTING_MASTER_ROOM
	)
	GAME_IS_ELECTING_CORRECT_ANSWER = lambda network, socket, rooms, game, params: (
		game and game.phase is GamePhase.ELECTING_CORRECT_ANSWER
	)
	GAME_IS_WAITING_ANSWERS = lambda network, socket, rooms, game, params: (
		game and game.phase is GamePhase.WAITING_ANSWERS
	)
	GAME_IS_RESULT_ROUND = lambda network, socket, rooms, game, params: (
		game and game.phase is GamePhase.RESULT_ROUND
	)
	PLAYER_MISSED_ANSWER = lambda network, socket, rooms, game, params: (
		socket in game.roundAnswers and game.roundAnswers.get(socket.ip, None) == game.roundWord
	)
	CHOSEN_PLAYER_IS_IN_ROOM = lambda network, socket, rooms, game, params: (
		socket in rooms.get(params[ActionParam.ROOM_ID]).players and 
		params[ActionParam.SOCKET_IP] in rooms.get(params[ActionParam.ROOM_ID], []).players
	)
	CHOSEN_PLAYER_IS_NOT_MASTER_ROOM = lambda network, socket, rooms, game, params: (
		game and game.roundMaster and 
		game.roundMaster.socket.ip == params[ActionParam.SOCKET_IP]
	)
	CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_MASTER_ROOM = lambda network, socket, rooms, game, params: (
		game and (
			(game.roundMaster and game.roundMaster.socket.ip == params[ActionParam.SOCKET_IP])
			or (game.contestingPlayer and game.contestingPlayer.socket.ip == params[ActionParam.SOCKET_IP])
		)
	)
	PLAYER_CAN_BE_OWNER = lambda network, socket, rooms, game, params: (
		# TODO: Falta verificar se o jogador está desconectado
		rooms.get(params[ActionParam.ROOM_ID]).players.index(socket) == 1
	)

	def __call__(self, network, socket, rooms, game, params):
		return bool(self.value(network, socketId, rooms, game, params))


class Action(Enum):
	CREATE_ROOM = (1, 'Create Room', ActionRw.WRITE, 
				   (ActionParam.ROOM_ID, ActionParam.ROOM_NAME, ActionParam.PLAYERS_LIMIT), 
				   (ActionCondiction.PLAYER_NOT_IN_ROOM,), 
				   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	JOIN_ROOM_PLAY = (2, 'Join into Room to Play', ActionRw.WRITE, 
					  (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					  (ActionCondiction.PLAYER_NOT_IN_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					  ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	JOIN_ROOM_WATCH = (3, 'Join into Room to Watch', ActionRw.WRITE, 
					   (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					   (ActionCondiction.PLAYER_NOT_IN_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	CHOOSE_ROUND_WORD = (4, 'Choose Round Word', ActionRw.WRITE,
						 (ActionParam.ROOM_ID, ActionParam.WORD_STRING), 
						 (ActionCondiction.PLAYER_IS_MASTER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						 	ActionCondiction.TIME_NOT_IS_UP), 
						 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CONTEST_WORD = (5, 'Contest Word', ActionRw.WRITE, 
					(ActionParam.ROOM_ID,),
					(ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						ActionCondiction.GAME_IS_WAITING_CONTESTS, ActionCondiction.TIME_NOT_IS_UP,
						ActionCondiction.PLAYER_MISSED_ANSWER), 
					ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	
	QUIT_ROOM = (6, 'Quit Room', ActionRw.WRITE, 
				 (ActionParam.ROOM_ID,), 
				 (ActionCondiction.PLAYER_INSIDE_ROOM,), 
				 ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	CHOOSE_VOTE_ELECTION_ROUND_MASTER = (7, 'Choose Vote Election Round Master', ActionRw.WRITE, 
										 (ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
										 (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
										 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM, ActionCondiction.GAME_IS_ELECTING_MASTER_ROOM,
										 	ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.CHOSEN_PLAYER_IS_NOT_MASTER_ROOM), 
										 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	SEND_PLAYER_ANSWER = (8, 'Send Player Answer', ActionRw.WRITE, 
						  (ActionParam.ROOM_ID, ActionParam.WORD_DIVISION), 
						  (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						  	ActionCondiction.GAME_IS_WAITING_ANSWERS, ActionCondiction.TIME_NOT_IS_UP,
						  	ActionCondiction.PLAYER_IS_NOT_MASTER_ROOM), 
						  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CHOOSE_VOTE_CONTEST_ANSWER = (9, 'Choose Vote Contest Answer', ActionRw.WRITE, 
								  (ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
								  (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM, ActionCondiction.GAME_IS_ELECTING_CORRECT_ANSWER,
								 	ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_MASTER_ROOM), 
								  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	GET_LIST_ROOMS = (10, 'Get List Rooms', ActionRw.READ, 
					  tuple(), 
					  tuple(), 
					  ActionGroup.NONE, ActionGroup.NONE)

	GET_ROOM_DATA_TABLE = (11, 'Get Room Data Table', ActionRw.READ, 
						   (ActionParam.ROOM_ID,), 
						   tuple(), 
						   ActionGroup.ROOM_OWNER, ActionGroup.ROOM_OWNER)

	KICK_PLAYER_ROOM = (12, 'Kick Player of Room', ActionRw.WRITE, 
						(ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
						(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT,
						 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM), 
						ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	START_ROOM_GAME = (13, 'Start Room Game', ActionRw.WRITE, 
					   (ActionParam.ROOM_ID,), 
					   (ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	INCREMENT_GAME_PHASE = (14, 'Increment Game Phase', ActionRw.WRITE, 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								ActionCondiction.TIME_IS_UP), 
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	INCREMENT_GAME_ROUND = (15, 'Increment Game Round', ActionRw.WRITE, 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								ActionCondiction.GAME_IS_RESULT_ROUND, ActionCondiction.TIME_IS_UP),
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	BE_ROOM_OWNER = (16, 'Be Room Owner', ActionRw.WRITE, 
					 (ActionParam.ROOM_ID,), 
					 (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						ActionCondiction.PLAYER_CAN_BE_OWNER), 
					 ActionGroup.ALL_NETWORK, ActionGroup.ROOM_PLAYERS)

	SEND_MASTER_ANSWER = (17, 'Send Master Answer', ActionRw.WRITE, 
						  (ActionParam.ROOM_ID, ActionParam.WORD_DIVISION),
						  (ActionCondiction.PLAYER_IS_MASTER_ROOM, ActionCondiction.GAME_IS_WAITING_ANSWERS, 
						  	ActionCondiction.TIME_IS_UP), 
						  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	def __init__(self, id_, description, 
				 rw, params, conditions,
				 receiverGroup, approvationGroup):
		self.id 				= id_
		self.description 		= description
		self.rw 				= rw
		self.params 			= params
		self.conditions 		= conditions
		self.receiverGroup 		= receiverGroup
		self.approvationGroup 	= approvationGroup

	@property
	def codename(self):
		return 'AC{:03d}'.format(self.id)

	@staticmethod
	def getById(id_):
		for action in Action:
			if id_ == action.id:
				return action
		raise NotImplementedError

if __name__ == '__main__':
	packetAction = Action.CHOOSE_ROUND_WORD
	print(packetAction.params)
