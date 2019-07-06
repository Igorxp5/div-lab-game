import time

from . import console as Console
from .console_input import ConsoleInput
from .console_rectangle import ConsoleRectangle

from threading import Lock

class ConsoleChat:
	def __init__(self):
		self._lines = []
		self._height = Console.CONSOLE_HEIGHT - 7
		self._width = Console.CONSOLE_WIDTH - 4
		self._inputPosition = 2, Console.CONSOLE_HEIGHT - 4
		self._input = ConsoleInput(self._inputPosition, Console.CONSOLE_WIDTH - 4)

	def start(self):
		ConsoleRectangle((2, 1), self._width, self._height).draw()
		self._input.draw()


	def input(self):
		self._input.start()
		text = self._input.getText()
		self._input.clearText()
		return text

	def putLine(self, lines, breakLineBefore=False, breakLineAfter=False):
		if breakLineBefore:
			self._lines.append('')

		lines = str(lines)
		for line in lines.split('\n'):
			line = line.replace('\n', '')
			if line: 
				self._lines.append(line)

		if breakLineAfter:
			self._lines.append('')
		
		currentPosition = Console.cursorPosition()
		Console.moveCursor(5, 2)
		start = None
		if len(self._lines) <= self._height:
			start = 0
		else:
			start = len(self._lines) - self._height

		lineNumber = 0
		for i in range(start, len(self._lines)):
			print(f'{self._lines[i]}')
			lineNumber += 1
			Console.moveCursor(5, 2 + lineNumber)

		Console.moveCursor(*currentPosition)

	def moveCursorOut(self):
		x, y = self._inputPosition[0], self._inputPosition[1] + 3
		Console.moveCursor(x, y)


if __name__ == '__main__':
	import colorama
	
	colorama.init()
	
	chat = ConsoleChat()
	chat.start()
	while True:
		text = chat.input()
		chat.putLine(text)
	while True: pass

