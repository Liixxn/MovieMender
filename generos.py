import requests
import pandas as pd
import numpy as np
import seaborn as sns
from bs4 import BeautifulSoup
import warnings
import nltk
#import surprise
import scipy as sp


from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from nltk import word_tokenize, RegexpTokenizer
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer

import movieMender

class Generos:
    
    
    def __init__(self):
        self.cargaDocumentos()
        
    def cargaDocumentos(self):
        self.df_usuaarioO = pd.read_csv('csv/Usuario_0.csv', sep=';')

        self.df_movies = pd.read_csv('csv/movies.csv')
        # Carga del dataframe de las peliculas con su sinopsis


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
        
    def recomedacionPorGenero(self, nombrePelicula, n_similares):
        n_similares=int(n_similares)
        genres = list(set([genre for genres in self.df_movies["genres"].str.split("|") for genre in genres]))
        genre_matrix = []
        for index, row in self.df_movies.iterrows():
            genre_list = row["genres"].split("|")
            genre_vector = [1 if genre in genre_list else 0 for genre in genres]
            genre_matrix.append(genre_vector)
        genre_matrix = pd.DataFrame(genre_matrix, columns=genres)
        contador = 1
        selected_movie = self.df_movies[self.df_movies["title"] == nombrePelicula]
        selected_movie_index = selected_movie.index[0]
        #sacamos las similitudes de los generos
        similarities = cosine_similarity(genre_matrix[selected_movie_index:selected_movie_index+1], genre_matrix).flatten()
        #las metemos en una tupla y las ordenamos de mayor a menor 
        movie_list = [(index, similarity) for index, similarity in enumerate(similarities)]
        movie_list.sort(key=lambda x: x[1], reverse=True)

        #la bandera nos sirve para saltarnos la propia peli que buscamos
        #siempre esta a false y si nos encontramos la peli que estamos buscando la activamos a True
        #si esta en True al finalizar el bucle significa que ha saltado el titulo que buscabamos para no repetirse a si mismo 
        #y por lo tanto hay que añadir uno mas para llegar al numero deseado por el usuario
        listaPeliculasMostrar = []
        bandera=False
        if(n_similares>len(self.df_movies)):
            n_similares=len(self.df_movies)-1
        for movie in movie_list[0:n_similares]:
            if(nombrePelicula != self.df_movies.iloc[movie[0]]["title"]):
                listaPeliculasMostrar.append(self.df_movies.iloc[movie[0]]["title"])
                contador+=1
            else:
                bandera=True
        if(bandera):

            mov=movie_list[n_similares][0]
            listaPeliculasMostrar.append(self.df_movies.iloc[mov]["title"])
        return listaPeliculasMostrar
                
    def predecirRatingDeUserAPeliculaPorSusGeneros(self, nombrePelicula, user_id):
        user_id=int(user_id)
        yaVotado = self.df_movies_ratings[(self.df_movies_ratings['title']==nombrePelicula) & (self.df_movies_ratings['userId']==user_id)]["rating"].unique()
        if(len(yaVotado)!=0):
            prediction = yaVotado[0]

            return str(prediction)
        else:
            # obtener géneros de la película a predecir
            movie_genres = self.df_movies_ratings[self.df_movies_ratings['title']==nombrePelicula]["genres"].unique()
            generosPeli = movie_genres[0].split("|")
            # filtrar valoraciones del usuario para peliculas con generos en comun
            user_ratings_ID = self.df_movies_ratings[self.df_movies_ratings['userId'] == user_id]
            user_ratings = user_ratings_ID.loc[user_ratings_ID['genres'].str.split('|').apply(lambda x: any(i in x for i in generosPeli))]
            # calcular la media de valoraciones del usuario para las peliculas con generos en comun
            if user_ratings.empty:
                print()
                return "Vacio"
            else:
                #prediction = user_ratings_ID['rating'].mean()
                prediction = format(user_ratings['rating'].mean(), '.3f')

                return str(prediction)

    def recomendacionEnBaseGeneroPelisQueNoHaVistoUsuario(self, user_id, n_similares):
        warnings.filterwarnings('ignore')
        user_id=int(user_id)
        n_similares=int(n_similares)
        #warnings.filterwarnings('ignore')
        df_movies_rating_user = self.df_movies_ratings[self.df_movies_ratings['userId']==user_id]
        df_movies_rating_user = df_movies_rating_user.sort_values(by='rating',ascending=False)

        #cogemos los primeros 10 para ver que generos le gustan mas, anteriormente hemos ordenado por genero
        genero_mejor_rating_unicos = list(set([genre for genres in df_movies_rating_user.head(10)["genres"].str.split("|") for genre in genres]))

        # creamos un diccionario para guardar los generos y cuantas veces se repiten
        genre_count = {}
        for g in genero_mejor_rating_unicos:
            genre_count[g] = df_movies_rating_user.head(10)['genres'].str.count(g).sum()

        #ordenamos el diccionario de mayor a menor
        genero_mejor_rating = dict(sorted(genre_count.items(), key=lambda x: x[1], reverse=True))

        #sacamos las pelis que el usuario no ha visto
        df_movies_no_rating_user = self.df_movies[self.df_movies['movieId'].isin(df_movies_rating_user['movieId']) == False]
        #creamos en el df una columna por cada genero que le gusta al usuario y le agregamos cuanto le gusta
        for genre, weight in genero_mejor_rating.items():
            df_movies_no_rating_user[genre] = df_movies_no_rating_user["genres"].str.contains(genre).apply(lambda x: weight if x else 0)
        #creamos una nueva columna con la suma de cada fila para saber que peliculas le pueden gustar mas
        df_movies_no_rating_user["sumaPesos"] = df_movies_no_rating_user[genero_mejor_rating.keys()].sum(axis=1)
        #ordenamos por las pelis que tengan una mayor puntuacion en la columna sumaPesos ya que esto quiere decir que hay muchos generos que le gustan al usuario
        df_movies_no_rating_user = df_movies_no_rating_user.sort_values(by='sumaPesos',ascending=False)

        df_peliculas_mostrar = df_movies_no_rating_user['title'][0:n_similares]

        listaPeliculasMostrar = []
        contador = 1
        for movie in df_peliculas_mostrar:
            listaPeliculasMostrar.append(movie)
            contador+=1
        return listaPeliculasMostrar