import subprocess
from utils.console import *

init()

def drawInputBox():
	for x in range(CONSOLE_WIDTH + 1):
		move_cursor(x, CONSOLE_HEIGHT - 1)
		print('_', end='')

drawInputBox()
# command = input('[COMMAND HERE] -> ')

def runProcess(exe):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        # returns None while subprocess is running
        retcode = p.poll() 
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break
move_cursor(0, 0)
for line in runProcess('python game_client.py'):
	print(line)

# print(Fore.RED + 'some red text')

# print('F' * 1000)
# time.sleep(3)
# print("\033c")
# print("\n" * get_terminal_size().lines, end='')
# text = input('Digite alguma coisa: ')
# print("\n" * get_terminal_size().lines, end='')
# print('coisa')