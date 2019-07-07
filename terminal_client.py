import re
import sys
import time
import logging

from enum import Enum
from threading import Thread, Event

from console_lib import console
from console_lib.console_chat import ConsoleChat

from game_client import GameClient, GameClientLog, GameActionError, getAllIpAddress

class ChatLogTag(Enum):
    GAME_CLIENT = ('game_client', '', False, False)
    NETWORK = ('network.network', 'Rede', False, True)
    DISCOVERY_SERVICE = ('network.discovery_service', 'Rede', True, False)

    def __init__(self, module, title, breakLineBefore, breakLineAfter):
        self.module = module
        self.title = title
        self.breakLineBefore = breakLineBefore
        self.breakLineAfter = breakLineAfter

    @staticmethod
    def getByName(module):
        for tag in ChatLogTag:
            if module == tag.module:
                return tag
        raise NotImplementedError(f'not found {module}.')

class ChatLogFormatter(logging.Formatter):
    def format(self, record):
        tag = ChatLogTag.getByName(record.name)
        if tag is ChatLogTag.GAME_CLIENT:
            if record.args[0] == GameClientLog.GENERAL:
                socket = record.msg
                socketString = f'{socket.ip}' 
                message = record.args[1]
                return f'[{socketString}]: {message}'
            print(record.args)
        return f'[{tag.title}]: {record.msg}'

class ChatLogHandler(logging.StreamHandler):
    def __init__(self, consoleChat, level=logging.INFO):
        super().__init__(level)
        self._consoleChat = consoleChat

    def emit(self, record):
        tag = ChatLogTag.getByName(record.name)
        message = self.format(record)
        consoleChat.putLine(message, 
                            breakLineBefore=tag.breakLineBefore,
                            breakLineAfter=tag.breakLineAfter)

class GameChatCommand(Enum):
    CREATE_ROOM = ('create-room', (str, int, str), (None, None, None),
                    lambda game, roomName, limit, playerName: (
                        game.createRoom(roomName, limit, playerName)
                    )
                  )
    JOIN_ROOM = ('join-room', (str, str), (None, None),
                    lambda game, roomName, playerName: (
                        game.joinRoomToPlay(game.getRoomByName(roomName), playerName)
                    )
                  )

    def __init__(self, alias, argTypes, argFilters, func):
        self._alias = alias
        self._argTypes = argTypes
        self._argFilters = argFilters
        self._totalArgs = len(self._argTypes)
        self._func = func

    def __call__(self, gameClient, *args):
        if len(args) != len(self._argTypes):
            raise RuntimeError(f'O comando necessita de {self._totalArgs} argumentos.')
        args = self.type(args)
        args = self.filter(args)
        self._func(gameClient, *args)

    def type(self, args):
        return tuple(self._argTypes[i](args[i]) for i in range(self._totalArgs))

    def filter(self, args):
        result = []
        for i in range(self._totalArgs):
            if self._argFilters[i]:
                arg = self._argFilters[i](args[i])
            else:
                arg = args[i]
            result.append(arg)
        return tuple(result)

    @staticmethod
    def getByAlias(alias):
        for command in GameChatCommand:
            if alias == command._alias:
                return command
        raise NotImplementedError

    @staticmethod
    def getCommand(gameClient, text):
        words = re.split(r'\s+(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)', commandText)
        alias, args = words[0], words[1:]
        args = tuple(re.sub(r'\'|\"', '', arg) for arg in args)
        command = GameChatCommand.getByAlias(alias)
        return command, args


consoleChat = ConsoleChat()
consoleChat.start()

consoleChatLogFormatter = ChatLogFormatter()
consoleChatLogHandler = ChatLogHandler(consoleChat)
consoleChatLogHandler.setFormatter(consoleChatLogFormatter)
logging.basicConfig(level=logging.INFO, handlers=(consoleChatLogHandler,))

try:
    interfaces = getAllIpAddress()
    consoleChat.putLine('[Cliente]: Escolha a interface que você deseja para iniciar o jogo:')
    for i, ip in enumerate(interfaces):
        consoleChat.putLine(f'         {i} - {ip}')

    numberInterface = int(consoleChat.input())

    gameClient = GameClient(interfaces[numberInterface], daemon=True)
    gameClient.start()

    gameClient.blockUntilNetworkReady()
    
    while True:
        try:
            commandText = consoleChat.input()
            command, args = GameChatCommand.getCommand(gameClient, commandText)
            command(gameClient, *args)
        except GameActionError as error:
            consoleChat.putLine(f'[Erro]: {error}', breakLineAfter=True)
except KeyboardInterrupt:
    consoleChat.putLine('[Cliente]: O Cliente foi encerrado.', breakLineBefore=True)
    consoleChat.moveCursorOut()