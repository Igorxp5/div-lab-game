# from room import RoomStatus
# from game import GamePhase
from enum import Enum

class ActionGroup(Enum):
	ALL_NETWORK = 0
	ROOM_PLAYERS = 1
	ONE_PLAYER = 2
	ROOM_OWNER = 3


class ActionParam(Enum):
	ROOM_NAME = 'room_name'
	PLAYERS_LIMIT = 'players_limit'
	ROOM_ID = 'room_id'
	PLAYER_NAME = 'player_name'
	WORD_STRING = 'word_string'
	WORD_DIVISION = 'word_division'
	SOCKET_ID = 'socket_id'

	def __str__(self):
		return self.value


class ActionCondiction(Enum):
	ROOM_STATUS_IN_GAME = lambda network, socketId, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).roomStatus is RoomStatus.IN_GAME
	)
	ROOM_STATUS_IN_WAIT = lambda network, socketId, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).roomStatus is RoomStatus.IN_WAIT
	)
	PLAYER_NOT_IN_ROOM = lambda network, socketId, rooms, game, params: (
		all((socketId not in room.players for room in rooms))
	)
	PLAYER_INSIDE_ROOM = lambda network, socketId, rooms, game, params: (
		socketId in rooms.get(params[ActionParam.ROOM_ID]).players
	)
	PLAYER_IS_OWNER_ROOM = lambda network, socketId, rooms, game, params: (
		rooms.get(params[ActionParam.ROOM_ID]).owner.socket.id == socketId
	)
	PLAYER_IS_MASTER_ROOM = lambda network, socketId, rooms, game, params: (
		game and game.roundMaster and game.roundMaster.socket.id == socketId
	)
	PLAYER_IS_NOT_MASTER_ROOM = lambda network, socketId, rooms, game, params: (
		game and game.roundMaster and game.roundMaster.socket.id != socketId
	)
	TIME_NOT_IS_UP = lambda network, socketId, rooms, game, params: (
		game and game.phaseTime and game.phaseTime == 0
	)
	TIME_IS_UP = lambda network, socketId, rooms, game, params: (
		game and game.phaseTime and game.phaseTime < 800
	)
	GAME_IS_WAITING_CONTESTS = lambda network, socketId, rooms, game, params: (
		game and game.phase is GamePhase.WAITING_CONTESTS
	)
	GAME_IS_ELECTING_MASTER_ROOM = lambda network, socketId, rooms, game, params: (
		game and game.phase is GamePhase.ELECTING_MASTER_ROOM
	)
	GAME_IS_ELECTING_CORRECT_ANSWER = lambda network, socketId, rooms, game, params: (
		game and game.phase is GamePhase.ELECTING_CORRECT_ANSWER
	)
	GAME_IS_WAITING_ANSWERS = lambda network, socketId, rooms, game, params: (
		game and game.phase is GamePhase.WAITING_ANSWERS
	)
	GAME_IS_RESULT_ROUND = lambda network, socketId, rooms, game, params: (
		game and game.phase is GamePhase.RESULT_ROUND
	)
	PLAYER_MISSED_ANSWER = lambda network, socketId, rooms, game, params: (
		socketId in game.roundAnswers and game.roundAnswers.get(socketId) == game.roundWord
	)
	CHOSEN_PLAYER_IS_IN_ROOM = lambda network, socketId, rooms, game, params: (
		socketId in rooms.get(params[ActionParam.ROOM_ID]).players
		and params[ActionParam.SOCKET_ID] in rooms.get(params[ActionParam.ROOM_ID]).players
	)
	CHOSEN_PLAYER_IS_NOT_MASTER_ROOM = lambda network, socketId, rooms, game, params: (
		game and game.roundMaster and game.roundMaster.socket.id == params[ActionParam.SOCKET_ID]
	)
	CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_MASTER_ROOM = lambda network, socketId, rooms, game, params: (
		game and (
			(game.roundMaster and game.roundMaster.socket.id == params[ActionParam.SOCKET_ID])
			or (game.contestingPlayer and game.contestingPlayer.socket.id == params[ActionParam.SOCKET_ID])
		)
	)
	PLAYER_CAN_BE_OWNER = lambda network, socketId, rooms, game, params: (
		# TODO: Falta verificar se o jogador está desconectado
		rooms.get(params[ActionParam.ROOM_ID]).players.index(socketId) == 1
	)

	def __call__(self, p2p, socketId, rooms, game, params):
		return bool(self.value(socketId, rooms, game, params))


class Action(Enum):
	CREATE_ROOM = (1, 'Create Room', 'w', 
				   (ActionParam.ROOM_NAME, ActionParam.PLAYERS_LIMIT), 
				   (ActionCondiction.PLAYER_NOT_IN_ROOM,), 
				   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	JOIN_ROOM_PLAY = (2, 'Join into Room to Play', 'w', 
					  (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					  (ActionCondiction.PLAYER_NOT_IN_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					  ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	JOIN_ROOM_WATCH = (3, 'Join into Room to Watch', 'w', 
					   (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
					   (ActionCondiction.PLAYER_NOT_IN_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ROOM_OWNER)

	CHOOSE_ROUND_WORD = (4, 'Choose Round Word', 'w',
						 (ActionParam.ROOM_ID, ActionParam.WORD_STRING), 
						 (ActionCondiction.PLAYER_IS_MASTER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						 	ActionCondiction.TIME_NOT_IS_UP), 
						 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CONTEST_WORD = (5, 'Contest Word', 'w', 
					(ActionParam.ROOM_ID,),
					(ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						ActionCondiction.GAME_IS_WAITING_CONTESTS, ActionCondiction.TIME_NOT_IS_UP,
						ActionCondiction.PLAYER_MISSED_ANSWER), 
					ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	
	QUIT_ROOM = (6, 'Quit Room', 'w', 
				 (ActionParam.ROOM_ID,), 
				 (ActionCondiction.PLAYER_INSIDE_ROOM,), 
				 ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	CHOOSE_VOTE_ELECTION_ROUND_MASTER = (7, 'Choose Vote Election Round Master', 'w', 
										 (ActionParam.ROOM_ID, ActionParam.SOCKET_ID), 
										 (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
										 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM, ActionCondiction.GAME_IS_ELECTING_MASTER_ROOM,
										 	ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.CHOSEN_PLAYER_IS_NOT_MASTER_ROOM), 
										 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	SEND_PLAYER_ANSWER = (8, 'Send Player Answer', 'w', 
						  (ActionParam.ROOM_ID, ActionParam.WORD_DIVISION), 
						  (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						  	ActionCondiction.GAME_IS_WAITING_ANSWERS, ActionCondiction.TIME_NOT_IS_UP,
						  	ActionCondiction.PLAYER_IS_NOT_MASTER_ROOM), 
						  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CHOOSE_VOTE_CONTEST_ANSWER = (9, 'Choose Vote Contest Answer', 'w', 
								  (ActionParam.ROOM_ID, ActionParam.SOCKET_ID), 
								  (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM, ActionCondiction.GAME_IS_ELECTING_CORRECT_ANSWER,
								 	ActionCondiction.TIME_NOT_IS_UP, ActionCondiction.CHOSEN_PLAYER_IS_CONTESTING_ANSWER_OR_MASTER_ROOM), 
								  ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	GET_DATA_TABLE = (10, 'Get Data Table', 'r', 
					  tuple(), 
					  tuple(), 
					  ActionGroup.ONE_PLAYER, ActionGroup.ONE_PLAYER)

	GET_ROOM_DATA_TABLE = (11, 'Get Room Data Table', 'r', 
						   (ActionParam.ROOM_ID,), 
						   tuple(), 
						   ActionGroup.ROOM_OWNER, ActionGroup.ROOM_OWNER)

	KICK_PLAYER_ROOM = (12, 'Kick Player of Room', 'w', 
						(ActionParam.ROOM_ID, ActionParam.SOCKET_ID), 
						(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT,
						 	ActionCondiction.CHOSEN_PLAYER_IS_IN_ROOM), 
						ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	START_ROOM_GAME = (13, 'Start Room Game', 'w', 
					   (ActionParam.ROOM_ID,), 
					   (ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_WAIT), 
					   ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)

	INCREMENT_GAME_PHASE = (14, 'Increment Game Phase', 'w', 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								ActionCondiction.TIME_IS_UP), 
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	INCREMENT_GAME_ROUND = (15, 'Increment Game Round', 'w', 
							(ActionParam.ROOM_ID,), 
							(ActionCondiction.PLAYER_IS_OWNER_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
								ActionCondiction.GAME_IS_RESULT_ROUND, ActionCondiction.TIME_IS_UP),
							ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	BE_ROOM_OWNER = (16, 'Be Room Owner', 'w', 
					 (ActionParam.ROOM_ID,), 
					 (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						ActionCondiction.PLAYER_CAN_BE_OWNER), 
					 ActionGroup.ALL_NETWORK, ActionGroup.ROOM_PLAYERS)

	SEND_MASTER_ANSWER = (17, 'Send Master Answer', 'w', 
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

if __name__ == '__main__':
	packetAction = Action.CHOOSE_ROUND_WORD
	print(packetAction.params)
