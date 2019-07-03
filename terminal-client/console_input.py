import time
import msvcrt
import console as Console

from console_rectangle import ConsoleRectangle

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

    def draw(self):
        self._inputRectangle = ConsoleRectangle(
            self.inputPosition, self.inputWidth, self.inputHeight
        )
        self._inputRectangle.draw()

    def start(self):
        self._moveToStartPosition()
        self._capture()

    def _moveToStartPosition(self):
        Console.moveCursor(self.x + 2, self.y + 1)

    def _capture(self):
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b'\x08':
                    self._currentText = self._currentText[:-1] if len(self._currentText) - 1 >= 0 else self._currentText
                elif len(self._currentText) == self.maxLength and self.maxLength != -1:
                    continue
                elif key == b'\r':
                    return
                elif key:
                    try:
                        self._currentText += key.decode('utf-8')
                    except:
                        continue

            
            if self._lastText == self._currentText: 
                continue


            self._moveToStartPosition()

            for _ in range(self.maxLengthVisible):
                print(' ', end='')

            if len(self._currentText) > self.maxLengthVisible:
                self._visibleText = ''

                c = len(self._currentText) - self.maxLengthVisible
                for i in range(self.maxLengthVisible):
                    self._visibleText += self._currentText[c + i]
            else:
                self._visibleText = self._currentText

            self._moveToStartPosition()

            print(self._visibleText, end='')

            Console.moveCursor(self.x + 2 + len(self._visibleText), self.y + 1)

            self._lastText = self._currentText

            time.sleep(self._updateIntervalTime)

    def getText(self):
        return self._currentText

    def clearText(self):
        self._moveToStartPosition()

        for _ in range(self.maxLengthVisible):
            print(' ', end='')

        self._currentText = ''
        self._visibleText = ''
        self._lastText = ''


if __name__ == '__main__':
    import colorama

    colorama.init()

    consoleInput = ConsoleInput((2, Console.CONSOLE_HEIGHT - 4), Console.CONSOLE_WIDTH - 5)
    consoleInput.draw()
    consoleInput.start()