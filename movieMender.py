import sys



from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic.properties import QtWidgets, QtGui

from index_ui import Ui_MainWindow





# Clase principal de la aplicacion
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Carga de las diferentes ventanas
        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)

        ventanaPrincipal = self.ui

        ventanaPrincipal.stackedWidget.setCurrentIndex(0)

        ventanaPrincipal.btnRecomendarPorUsuario.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnRecomendarPorAtributo.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnPrediccionRating.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnRecomendarUserUser.clicked.connect(self.toogleButton)




    # Funcion que despliega las paginas del menu lateral
    def toogleButton(self):

        if str(self.sender().objectName()).__contains__("btnRecomendarPorUsuario"):
            self.ui.stackedWidget.setCurrentIndex(0)

        if str(self.sender().objectName()).__contains__("btnPrediccionRating"):
            self.ui.stackedWidget.setCurrentIndex(1)

        if str(self.sender().objectName()).__contains__("btnRecomendarPorAtributo"):
            self.ui.stackedWidget.setCurrentIndex(2)
        if str(self.sender().objectName()).__contains__("btnRecomendarUserUser"):
            self.ui.stackedWidget.setCurrentIndex(3)







# Main de la aplicacion
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Hoja de estilos
    # style_file = QFile("index.qss")
    # style_file.open(QFile.ReadOnly | QFile.Text)
    # style_stream = QTextStream(style_file)
    # app.setStyleSheet(style_stream.readAll())

    window = MainWindow()
    # Establecer un logo a la ventana
    window.show()

    sys.exit(app.exec_())



