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
        title.setText('SALA ' + 'X') 
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
        self.text.setText('Fase: Contestação da resposta')
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

        #texto aguardando jogadores responderem
        self.text = QLabel(self)
        self.text.setText('Aguardando jogadores responderem')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(250, 300)   
        self.text.setMinimumSize(1000, 32)
        self.text.hide()
    
        #texto aguardando contestações dos jogadores
        self.text = QLabel(self)
        self.text.setText('Aguardando contestações dos jogadores')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(250, 300)   
        self.text.setMinimumSize(1000, 32)
        self.text.hide()

        #texto contestação dos jogadores 
        self.text = QLabel(self)
        self.text.setText('Jogador X' + 'contestou a resposta correta desta rodada. Vote na palavra correta. Caso a palavra do organizador esteja errada, ele será eliminado da partida.')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 10pt") 
        self.text.move(250, 220)   
        self.text.setMinimumSize(500, 32)

                #Caixa de divisão silábica
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('RESPOSTA SUGERIDA')
        self.nameLabel.resize(200, 32)
        self.nameLabel.move(250, 380)
        self.line = QLineEdit(self)
        self.line.setText('PA-RA-LELE-PÍ-PA-DO')    
        self.line.move(360, 380)
        self.line.resize(200, 32)
        self.nameLabel.hide()
        self.line.hide()

        #Botão de votar em palavra contestada como errada
        voteWrongButton = QPushButton('Errada', self)
        #voteWrongButton.clicked.connect(self.clickMethod)
        voteWrongButton.resize(200, 32)
        voteWrongButton.move(250, 500)
        voteWrongButton.hide()
        #setVisible(false)
        
        #Botão de votar em palavra contestada como nulo
        voteNullButton = QPushButton('Nulo', self)
        #voteNullButton.clicked.connect(self.clickMethod)
        voteNullButton.resize(200, 32)
        voteNullButton.move(480, 500)
        voteNullButton.hide()

        #Botão de votar em palavra contestada como correta
        voteRightButton = QPushButton('Correta', self)
        #voteRightButton.clicked.connect(self.clickMethod)
        voteRightButton.resize(200, 32)
        voteRightButton.move(710, 500)
        voteRightButton.hide()

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

        #Caixa de palavra da rodada
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('PALAVRA DA RODADA')
        self.nameLabel.resize(200, 32)
        self.nameLabel.move(250, 300)
        self.line = QLineEdit(self)
        self.line.cursor  
        self.line.setText('PARALELEPIPADO')
        self.line.move(360, 300)
        self.line.resize(200, 32)

        #Caixa de divisão silábica
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('DIVISÃO SILÁBICA')
        self.nameLabel.resize(200, 32)
        self.nameLabel.move(250, 380)
        self.line = QLineEdit(self)    
        self.line.move(360, 380)
        self.line.resize(200, 32)

        #Botão de votar em um organizador para partida
        voteButton = QPushButton('Enviar Palavra', self)
        #voteButton.clicked.connect(self.clickMethod)
        voteButton.resize(200, 32)
        voteButton.move(450, 500)

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