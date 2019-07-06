import os
import ctypes
import colorama

CHAR_PIXEL = "█"

# Console width
console_size = os.get_terminal_size()
CONSOLE_WIDTH = console_size.columns
CONSOLE_HEIGHT = console_size.lines
CONSOLE_COLOR = 192, 192, 192

currentPosition = 0, 0

def init(*args, **kwargs):
    colorama.init(*args, **kwargs)

def setColor(rgb):
    colors = [str(i) for i in rgb]
    return "\033[38;2;" + ";".join(colors) + "m"


def resetColor():
    print("\033[0m", end="")
    return "\033[0m"


def stringColor(rgb, string):
    return setColor(rgb) + string + resetColor()


def cursorPosition():
    global currentPosition
    return currentPosition

def moveCursor(x, y):
    global currentPosition
    print("\033[%d;%dH" % (y, x), end="")
    currentPosition = x, y

def setConsoleFont(facename="Lucida Console", size=8,
                     dwFontsizeX=7, dwFontsizeY=14, fontfamily=54, fontWeight=400):

    global CONSOLE_WIDTH
    global CONSOLE_HEIGHT

    if os.name == "nt":
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class CONSOLE_FONT_INFOEX(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong),
                        ("nFont", ctypes.c_ulong),
                        ("dwFontSize", COORD),
                        ("FontFamily", ctypes.c_uint),
                        ("FontWeight", ctypes.c_uint),
                        ("FaceName", ctypes.c_wchar * 32)]

        font = CONSOLE_FONT_INFOEX()
        font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
        font.nFont = size
        font.dwFontSize.X = dwFontsizeX
        font.dwFontSize.Y = dwFontsizeY
        font.FontFamily = fontfamily
        font.FontWeight = fontWeight
        font.FaceName = facename

        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.SetCurrentConsoleFontEx(
            handle, ctypes.c_long(False), ctypes.pointer(font))

        CONSOLE_WIDTH = int(CONSOLE_WIDTH * (7 / dwFontsizeX))
        CONSOLE_HEIGHT = int(CONSOLE_HEIGHT * (14 / dwFontsizeY))

def setPixel(x, y, rgb):
	stringPixel = stringColor(rgb, CHAR_PIXEL)
	moveCursor(x, y)
	print(stringPixel)

def maximizeWindow():
	if os.name == "nt":
		hWnd = ctypes.windll.kernel32.GetConsoleWindow()
		ctypes.windll.user32.ShowWindow(hWnd, 3)