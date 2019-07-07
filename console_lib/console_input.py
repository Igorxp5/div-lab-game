import time
import msvcrt
from . import console as Console

from .console_rectangle import ConsoleRectangle

class ConsoleInput:
    def __init__(self, position, width=15, height=1, maxLength=None):
        self.maxLengthVisible = width - 2
        self.maxLength = maxLength
        self.inputWidth = width
        self.inputHeight = height
        self.inputPosition = position
        self.x, self.y = position

        self._inputRectangle = None
        self._currentText = ''
        self._visibleText = ''
        self._lastText = ''

        self._updateIntervalTime = 0.005

        self._cursorTextPosition = 0
        self._keyArrowsCallback = None

    def draw(self):
        self._inputRectangle = ConsoleRectangle(
            self.inputPosition, self.inputWidth, self.inputHeight
        )
        self._inputRectangle.draw()

    def start(self):
        self.moveToStartPosition()
        self._capture()

    def setKeyArrowsCallback(self, callback):
        self._keyArrowsCallback = callback

    def currentPosition(self):
        return self.x + 2 + self._cursorTextPosition, self.y + 1 

    def moveToStartPosition(self):
        Console.moveCursor(self.x + 2, self.y + 1)

    def _capture(self):
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b'\x08':
                    if len(self._currentText) - 1 >= 0:
                        self._currentText = self._currentText[:self._cursorTextPosition - 1] + self._currentText[self._cursorTextPosition:]
                        self._cursorTextPosition -= 1
                elif len(self._currentText) == self.maxLength and self.maxLength != -1:
                    continue
                elif key == b'\r':
                    return
                elif key == b'\xe0':
                    key = msvcrt.getch()

                    if key[0] in (72, 77, 80, 75):
                        if key[0] == 77: # Right
                            self._cursorTextPosition = min(self._cursorTextPosition + 1, len(self._currentText))
                        elif key[0] == 75: # Left
                            self._cursorTextPosition = max(0, self._cursorTextPosition - 1)

                        if self._keyArrowsCallback:
                            self._keyArrowsCallback(key)
                    elif key == b'G': # Home
                        self._cursorTextPosition = 0
                    elif key == b'O': # End
                        self._cursorTextPosition = len(self._currentText)
                    elif key == b'S': # Delete
                        if len(self._currentText) - 1 >= 0:
                            self._currentText = self._currentText[:self._cursorTextPosition] + self._currentText[self._cursorTextPosition + 1:]
                    Console.moveCursor(*self.currentPosition())
                elif key:
                    try:
                        self._currentText = (self._currentText[:self._cursorTextPosition] 
                                        + key.decode('utf-8') + self._currentText[self._cursorTextPosition:])
                        self._cursorTextPosition += 1
                    except:
                        continue

            
            if self._lastText == self._currentText: 
                continue


            self.moveToStartPosition()

            for _ in range(self.maxLengthVisible):
                print(' ', end='')

            if len(self._currentText) > self.maxLengthVisible:
                self._visibleText = ''

                c = len(self._currentText) - self.maxLengthVisible
                for i in range(self.maxLengthVisible):
                    self._visibleText += self._currentText[c + i]
            else:
                self._visibleText = self._currentText

            self.moveToStartPosition()

            print(self._visibleText, end='')

            Console.moveCursor(*self.currentPosition())

            self._lastText = self._currentText

            time.sleep(self._updateIntervalTime)

    def getText(self):
        return self._currentText

    def clearText(self):
        currentPosition = Console.cursorPosition()
        self.moveToStartPosition()

        for _ in range(self.maxLengthVisible):
            print(' ', end='')

        self._currentText = ''
        self._visibleText = ''
        self._lastText = ''
        self._cursorTextPosition = 0

        Console.moveCursor(*currentPosition)


if __name__ == '__main__':
    import colorama

    colorama.init()

    consoleInput = ConsoleInput((2, Console.CONSOLE_HEIGHT - 4), Console.CONSOLE_WIDTH - 5)
    consoleInput.draw()
    consoleInput.start()