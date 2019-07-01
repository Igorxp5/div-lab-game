import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize    

#---- CRONÔMETRO IMPLEMENTADO EM OUTRA CLASSE
class ContestationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
       #janela
        self.resize(1000, 600)
        self.qtRectangle = self.frameGeometry()
        self.setMinimumSize(self.sizeHint())    
        self.setWindowTitle("Sala X | DivLab Game")
        
        #título
        title = QLabel(self)
        title.setText('SALA X') 
        title.setStyleSheet("font: 30pt")
        title.resize(200, 32)
        title.move(10, 10)

        #texto nº de participantes
        self.text = QLabel(self)
        self.text.setText('Participantes:')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(50, 150)   
        self.text.setMinimumSize(1000, 32)

        #texto fase de eleição do organizador
        self.text = QLabel(self)
        self.text.setText('Fase: Contestação da Resposta')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(250, 150)   
        self.text.setMinimumSize(1000, 32)

        #texto nº da rodada
        self.text = QLabel(self)
        self.text.setText('Rodada: ' + 'X')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(800, 150)   
        self.text.setMinimumSize(1000, 32)

        #Botão de começar
        startButton = QPushButton('Começar', self)
        #startButton.clicked.connect(self.clickMethod)
        startButton.resize(200, 32)
        startButton.move(300, 550)
    
        #Botão de sair
        leaveButton = QPushButton('Sair', self)
        #leaveButton.clicked.connect(self.clickMethod)
        leaveButton.resize(200, 32)
        leaveButton.move(500, 550)

        #Lista de jogadores da sala
        # ----- COLOCAR ÍCONE AO LADO DE QUEM ESTA ASSISTINDO
        # ----- ESSA MESMA LISTA SERVIRÁ PARA VOTAR EM UM ORGANIZADOR DA PARTIDA
        listView = myListWidget(self)
        listView.addItem("Jogador 1")
        listView.addItem("Jogador 2")
        listView.addItem("Jogador 3")
        listView.addItem("Jogador 4")
        listView.addItem("Jogador 5")
        listView.addItem("Jogador 6")
        listView.addItem("Jogador 7")
        listView.addItem("Jogador 8")
        listView.addItem("Jogador 9")
        listView.addItem("Jogador 10")
        listView.addItem("Jogador 11")
        listView.addItem("Jogador 12")
        listView.addItem("Jogador 13")
        listView.addItem("Jogador 14")
        listView.addItem("Jogador 15")
        listView.addItem("Jogador 16")
        listView.addItem("Jogador 17")
        listView.addItem("Jogador 18")
        listView.addItem("Jogador 19")
        listView.addItem("Jogador 20")
        listView.addItem("Jogador 21")
        listView.addItem("Jogador 22")

        #listView.clicked.connect() add função de clique
        listView.move(50, 200)
        listView.resize(180, 300)

#Ação de clicar em um item da lista
class myListWidget(QListWidget):
   def Clicked(self):
      item = self.listwidget.currentItem()
      QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    contestationWin = ContestationWindow()
    contestationWin.show()
    sys.exit( app.exec_() )