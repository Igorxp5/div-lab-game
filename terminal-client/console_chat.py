import time
import console as Console

from console_rectangle import ConsoleRectangle
from console_input import ConsoleInput

class ConsoleChat:
	def __init__(self):
		self._lines = []
		self._height = Console.CONSOLE_HEIGHT - 7
		self._width = Console.CONSOLE_WIDTH - 5
		self._input = ConsoleInput((2, Console.CONSOLE_HEIGHT - 4), Console.CONSOLE_WIDTH - 5)

	def start(self):
		ConsoleRectangle((2, 1), self._width, self._height).draw()
		self._input.draw()


	def input(self):
		self._input.start()
		text = self._input.getText()
		self._input.clearText()
		return text

	def putLine(self, line):
		self._lines.append(line)
		Console.moveCursor(5, 2)
		start = 0 if len(self._lines) <= self._height else len(self._lines) - self._height
		lineNumber = 0
		for i in range(start, len(self._lines)):
			print(f'{self._lines[i]}')
			lineNumber += 1
			Console.moveCursor(5, 2 + lineNumber)


if __name__ == '__main__':
	import colorama
	
	colorama.init()
	
	chat = ConsoleChat()
	chat.start()
	while True:
		text = chat.input()
		chat.putLine(text)
	while True: pass

