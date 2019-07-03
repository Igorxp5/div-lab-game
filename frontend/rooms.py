import sys
#from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QMainWindow, QPushButton, QLineEdit, QInputDialog, QApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize 

from game_client import Action, ActionError, GameActionError
from frontend.dialog import Dialog 

class RoomsWindow(QMainWindow):
    def __init__(self, gameClient):
        self.gameClient = gameClient

        self.dialog = Dialog()

        QMainWindow.__init__(self)

        self.gameClient.setListenPacketCallbackByAction(Action.GET_LIST_ROOMS, self._getListRoomsCallback)
        self.gameClient.setListenPacketCallbackByAction(Action.CREATE_ROOM, self._getListRoomsCallback)
        
        #janela
        self.resize(1000, 600)
        self.qtRectangle = self.frameGeometry()
        self.setMinimumSize(self.sizeHint())    
        self.setWindowTitle("Salas | DivLab Game")
        '''
        #título
        title = QLabel(self)
        title.setText('DIVLAB GAME') 
        title.setStyleSheet("font: 30pt Comic Sans MS")
        title.resize(200, 32)
        title.move(10, 10)
        '''
        #texto informativo
        self.text = QLabel(self)
        self.text.setText('Para começar a jogar escolha um apelido, e entre em alguma das salas criadas pelos outros jogadores. Você também pode criar uma nova sala e aguardar seus colegas de jogo entrarem.')
        self.text.setWordWrap(True) 
        self.text.move(20, 10)   
        self.text.setMinimumSize(1000, 32)

        #Caixa de texto de criar apelido
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Apelido:')
        self.line = QLineEdit(self)        
        self.line.move(180, 100)
        self.line.resize(200, 32)
        self.nameLabel.move(120, 100)

        #Botão de criar sala
        createRoomButton = QPushButton('Criar sala', self)
        createRoomButton.clicked.connect(self._createRoom)
        createRoomButton.resize(200, 32)
        createRoomButton.move(400, 550)

        #Botão de entrar na sala
        logInRoomButton = QPushButton('Entrar', self)
        logInRoomButton.clicked.connect(self._joinRoom) #add a função de abrir as caixas de dialogo
        logInRoomButton.resize(200, 32)
        logInRoomButton.move(630, 385)

        #Lista de salas (add qtd de jogadores na mesma string)
        self.listView = myListWidget(self)        

        #listView.clicked.connect() add função de clique
        self.listView.move(150, 300)
        self.listView.resize(450, 200)

    def _getListRoomsCallback(self, socket, params, actionError):
        if actionError == ActionError.NONE:
            self.listView.clear()
            for room in self.gameClient.getAvailableRooms().values():
                roomName = room.getName()
                self.listView.addItem(roomName)
        else:
            self.dialog.generic('Erro', actionError.message)

    def _createRoom(self):
        pass


    def _joinRoom(self):
        playerName = self.line.text()

        try:

            if len(playerName) == 0:
                self.dialog.generic('Campo Obrigatório', 'Escreva um apelido.')
            else:
                roomName = self.listView.currentItem().text()
                if len(roomName) == 0:
                    self.dialog.generic('Campo Obrigatório', 'Escolha uma sala')
                else:
                    room = self.gameClient.getRoomByName(roomName)
                    print(room)
                    self.gameClient.joinRoomToPlay(room, playerName)

        except GameActionError as e:
            self.dialog.generic('Erro', e.actionError.message)


    @staticmethod
    def startWindow(gameClient,*args):
        gameClient.blockUntilConnectToNetwork()
        app = QtWidgets.QApplication(list(args))
        mainWin = RoomsWindow(gameClient, *args)
        mainWin.show()
        sys.exit( app.exec_() )

#Ação de clicar em um item da lista
class myListWidget(QListWidget):
   def Clicked(self):
      item = self.listwidget.currentItem()
      QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())