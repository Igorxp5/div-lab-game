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
	WORD_DIVISION = 'word_division',
	VOTE_PLAYER = 'vote_player'
	VOTE_CONTEST_ANSWER = 'vote_contest_answer'
	PLAYER_ID = 'player_id'

	def __str__(self):
		return self.value


class ActionCondiction(Enum):
	ROOM_STATUS_IN_GAME = lambda socket, player, rooms, game, params: (
		rooms[params[ActionParam.ROOM_ID]].room_status == RoomStatus.IN_GAME
	)
	ROOM_STATUS_IN_WAIT = lambda socket, player, rooms, game, params: (
		rooms[params[ActionParam.ROOM_ID]].room_status == RoomStatus.IN_WAIT
	)
	PLAYER_NOT_IN_ROOM = lambda socket, player, rooms, game, params: (
		player is None
	)
	PLAYER_INSIDE_ROOM = lambda socket, player, rooms, game, params: (
		player and player in rooms[params[ActionParam.ROOM_ID]].players
	)
	PLAYER_IS_MASTER_ROOM = lambda socket, player, rooms, game, params: (
		player and player in rooms[params[ActionParam.ROOM_ID]].players
		and game.round_master is player
	)
	TIME_NOT_IS_UP = lambda socket, player, rooms, game, params: (
		game and game.phase_time > 0
	)

	def __init__(self, condition_test):
		self.condition_test = condition_test

	def __call__(self, socket, player, rooms, game, params):
		return bool(self.condition_test(socket, player, rooms, game, params))


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
						 (ActionParam.ROOM_ID, ActionParam.PLAYER_NAME), 
						 (ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME,
						 	ActionCondiction.PLAYER_IS_MASTER_ROOM, ActionCondiction.TIME_NOT_IS_UP), 
						 ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	CONTEST_WORD = (5, 'Contest Word', 'w', 
					(ActionParam.ROOM_ID,),
					(ActionCondiction.PLAYER_INSIDE_ROOM, ActionCondiction.ROOM_STATUS_IN_GAME), 
					ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	
	QUIT_ROOM = (6, 'Quit Room', 'w', None, None, ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)
	CHOOSE_VOTE_ELECTION_ROUND_MASTER = (7, 'Choose Vote Election Round Master', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	SEND_PLAYER_ANSWER = (8, 'Send Player Answer', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	CHOOSE_VOTE_CONTEST_ANSWER = (9, 'Choose Vote Contest Answer', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	GET_DATA_TABLE = (10, 'Get Data Table', 'r', None, None, ActionGroup.ONE_PLAYER, ActionGroup.ONE_PLAYER)
	GET_ROOM_DATA_TABLE = (11, 'Get Room Data Table', 'r', None, None, ActionGroup.ROOM_OWNER, ActionGroup.ROOM_OWNER)
	KICK_PLAYER_ROOM = (12, 'Kick Player of Room', 'w', None, None, ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)
	START_ROOM_GAME = (13, 'Start Room Game', 'w', None, None, ActionGroup.ALL_NETWORK, ActionGroup.ALL_NETWORK)
	INCREMENT_GAME_PHASE = (14, 'Increment Game Phase', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	INCREMENT_GAME_ROUND = (15, 'Increment Game Round', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	BE_ROOM_OWNER = (16, 'Be Room OWner', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)
	SEND_MASTER_ANSWER = (17, 'Send Master Answer', 'w', None, None, ActionGroup.ROOM_PLAYERS, ActionGroup.ROOM_PLAYERS)

	def __init__(self, id, description, 
				 rw, params, conditions,
				 receiver_group, approvation_group):
		self.id = id
		self.description = description
		self.rw = rw
		self.params = params
		self.conditions = conditions
		self.receiver_group = receiver_group
		self.approvation_group = approvation_group

	@property
	def codename(self):
		return 'AC{:03d}'.format(self.id)

if __name__ == '__main__':
	packet_action = Action.CHOOSE_ROUND_WORD
	print(packet_action.params)
