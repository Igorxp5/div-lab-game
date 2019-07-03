import sys
from PyQt5.QtWidgets import *

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
 
class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'Alerta | DivLab Game'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        #self.winnerPollDialog()
 
    def fullRoomDialog(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        fRD = QMessageBox.question(self, 'Alerta | DivLab Game', "A sala selecionada está cheia, deseja entrar para assistir?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if fRD == QMessageBox.Yes:
            print('Yes clicked.')
        else:
            print('No clicked.')
 
        self.show()
    
    def createRoomDialog(self):
        self.setWindowTitle('Criar sala | DivLab Game')
        self.setGeometry(self.left, self.top, 300, 200)
 
        #Caixa de nome da sala
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Nome da sala:')
        self.nameLabel.resize(100, 30)
        self.nameLabel.move(20, 30)
        self.line = QLineEdit(self)
        self.line.move(120, 30)
        self.line.resize(100, 30)

        #Caixa de limite de jogadores
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Limite de jogadores:')
        self.nameLabel.resize(100, 30)
        self.nameLabel.move(20, 90)
        self.line = QLineEdit(self)    
        self.line.move(120, 90)
        self.line.resize(100, 30)

        #Botão de criar uma sala
        createRoomButton = QPushButton('Criar sala', self)
        #createRoomButton.clicked.connect(self.clickMethod)
        createRoomButton.resize(100, 30)
        createRoomButton.move(120, 150)
 
        self.show()
    
    def organizerWinnerDialog(self):
        oWD = QMessageBox.about(self, 'Vencedor | DivLab Game', "Você venceu a eleição para organizador da rodada. Escolha uma palavra e informe sua divisão silábica.")

    def incorrectAnswerDialog(self):
        iAD = QMessageBox.question(self, 'Resposta Incorreta | DivLab Game', "A resposta correta era " + "PA-RA-LE-LE-PÍ-PA-DO" + ". Você tem a opção de contestar. Deseja contestar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if iAD == QMessageBox.Yes:
            print('Yes clicked.')
        else:
            print('No clicked.')
 
        self.show()
    
    def roundWordDialog(self):
        rWD = QMessageBox.about(self, 'Palavra da rodada | DivLab Game', "O organizador da rodada escolheu  a palavra " + "PARALELEPÍPADO" + " como palavra da rodada.")
    
    def lobbyDialog(self):
        lD = QMessageBox.question(self, 'Alerta | DivLab Game', "Você tem certeza de que quer expulsar " + "Jogador X" + " da sala? Ele não poderá retornar a sala.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if lD == QMessageBox.Yes:
            print('Yes clicked.')
        else:
            print('No clicked.')
    
    def annulledVoteDialog(self):
        aVD = QMessageBox.about(self, 'Voto Anulado | DivLab Game', "Você não votou durante a eleição. Seu voto foi anulado.")

    def winnerPollDialog(self):
        wPD = QMessageBox.about(self, 'Vencedor | DivLab Game', "O " + "Jogador X" + " venceu a eleição. Ele será o organizador da rodada.")
    
    def drawPollDialog(self):
        dPD = QMessageBox.about(self, 'Empate | DivLab Game', "Houveram empates durante a votação. Uma nova eleição será realizada com os candidatos empatados.")

    def contestationPollDialog(self):
        cPD = QMessageBox.about(self, 'Contestação | DivLab Game', "O " + "Jogador X" + " contestou a resposta. A rodada de votação para a resposta correta começará.")
    
    def rightAnswerRoundDialog(self):
        rARD = QMessageBox.about(self, 'Resposta Correta | DivLab Game', "Parabéns!!! Você acertou a divisão silábica da palavra da rodada!")
    
    def contestationAcceptedDialog(self):
        cAD = QMessageBox.about(self, 'Contestação Aceita | DivLab Game', "A divisão silábica sugerida por " + "Jogador X" + " venceu a votação. O organizador dessa rodada será eliminado.")
    
    def contestationRefusedDialog(self):
        cRD = QMessageBox.about(self, 'Contestação Recusada | DivLab Game', "A resposta correta se manteve. " + "Jogador X" + " permanece eliminado.")

    def drawContestationDialog(self):
        dCD = QMessageBox.about(self, 'Empate | DivLab Game', "Houveram empates durante a contestação. Ninguém será eliminado.")

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())