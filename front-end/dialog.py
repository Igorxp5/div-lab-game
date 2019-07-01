from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, 
    QInputDialog, QApplication)
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import sys

class DialogWindow(QMainWindow):
    
    def __init__(self):
        #super().__init__()
        QMainWindow.__init__(self)

        self.open_dialog()
        
    def initUI(self):      
        self.btn = QPushButton('Dialog', self)
        self.btn.move(20, 20)
        self.btn.clicked.connect(self.showDialog)
        
        self.le = QLineEdit(self)
        self.le.move(130, 22)
        
        self.setGeometry(300, 300, 290, 150)
        self.setWindowTitle('Input dialog')
        self.show()
        
        
    def showDialog(self):
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')
        
        if ok:
            self.le.setText(str(text))

    def open_dialog(self):
        #Botão de Ok e Cancelar
        wid = QWidget(self)
        layout = QVBoxLayout()        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(QDialog.accept)
        buttons.rejected.connect(QDialog.reject)
        layout.addWidget(buttons)
        wid.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialogWindow = DialogWindow()
    sys.exit(app.exec_())