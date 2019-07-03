import console

from console_chat import ConsoleChat

from threading import Thread

console.init()

def runProcess(exe):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        # returns None while subprocess is running
        retcode = p.poll() 
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break

def readProcessLines(chat):
    for line in runProcess('venv/Scripts/python game_client.py'):
        chat.putLine(line)

def command(command_):

Thread(readProcessLines, daemon=True).start()

chat = ConsoleChat()
chat.start()
while True:
    text = chat.input()





# print(Fore.RED + 'some red text')

# print('F' * 1000)
# time.sleep(3)
# print("\033c")
# print("\n" * get_terminal_size().lines, end='')
# text = input('Digite alguma coisa: ')
# print("\n" * get_terminal_size().lines, end='')
# print('coisa')