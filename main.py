from game_client import GameClient, getAllIpAddress
from frontend.rooms import RoomsWindow

interfaces = getAllIpAddress()
print('Interface disponíveis: ')
for i, ip in enumerate(interfaces):
	print(f'{i} - {ip}')
number_interface = int(input('\nSelecione a interface: '))
gameClient = GameClient(interfaces[number_interface])
gameClient.start()

RoomsWindow.startWindow(gameClient)