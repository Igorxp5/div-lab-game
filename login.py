import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

def main():
    
    app = QApplication(sys.argv)
    centerPoint = QDesktopWidget().availableGeometry().center()
    
    main = QMainWindow()
    main.resize(1000, 600)
    qtRectangle = main.frameGeometry()
    centerPoint = QDesktopWidget().availableGeometry().center()
    qtRectangle.moveCenter(centerPoint)
    main.move(qtRectangle.topLeft())
    main.setWindowTitle('Bem-vindo!')
    
    main.setAutoFillBackground(True)
    p = main.palette()
    p.setColor(main.backgroundRole(), QColor(60, 168, 222))
    main.setPalette(p)
    
    main.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()