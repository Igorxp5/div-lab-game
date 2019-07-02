def gameController(game):
	# game.createRoom('Sala de Teste', 2, 'Igorxp5')
	# print(game.getAvailableRooms())
	# game.joinRoomToPlay(list(game.getAvailableRooms().keys())[0], 'Igorxp5')
	# game.quitRoom()
	# game.startGame()
	game.voteRoundMaster(game.getCurrentRoom().getPlayers()[0])
	# game.chooseRoundWord('bola', 'bo-la')
	# game.answerRoundWord('bo-la-la')
	# game.contestCorrectAnswer()
	pass
