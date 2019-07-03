import console as Console

class ConsoleRectangle:
	def __init__(self, position, width, height, borderColor=Console.CONSOLE_COLOR):
		self.width = width
		self.height = height
		self.position = position
		self.x, self.y = position
		self.borderColor = borderColor

	def draw(self):
		line = '┌'
		space = ''
		temp = ''
		for _ in range(self.width):
			space += ' '
			line += '─'

		for _ in range(self.x - 1):
			temp += ' '

		line += '┐' + '\n'
		
		for _ in range(self.height):
			line += temp + '│' + space + '│' + '\n'

		line += temp + '└'
		for _ in range(self.width):
			line += '─'

		line += '┘' + '\n'

		Console.moveCursor(self.x, self.y)
		Console.setColor(self.borderColor)
		print(line)
		Console.resetColor()


if __name__ == '__main__':
	import colorama
	colorama.init()

	ConsoleRectangle((5, 5), 30, 10, (255, 255, 255)).draw()