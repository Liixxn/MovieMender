import sys
from PyQt5.QtWidgets import QMessageBox
import pandas as pd
#import surprise
import scipy as sp
import webbrowser


from sklearn.metrics.pairwise import cosine_similarity
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtWidgets import QMainWindow, QApplication

from index_ui import Ui_MainWindow


import webScraping
import sinopsis
import pandas_table
import generos
import tags






# Clase principal de la aplicacion
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Carga de las diferentes ventanas
        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)

        ventanaPrincipal = self.ui

        ventanaPrincipal.stackedWidget.setCurrentIndex(0)
        ventanaPrincipal.btnRecomendarPorUsuario.setChecked(True)


        ventanaPrincipal.btnRecomendarPorUsuario.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnRecomendarPorAtributo.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnPrediccionRating.clicked.connect(self.toogleButton)
        ventanaPrincipal.btnRecomendarUserUser.clicked.connect(self.toogleButton)

        # Carga de los ficheros csv
        self.cargaDocumentos()

        # Carga de los usuarios y las peliculas en sus respectivos comboBoxs
        listaUsuarios = self.cambiarUserIdString()

        ventanaPrincipal.comboBoxUsuario.addItems(listaUsuarios)
        ventanaPrincipal.comboBoxPeliculaAtributos.addItems(self.df_movies['title'].tolist())
        ventanaPrincipal.comboBoxPeliculaUserUser.addItems(self.df_movies['title'].tolist())
        ventanaPrincipal.comboBoxPeliculaRating.addItems(self.df_movies['title'].tolist())
        ventanaPrincipal.comboBoxUsuarioRating.addItems(listaUsuarios)


        ventanaPrincipal.btnRecomendarPeliculaUser.clicked.connect(self.recomendarNPeliculasPorUsuario)

        ventanaPrincipal.btnRecomendarPeliculaAtributo.clicked.connect(self.recomendarNPeliculasPorAtributos)

        ventanaPrincipal.btnPredecirRating.clicked.connect(self.predecirRatingPelicula)

        ventanaPrincipal.btnRecomendarPeliculasUserUser.clicked.connect(self.recomendarNPeliculasUserUser)


    ####################################################################################################

     # CARGA DE DATOS Y FUNCIONES AL INICIALIZAR LA APLICACION

    ####################################################################################################


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


    # Funcion que carga los ficheros csv
    def cargaDocumentos(self):
        extract = webScraping.extraccionSinopsisPeliculas()
        # Funciones para realizar el web scraping, escribir el fichero y rellenar la informacion vacia
        # extract.scrapingSinopsisPeliculas()
        # extract.escribirSinopsisFichero()
        self.df_sinopsis = extract.cargarFicheroSinopsisDataframe()

        self.df_peliculasConSinopsis = self.df_sinopsis[self.df_sinopsis["sinopsis"] != "Sin Informacion"]
        self.df_peliculasConSinopsis = self.df_peliculasConSinopsis.reset_index()


        self.df_usuaarioO = pd.read_csv('csv/Usuario_0.csv', sep=';')

        self.df_movies = pd.read_csv('csv/movies.csv')
        # Carga del dataframe de las peliculas con su sinopsis
        self.df_moviesSinopsis = pd.concat([self.df_movies, self.df_sinopsis], axis=1)



        self.procesoSinopsis = sinopsis.procesamientoTexto()
        self.procesoSinopsis.tratamientoBasico(self.df_peliculasConSinopsis)
        self.procesoSinopsis.quit_stopwords(self.df_peliculasConSinopsis)
        self.procesoSinopsis.stemming(self.df_peliculasConSinopsis)
        self.procesoSinopsis.prepararSinopsisTfidf(self.df_peliculasConSinopsis)

        self.df_peliculasConSinopsis.drop('index', inplace=True, axis=1)




        self.df_links = pd.read_csv('csv/links.csv')
        self.df_links = self.df_links.dropna()
        self.df_movies = self.df_movies.dropna()
        self.df_ratings = pd.read_csv('csv/ratings.csv')
        self.df_ratings = self.df_ratings.dropna()
        self.df_tags = pd.read_csv('csv/tags.csv')
        self.df_tags = self.df_tags.dropna()
        self.df_movies_ratings = self.df_ratings.merge(self.df_movies)[
            ['userId', 'movieId', 'title', 'rating', 'genres']]

        self.df_movies_ratings_tags = pd.merge(self.df_movies_ratings, self.df_tags, how='outer')[
            ['userId', 'movieId', 'title', 'rating', 'genres', 'tag']]
        self.df_movies_ratings_tags["tag"] = self.df_movies_ratings_tags["tag"].str.lower()
        # self.df_movies_ratings_tags.fillna("vacio", inplace = True)

        self.ratings_table = self.df_movies_ratings.pivot_table(index='userId', columns='title', values='rating')
        # para cambiar los NAN por 0:
        self.ratings_table.fillna(0, inplace=True)

    # Funcion que cambia el id de los usuarios a string para poder introducirlo en un comboBox
    def cambiarUserIdString(self):

        listaUsuariosId = []
        df_usuariosUnicos = self.df_ratings['userId'].unique()
        for usuario in range(len(df_usuariosUnicos)):
            listaUsuariosId.append(str(df_usuariosUnicos[usuario]))

        return listaUsuariosId


    ####################################################################################################
    
    # Mensajes por pantalla
    
    ####################################################################################################

    def mensaje_error(self, mensaje):
        QMessageBox.critical(
            self,
            "Error",
            mensaje,
            buttons=QMessageBox.Discard,
            defaultButton=QMessageBox.Discard,
        )

    ####################################################################################################

    # FUNCIONES DE RECOMENDACION

    ####################################################################################################


    def mirarPelisPorUsuario(self):
        index = self.ui.tableViewPeliculasUser.selectedIndexes()[0]
        print(index)
        peli = index.data()
        
        idPeli = self.df_movies[self.df_movies["title"] == peli]["movieId"]
        idPeliBuscador = str(int(self.df_links[self.df_links["movieId"]==int(idPeli)]["tmdbId"]))
        webbrowser.open("www.themoviedb.org/movie/" + idPeliBuscador)


    # Funcion que recomienda N peliculas que no ha visto el usuario en base a sus atributos
    def recomendarNPeliculasPorUsuario(self):

        if self.ui.comboBoxUsuario.currentText() != "" and self.ui.comboBoxRecomendacionUsuarios.currentText() != "" and (self.ui.checkBoxGenerosRecomendacionUsuarios.isChecked() or self.ui.checkBoxTagsRecomendacionUsuarios.isChecked() or self.ui.checkBoxSinopsisRecomendacionUsuarios.isChecked()):
            if self.ui.comboBoxUsuario.currentText().isdigit() and self.ui.comboBoxRecomendacionUsuarios.currentText().isdigit():

                listaUsuarios = self.cambiarUserIdString()

                if self.ui.comboBoxUsuario.currentText() in listaUsuarios:
                    self.ui.lblusuarioSeleccionado.setText(self.ui.comboBoxUsuario.currentText())
                    if self.ui.checkBoxGenerosRecomendacionUsuarios.isChecked():

                        genero = generos.Generos()
                        peliculasRecomendadas = genero.recomendacionEnBaseGeneroPelisQueNoHaVistoUsuario(
                            self.ui.comboBoxUsuario.currentText(), self.ui.comboBoxRecomendacionUsuarios.currentText())

                        df_listaPeliculasGeneros = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasGeneros["Peliculas"] = peliculasRecomendadas

                        model = pandas_table.DataFrameModel(df_listaPeliculasGeneros)
                        self.ui.tableViewPeliculasUser.setModel(model)
                        self.ui.tableViewPeliculasUser.clicked.connect(self.mirarPelisPorUsuario)

                    if self.ui.checkBoxTagsRecomendacionUsuarios.isChecked():

                        tag = tags.Tags()
                        peliculasRecomendadas = tag.recomedacionPorTagsUser(self.ui.comboBoxUsuario.currentText(), self.ui.comboBoxRecomendacionUsuarios.currentText())
                        df_listaPeliculasTags = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasTags["Peliculas"] = peliculasRecomendadas

                        model = pandas_table.DataFrameModel(df_listaPeliculasTags)
                        self.ui.tableViewPeliculasUser.setModel(model)
                        self.ui.tableViewPeliculasUser.clicked.connect(self.mirarPelisPorUsuario)

                    if self.ui.checkBoxSinopsisRecomendacionUsuarios.isChecked():

                        listaPeliculasSinopsis = []
                        listaPeliculasSinopsis = self.procesoSinopsis.recomendarNPeliculasNoVistasSinopsis(self.ui.comboBoxUsuario.currentText(), self.ui.comboBoxRecomendacionUsuarios.currentText(), self.df_moviesSinopsis)
                        df_listaPeliculasSinopsis = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasSinopsis["Peliculas"] = listaPeliculasSinopsis

                        model = pandas_table.DataFrameModel(df_listaPeliculasSinopsis)
                        self.ui.tableViewPeliculasUser.setModel(model)
                        self.ui.tableViewPeliculasUser.clicked.connect(self.mirarPelisPorUsuario)
                else:
                    self.mensaje_error("El usuario introducido no existe")
            else:
                self.mensaje_error("Introduzca un formato válido de usuario o número de recomendaciones")
        else:
            self.mensaje_error("Rellene los campos necesarios")



    def mirarPelisPorAtributos(self):
        index = self.ui.tableViewPeliculasAtributo.selectedIndexes()[0]
        peli = index.data()
        
        idPeli = self.df_movies[self.df_movies["title"] == peli]["movieId"]
        idPeliBuscador = str(int(self.df_links[self.df_links["movieId"]==int(idPeli)]["tmdbId"]))
        webbrowser.open("www.themoviedb.org/movie/" + idPeliBuscador)

    # Funcin que recomienda N peliculas en base a los atributos de esta
    def recomendarNPeliculasPorAtributos(self):

        if self.ui.comboBoxPeliculaAtributos.currentText() != "" and self.ui.comboBoxNPeliculasAtributos.currentText() != "" and (self.ui.checkBoxGenerosAtributos.isChecked() or self.ui.checkBoxTagsAtributos.isChecked() or self.ui.checkBoxSinopsisAtributos.isChecked()):
            if self.ui.comboBoxNPeliculasAtributos.currentText().isdigit():

                titulo_pelicula = self.ui.comboBoxPeliculaAtributos.currentText()
                contador = 0
                encontrado = False
                while (encontrado == False and contador < len(self.df_movies['title'])):
                    if self.df_movies['title'][contador] == titulo_pelicula:
                        encontrado = True
                    else:
                        contador +=1

                if encontrado == True:
                    self.ui.lblPeliculaSeleccionadaAtributos.setText(titulo_pelicula)

                    if self.ui.checkBoxGenerosAtributos.isChecked():

                        genero = generos.Generos()
                        peliculasRecomendadas = genero.recomedacionPorGenero(titulo_pelicula, self.ui.comboBoxNPeliculasAtributos.currentText())

                        df_listaPeliculasSinopsis = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasSinopsis["Peliculas"] = peliculasRecomendadas

                        model = pandas_table.DataFrameModel(df_listaPeliculasSinopsis)
                        self.ui.tableViewPeliculasAtributo.setModel(model)
                        self.ui.tableViewPeliculasAtributo.clicked.connect(self.mirarPelisPorAtributos)

                    if self.ui.checkBoxTagsAtributos.isChecked():

                        tag = tags.Tags()
                        peliculasRecomendadas = tag.recomedacionPorTags(titulo_pelicula, self.ui.comboBoxNPeliculasAtributos.currentText())

                        df_listaPeliculasSinopsis = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasSinopsis["Peliculas"] = peliculasRecomendadas

                        model = pandas_table.DataFrameModel(df_listaPeliculasSinopsis)
                        self.ui.tableViewPeliculasAtributo.setModel(model)
                        self.ui.tableViewPeliculasAtributo.clicked.connect(self.mirarPelisPorAtributos)

                    if self.ui.checkBoxSinopsisAtributos.isChecked():

                        peliculasRecomendadasSinopsis = self.procesoSinopsis.recomendarPeliculasSinopsis(titulo_pelicula, self.ui.comboBoxNPeliculasAtributos.currentText(), self.df_moviesSinopsis)
                        df_listaPeliculasSinopsis = pd.DataFrame(columns=["Peliculas"])
                        df_listaPeliculasSinopsis["Peliculas"] = peliculasRecomendadasSinopsis

                        model = pandas_table.DataFrameModel(df_listaPeliculasSinopsis)
                        self.ui.tableViewPeliculasAtributo.setModel(model)
                        self.ui.tableViewPeliculasAtributo.clicked.connect(self.mirarPelisPorAtributos)

                else:
                    self.mensaje_error("No se ha encontrado la pelicula introducida")

            else:
                self.mensaje_error("Introduzca un número válido de recomendaciones")
        else:
            self.mensaje_error("Rellene los campos necesarios")


    # Funcoon que predice la nota para una pelicula dada en base a los atributos seleccionados
    def predecirRatingPelicula(self):

        if self.ui.comboBoxUsuarioRating.currentText() != "" and self.ui.comboBoxPeliculaRating.currentText() != "" and (self.ui.checkBoxGenerosPrediccion.isChecked() or self.ui.checkBoxTagsPrediccion.isChecked() or self.ui.checkBoxSinopsisPrediccion.isChecked()):
            if self.ui.comboBoxUsuarioRating.currentText().isdigit():

                listaUsuarios = self.cambiarUserIdString()

                if self.ui.comboBoxUsuarioRating.currentText() in listaUsuarios:

                    self.ui.lblusuarioSeleccionadoRating.setText(self.ui.comboBoxUsuarioRating.currentText())

                    titulo_pelicula = self.ui.comboBoxPeliculaRating.currentText()
                    contador = 0
                    encontrado = False
                    while (encontrado == False and contador < len(self.df_movies['title'])):
                        if self.df_movies['title'][contador] == titulo_pelicula:
                            encontrado = True
                        else:
                            contador +=1

                    if encontrado == True:
                        self.ui.lblPeliculaSeleccionadaRating.setText(titulo_pelicula)

                        if self.ui.checkBoxGenerosPrediccion.isChecked():

                            genero = generos.Generos()
                            ratingPelicula = genero.predecirRatingDeUserAPeliculaPorSusGeneros(titulo_pelicula, self.ui.comboBoxUsuarioRating.currentText())
                            if ratingPelicula == "Vacio":
                                self.ui.lblPeliculaPrediccion.setText("No se ha podido predecir el rating para la película " + titulo_pelicula + " porque no tiene géneros")
                            else:
                                self.ui.lblPeliculaPrediccion.setText("La predicción para la película " + titulo_pelicula + " es: ")
                                self.ui.lblnotaPrediccionPelicula.setText(str(ratingPelicula))

                        if self.ui.checkBoxSinopsisPrediccion.isChecked():
                            prediccionSinopsis = self.procesoSinopsis.predecirRatingUsuarioSinopsis(self.ui.comboBoxUsuarioRating.currentText(), self.ui.comboBoxPeliculaRating.currentText(), self.df_moviesSinopsis)
                            self.ui.lblPeliculaPrediccion.setText("La predicción para la película " + titulo_pelicula + " es: ")
                            self.ui.lblnotaPrediccionPelicula.setText(str(prediccionSinopsis))

                        if self.ui.checkBoxTagsPrediccion.isChecked():

                            tag = tags.Tags()
                            ratingPelicula = tag.predecirRatingDeUserAPeliculaPorSusTags(titulo_pelicula, self.ui.comboBoxUsuarioRating.currentText())
                            if ratingPelicula == "Vacio":
                                self.ui.lblPeliculaPrediccion.setText(
                                    "No se ha podido predecir el rating para la película " + titulo_pelicula + " porque no tiene géneros")
                            else:
                                self.ui.lblPeliculaPrediccion.setText(
                                    "La predicción para la película " + titulo_pelicula + " es: ")
                                self.ui.lblnotaPrediccionPelicula.setText(str(ratingPelicula))

                    else:
                       self.mensaje_error("No se ha encontrado la pelicula introducida")
                else:
                    self.mensaje_error("El usuario introducido no existe")
            else:
                self.mensaje_error("Introduzca un número válido de usuario")
        else:
            self.mensaje_error("Rellene los campos necesarios")



    def mirarPelisUserUser(self):
        index = self.ui.tableViewUserUser.selectedIndexes()[0]
        peli = index.data()
         
        idPeli = self.df_movies[self.df_movies["title"] == peli]["movieId"]
        idPeliBuscador = str(int(self.df_links[self.df_links["movieId"]==int(idPeli)]["tmdbId"]))
        webbrowser.open("www.themoviedb.org/movie/" + idPeliBuscador)
        
    # Función que recomienda películas a un usuario basandose en otros usuarios
    def recomendarNPeliculasUserUser(self):

        if self.ui.comboBoxPeliculaUserUser.currentText()!="" and self.ui.comboBoxNPeliculasUserUser.currentText()!="":
            if self.ui.comboBoxNPeliculasUserUser.currentText().isdigit():

                titulo_pelicula = self.ui.comboBoxPeliculaUserUser.currentText()
                contador = 0
                encontrado = False
                while (encontrado == False and contador < len(self.df_movies['title'])):
                    if self.df_movies['title'][contador] == titulo_pelicula:
                        encontrado = True
                    else:
                        contador +=1

                if encontrado == True:
                    self.ui.lblPeliculaSeleccionadaUserUser.setText(titulo_pelicula)

                    sparse_rating = sp.sparse.csr_matrix(self.ratings_table)
                    similitud_usuarios = cosine_similarity(sparse_rating)
                    # se hace con la transpuesta de la matriz creada anteriormente
                    similitud_movies = cosine_similarity(sparse_rating.T)
                    df_similitud_usuarios = pd.DataFrame(similitud_usuarios, index=self.ratings_table.index,
                                                         columns=self.ratings_table.index)
                    df_similitud_movies = pd.DataFrame(similitud_movies, index=self.ratings_table.columns,
                                                       columns=self.ratings_table.columns)
                    # le sumamos uno a n_similares porque la primera siempre es la propia pelicula y nos la saltamos
                    n_similares = int(self.ui.comboBoxNPeliculasUserUser.currentText())
                    n_similares +=1

                    listaPeliculasRecomendadas = []
                    for movie in df_similitud_movies[titulo_pelicula].sort_values(ascending=False).index[1:n_similares]:
                        listaPeliculasRecomendadas.append(movie)


                    df_peliculasRecomendadas = pd.DataFrame(columns=['Peliculas'])
                    df_peliculasRecomendadas['Peliculas'] = listaPeliculasRecomendadas

                    model = pandas_table.DataFrameModel(df_peliculasRecomendadas)
                    self.ui.tableViewUserUser.setModel(model)
                    self.ui.tableViewUserUser.clicked.connect(self.mirarPelisUserUser)


                else:
                    self.mensaje_error("No se ha encontrado la pelicula introducida")

            else:
                self.mensaje_error("Introduzca un número válido de recomendaciones")
        else:
            self.mensaje_error("Rellene los campos necesarios")






# Main de la aplicacion
if __name__ == "__main__":
    app = QApplication(sys.argv)


    style_file = QFile("index.qss")
    style_file.open(QFile.ReadOnly | QFile.Text)
    style_stream = QTextStream(style_file)
    app.setStyleSheet(style_stream.readAll())

    window = MainWindow()
    # Establecer un logo a la ventana
    window.show()
    window.showMaximized()

    sys.exit(app.exec_())



