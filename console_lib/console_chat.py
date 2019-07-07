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
		self._linesOffset = 0
		self._maxLengthLine = self._width - 4
		self._marginX, self._marginY = 5, 2 

		self._input.setKeyArrowsCallback(self._keyArrowsCallback)

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
		
		start = None
		if len(self._lines) <= self._height:
			start = 0
		else:
			start = len(self._lines) - self._height

		self._showLines(start)

		self._linesOffset = len(self._lines) - self._height

	def moveCursorOut(self):
		x, y = self._inputPosition[0], self._inputPosition[1] + 3
		Console.moveCursor(x, y)

	def clear(self):
		currentPosition = Console.cursorPosition()
		Console.moveCursor(self._marginX, self._marginY)

		lineNumber = 0
		for _ in range(self._height):
			print(' ' * self._maxLengthLine)
			lineNumber += 1
			Console.moveCursor(self._marginX, self._marginY + lineNumber)

		Console.moveCursor(*currentPosition)

	def _showLines(self, offset):
		self.clear()

		currentPosition = Console.cursorPosition()
		Console.moveCursor(self._marginX, self._marginY)

		lineNumber = 0
		end = min(offset + self._height, len(self._lines))
		for i in range(offset, end):
			print(f'{self._lines[i]}')
			lineNumber += 1
			Console.moveCursor(self._marginX, self._marginY + lineNumber)

		Console.moveCursor(*currentPosition)

	def _keyArrowsCallback(self, key):
		if key[0] == 72: # Up
			self._linesOffset = max(0, self._linesOffset - 1)
			self._showLines(self._linesOffset)
		elif key[0] == 80: # Down
			self._linesOffset = min(self._linesOffset + 1, len(self._lines) - self._height)
			self._showLines(self._linesOffset)


if __name__ == '__main__':
	import colorama
	
	colorama.init()
	
	chat = ConsoleChat()
	chat.start()
	while True:
		text = chat.input()
		chat.putLine(text)
	while True: pass

