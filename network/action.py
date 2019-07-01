import network.config as CONFIG
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

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'


class ActionRw(Enum):
	READ = 'r'
	WRITE = 'w'

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'


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

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'

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


class ActionError(Enum):
	NONE = (0, 'Sem erros.')
	UKNOWN = (1, 'Ocorreu um erro desconhecido.')
	GENERIC = (2, 'Ocorreu um erro.')
	ROOM_NOT_EXISTS = (3, 'A sala não existe.')
	PLAYER_IN_ROOM = (4, 'O jogador já se encontra numa sala.')
	PLAYER_NOT_IN_ROOM = (5, 'O jogador não se encontra na sala.')
	ROOM_NAME_ALREADY_EXIST = (6, 'Uma sala com nome solicitado já existe.')
	PLAYER_NAME_ALREADY_EXIST = (7, 'Um jogador com o nome solicitado já existe.')
	ROOM_IS_FULL = (8, 'A sala está cheia.')
	PLAYER_IS_NOT_OWNER = (9, 'O jogador não é o dono da sala.')
	PLAYER_IS_NOT_ROUND_MASTER = (10, 'O jogador não é o organizador da rodada.')
	PLAYER_IS_ROUND_MASTER = (11, 'O jogador é o organizador da rodada.')
	PLAYER_WAS_ROUND_MASTER = (12, 'O jogador foi o organizador da rodada passada.')
	TIME_IS_NOT_UP = (13, 'O tempo da rodada ainda não acabou.')
	TIME_IS_UP = (14, 'O tempo da rodada acabou.')
	PLAYER_NOT_MISSED_ANSWER = (15, 'O jogador não errou a palavra.')
	PLAYER_CANT_BE_OWNER = (16, 'O jogador não é elegível a dono da sala.')
	PLAYER_IS_A_OWNER = (17, 'O jogador já é dono de uma sala.')
	MIN_PLAYERS_TO_START = (18, f'A quantidade mínima de jogadores para iniciar uma sala é {CONFIG.MIN_PLAYERS_TO_START}')
	GAME_NOT_ELECTING_ROUND_MASTER = (19, 'O jogo não se encontra na rodada de eleição de organizador da rodada.')
	PLAYER_IS_OUT_ELECTING = (20, 'O jogador não pode ser escolhido, ele está fora da eleição.')
	ROOM_IN_GAME = (21, 'A sala já está em jogo.')
	ROOM_ON_HOLD = (22, 'A sala ainda não começou a partida.')

	def __init__(self, code, message):
		self.code = code
		self.message = message

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'

	def __bool__(self):
		return self.code == 0

	def __str__(self):
		return self.message

	@staticmethod
	def getByCode(code):
		for action in ActionError:
			if code == action.code:
				return action
		raise NotImplementedError


class ActionCondiction(Enum):
	ROOM_EXISTS = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (params[ActionParam.ROOM_ID] in rooms)
		else ActionError.ROOM_NOT_EXISTS
	)
	ROOM_STATUS_IN_GAME = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (rooms[params[ActionParam.ROOM_ID]].status is RoomStatus.IN_GAME)
		else ActionError.ROOM_ON_HOLD
	)
	ROOM_STATUS_IN_WAIT = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (rooms[params[ActionParam.ROOM_ID]].status is RoomStatus.ON_HOLD)
		else ActionError.ROOM_IN_GAME
	)
	PLAYER_IS_NOT_A_OWNER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (len(rooms) == 0 or 
			all((socket is not room.owner for room in rooms.values())))
		else ActionError.PLAYER_IS_A_OWNER
	)
	PLAYER_NAME_IS_VALID = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (
			not rooms[params[ActionParam.ROOM_ID]].playerNameInRoom(params[ActionParam.PLAYER_NAME])
		) else  ActionError.PLAYER_NAME_ALREADY_EXIST
	)
	PLAYER_NOT_IN_A_ROOM = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (len(rooms) == 0 or 
			all((not room.isPlayerInRoom(socket) for room in rooms.values())))
		else ActionError.PLAYER_IN_ROOM
	)
	PLAYER_INSIDE_ROOM = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (rooms[params[ActionParam.ROOM_ID]].isPlayerInRoom(socket) or 
			rooms[params[ActionParam.ROOM_ID]].owner is socket)
		else ActionError.PLAYER_NOT_IN_ROOM
	)
	PLAYER_IS_OWNER_ROOM = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (rooms[params[ActionParam.ROOM_ID]].owner is socket)
		else ActionError.PLAYER_IS_NOT_OWNER
	)
	PLAYER_IS_ROUND_MASTER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.roundMaster and game.roundMaster.socket.ip is socket)
		else ActionError.PLAYER_IS_NOT_ROUND_MASTER
	)
	PLAYER_IS_NOT_ROUND_MASTER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.roundMaster and game.roundMaster.socket.ip is not socket)
		else ActionError.PLAYER_IS_ROUND_MASTER
	)
	TIME_NOT_IS_UP = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.phaseTime and game.phaseTime > CONFIG.END_PHASE_TIME)
		else ActionError.TIME_IS_UP
	)
	TIME_IS_UP = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.phaseTime and game.phaseTime <= CONFIG.END_PHASE_TIME)
		else ActionError.TIME_IS_NOT_UP
	)
	GAME_IS_WAITING_CONTESTS = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.gamePhase is GamePhase.WAITING_CONTESTS)
		else ActionError.GENERIC
	)
	GAME_IS_ELECTING_ROUND_MASTER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.gamePhase is GamePhase.ELECTING_ROUND_MASTER or 
			game.gamePhase is GamePhase.RELECTING_ROUND_MASTER)
		else ActionError.GAME_NOT_ELECTING_ROUND_MASTER
	)
	GAME_IS_ELECTING_CORRECT_ANSWER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.gamePhase is GamePhase.ELECTING_CORRECT_ANSWER)
		else ActionError.GENERIC
	)
	GAME_IS_WAITING_ANSWERS = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.gamePhase is GamePhase.WAITING_ANSWERS)
		else ActionError.GENERIC
	)
	GAME_IS_RESULT_ROUND = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and game.gamePhase is GamePhase.RESULT_ROUND)
		else ActionError.GENERIC
	)
	PLAYER_MISSED_ANSWER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (socket in game.roundAnswers and game.roundAnswers.get(socket.ip, None) == game.roundWord)
		else ActionError.PLAYER_NOT_MISSED_ANSWER
	)
	CHOSEN_PLAYER_IS_IN_ROOM = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (
			rooms[params[ActionParam.ROOM_ID]].isPlayerInRoom(network.allNetwork[params[ActionParam.SOCKET_IP]]))
		else ActionError.PLAYER_NOT_IN_ROOM
	)
	CHOSEN_PLAYER_IS_NOT_ROUND_MASTER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and (not game.roundMaster or 
		game.roundMaster.socket.ip != params[ActionParam.SOCKET_IP]))
		else ActionError.PLAYER_WAS_ROUND_MASTER
	)
	CHOSEN_PLAYER_IS_NOT_OUT_ELECTING = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and params[ActionParam.SOCKET_IP] not in game.electingOut)
		else ActionError.PLAYER_IS_OUT_ELECTING
	)
	CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_ROUND_MASTER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (game and (
			(game.roundMaster and game.roundMaster.socket.ip == params[ActionParam.SOCKET_IP])
			or (game.contestingPlayer and game.contestingPlayer.socket.ip == params[ActionParam.SOCKET_IP])
		)) else ActionError.GENERIC
	)
	PLAYER_CAN_BE_OWNER = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (rooms[params[ActionParam.ROOM_ID]].owner not in network.peers and 
		rooms[params[ActionParam.ROOM_ID]].players[0].socket is socket)
		else ActionError.PLAYER_CANT_BE_OWNER
	)
	CAN_START_GAME = lambda network, socket, rooms, game, params: (
		ActionError.NONE if (len(rooms[params[ActionParam.ROOM_ID]].players) >= CONFIG.MIN_PLAYERS_TO_START)
		else ActionError.MIN_PLAYERS_TO_START
	)

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'

	def __call__(self, network, socket, rooms, game, params):
		return self.value(network, socketId, rooms, game, params)


class Action(Enum):
	CREATE_ROOM = (1, 'Create Room', ActionRw.WRITE, 
				   (ActionParam.ROOM_ID, ActionParam.ROOM_NAME, 
				   	ActionParam.PLAYERS_LIMIT, ActionParam.PLAYER_NAME), 
				   (ActionCondiction.PLAYER_IS_NOT_A_OWNER, ActionCondiction.PLAYER_NOT_IN_A_ROOM), 
				   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	JOIN_ROOM_PLAY = (2, 'Join into Room to Play', ActionRw.WRITE, 
					  (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					  (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_NOT_IN_A_ROOM, 
					  	ActionCondiction.ROOM_STATUS_IN_WAIT, ActionCondiction.PLAYER_NAME_IS_VALID), 
					  ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	JOIN_ROOM_WATCH = (3, 'Join into Room to Watch', ActionRw.WRITE, 
					   (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					   (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_NOT_IN_A_ROOM, 
					   	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.PLAYER_NAME_IS_VALID), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	CHOOSE_ROUND_WORD = (4, 'Choose Round Word', ActionRw.WRITE,
						 (ActionParam.ROOM_ID, ActionParam.WORD_STRING), 
						 (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_ROUND_MASTER, 
						 	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.TIME_NOT_IS_UP), 
						 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CONTEST_WORD = (5, 'Contest Word', ActionRw.WRITE, 
					(ActionParam.ROOM_ID,),
					(ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM, 
						ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.GAME_IS_WAITING_CONTESTS, 
						ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.PLAYER_MISSED_ANSWER), 
					ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	
	QUIT_ROOM = (6, 'Quit Room', ActionRw.WRITE, 
				 (ActionParam.ROOM_ID,), 
				 (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM,), 
				 ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	CHOOSE_VOTE_ELECTION_ROUND_MASTER = (7, 'Choose Vote Election Round Master', ActionRw.WRITE, 
										 (ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
										 (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM, 
										 	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM, 
										 	ActionCondiction.GAME_IS_ELECTING_ROUND_MASTER, ActionCondiction.TIME_NOT_IS_UP, 
										 	ActionCondiction.CHOSEN_PLAYER_IS_NOT_ROUND_MASTER,
										 	ActionCondiction.CHOSEN_PLAYER_IS_NOT_OUT_ELECTING), 
										 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	SEND_PLAYER_ANSWER = (8, 'Send Player Answer', ActionRw.WRITE, 
						  (ActionParam.ROOM_ID, ActionParam.WORD_DIVISION), 
						  (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM, 
						  	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.GAME_IS_WAITING_ANSWERS,
						  	ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.PLAYER_IS_NOT_ROUND_MASTER), 
						  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CHOOSE_VOTE_CONTEST_ANSWER = (9, 'Choose Vote Contest Answer', ActionRw.WRITE, 
								  (ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
								  (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM,
								  	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM,
								  	ActionCondiction.GAME_IS_ELECTING_CORRECT_ANSWER, ActionCondiction.TIME_NOT_IS_UP,
								  	ActionCondiction.CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_ROUND_MASTER,
								  	ActionCondiction.CHOSEN_PLAYER_IS_NOT_OUT_ELECTING), 
								  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	GET_LIST_ROOMS = (10, 'Get List Rooms', ActionRw.READ, 
					  tuple(), 
					  tuple(), 
					  ActionGroup.NONE, ActionGroup.NONE)

	GET_ROOM_DATA_TABLE = (11, 'Get Room Data Table', ActionRw.READ, 
						   (ActionParam.ROOM_ID,), 
						   (ActionCondiction.ROOM_EXISTS,), 
						   ActionGroup.ROOM_OWNER, ActionGroup.ROOM_OWNER)

	KICK_PLAYER_ROOM = (12, 'Kick Player of Room', ActionRw.WRITE, 
						(ActionParam.ROOM_ID, ActionParam.SOCKET_IP), 
						(ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_OWNER_ROOM,
							ActionCondiction.ROOM_STATUS_IN_WAIT, ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM), 
						ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	START_ROOM_GAME = (13, 'Start Room Game', ActionRw.WRITE, 
					   (ActionParam.ROOM_ID,), 
					   (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_OWNER_ROOM, 
					   	ActionCondiction.ROOM_STATUS_IN_WAIT, ActionCondiction.CAN_START_GAME), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	INCREMENT_GAME_PHASE = (14, 'Increment Game Phase', ActionRw.WRITE, 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_OWNER_ROOM, 
								ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.TIME_IS_UP), 
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	INCREMENT_GAME_ROUND = (15, 'Increment Game Round', ActionRw.WRITE, 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_OWNER_ROOM,
								ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.GAME_IS_RESULT_ROUND,
								ActionCondiction.TIME_IS_UP),
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	BE_ROOM_OWNER = (16, 'Be Room Owner', ActionRw.WRITE, 
					 (ActionParam.ROOM_ID,), 
					 (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_INSIDE_ROOM,
					 	ActionCondiction.ROOM_STATUS_IN_GAME, ActionCondiction.PLAYER_CAN_BE_OWNER), 
					 ActionGroup.ALL_NETWORK, ActionGroup.ROOM_PLAYERS)

	SEND_MASTER_ANSWER = (17, 'Send Master Answer', ActionRw.WRITE, 
						  (ActionParam.ROOM_ID, ActionParam.WORD_DIVISION),
						  (ActionCondiction.ROOM_EXISTS, ActionCondiction.PLAYER_IS_ROUND_MASTER,
						  	ActionCondiction.GAME_IS_WAITING_ANSWERS,  ActionCondiction.TIME_IS_UP), 
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

	def __repr__(self):
		return f'{self.__class__.__name__}.{self.name}'

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
