import sys
#from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QMainWindow, QPushButton, QLineEdit, QInputDialog, QApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize    

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
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
        
        #Botão de criar apelido
        pybutton = QPushButton('OK', self)
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(200, 32)
        pybutton.move(380, 100)

        #Botão de criar sala
        createRoomButton = QPushButton('Criar sala', self)
        createRoomButton.clicked.connect(self.clickMethod)
        createRoomButton.resize(200, 32)
        createRoomButton.move(400, 550)
    
        #Botão de assistir partida
        watchRoomButton = QPushButton('Assistir', self)
        watchRoomButton.clicked.connect(self.clickMethod)
        watchRoomButton.resize(200, 32)
        watchRoomButton.move(630, 350)

        #Botão de entrar na sala
        logInRoomButton = QPushButton('Entrar', self)
        logInRoomButton.clicked.connect(self.clickMethod) #add a função de abrir as caixas de dialogo
        logInRoomButton.resize(200, 32)
        logInRoomButton.move(630, 385)

        #Lista de salas (add qtd de jogadores na mesma string)
        listView = myListWidget(self)
        listView.addItem("Sala 1")
        listView.addItem("Sala 2")
        listView.addItem("Sala 3")
        listView.addItem("Sala 4")
        listView.addItem("Sala 5")
        listView.addItem("Sala 6")
        listView.addItem("Sala 7")
        listView.addItem("Sala 8")
        listView.addItem("Sala 9")
        listView.addItem("Sala 10")
        listView.addItem("Sala 11")
        listView.addItem("Sala 12")
        #listView.clicked.connect() add função de clique
        listView.move(150, 300)
        listView.resize(450, 200)

    def clickMethod(self):
        print('Your name: ' + self.line.text())

#Ação de clicar em um item da lista
class myListWidget(QListWidget):
   def Clicked(self):
      item = self.listwidget.currentItem()
      QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit( app.exec_() )