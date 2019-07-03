import sys
#from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QMainWindow, QPushButton, QLineEdit, QInputDialog, QApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize    

class RankingWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
        #janela
        self.resize(1000, 600)
        self.qtRectangle = self.frameGeometry()
        self.setMinimumSize(self.sizeHint())    
        self.setWindowTitle('Sala' + 'X' + '| DivLab Game')
       
        #título
        title = QLabel(self)
        title.setText('SALA ' + 'X') 
        title.setStyleSheet("font: 30pt")
        title.resize(200, 32)
        title.move(10, 10)

        #texto ranking final
        self.text = QLabel(self)
        self.text.setText('Ranking Final')
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font: 15pt") 
        self.text.move(50, 150)   
        self.text.setMinimumSize(1000, 32)

        #Lista de ranking de jogadores
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
        listView.move(50, 200)
        listView.resize(900, 300)

    def clickMethod(self):
        print('Your name: ' + self.line.text())

#Ação de clicar em um item da lista
class myListWidget(QListWidget):
   def Clicked(self):
      item = self.listwidget.currentItem()
      QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    rankingWin = RankingWindow()
    rankingWin.show()
    sys.exit( app.exec_() )