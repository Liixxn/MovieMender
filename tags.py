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




class Tags():

    def __init__(self):
         self.cargaDocumentos()


    def cargaDocumentos(self):
        self.df_usuaarioO = pd.read_csv('csv/Usuario_0.csv', sep=';')
        self.df_movies = pd.read_csv('csv/movies.csv')

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


    def recomedacionPorTags(self, nombrePelicula, n_similares):
        n_similares=int(n_similares)
        count_matrix = self.df_movies_ratings_tags.pivot_table(index='movieId', columns='tag', values='userId')
        #count_matrix = self.df_movies_ratings_tags.pivot_table(index='movieId', columns='tag', values='rating')
        count_matrix.fillna(0, inplace=True)
        sparse_rating = sp.sparse.csr_matrix(count_matrix)
        selected_movie = self.df_movies[self.df_movies["title"] == nombrePelicula]["movieId"].values[0]


        #encontramos el id de la pelicula en la matriz
        selected_movie_index = count_matrix.index.get_loc(selected_movie)

        similarities = cosine_similarity(sparse_rating, sparse_rating[selected_movie_index])

        movie_list = [(index, similarity) for index, similarity in enumerate(similarities)]
        movie_list.sort(key=lambda x: x[1], reverse=True)

        print(n_similares)
        if(n_similares>len(movie_list)):
            n_similares=len(movie_list)-1
        print(n_similares)
        bandera=False
        listaPeliculasMostrar = []
        contador = 1
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
                
    def predecirRatingDeUserAPeliculaPorSusTags(self, nombrePelicula, user_id):
        user_id=int(user_id)
        yaVotado = self.df_movies_ratings[(self.df_movies_ratings['title']==nombrePelicula) & (self.df_movies_ratings['userId']==user_id)]["rating"].unique()
        if(len(yaVotado)!=0):
            prediction = yaVotado[0]

            return str(prediction)
        else:
            # obtener tags de la película a predecir
            tagsPeli = []
            movie_tags = self.df_movies_ratings_tags[self.df_movies_ratings_tags['title']==nombrePelicula]["tag"].unique()
            for m in movie_tags:
                tagsPeli.append(m)

            filtroMergeandoTags = self.df_movies_ratings_tags[['userId','movieId','title', 'rating', 'tag']]
            filtroEnBaseUserId = filtroMergeandoTags[filtroMergeandoTags['userId']==user_id]
            
            #similitud = [distance.cosine(tagsPeli, j['tag']) for i,j in filtroEnBaseUserId.iterrows()]
            
            user_ratings = filtroEnBaseUserId[filtroEnBaseUserId['tag'].isin(tagsPeli)]
            #si el usuario a creado un tag de alguna peli que sea igual a alguno de el de la pelicula buscada filtramos mas el df quitando los nulos
            #si no a hecho ningun tag y todos sus tag son nan dejamos el df como esta ya que si hacemos dropna eliminamos el df entero
            if user_ratings.dropna().size != 0:
                user_ratings = user_ratings.dropna()

            # calcular la media de valoraciones del usuario para las peliculas con generos en comun
            if user_ratings.empty:
                print()
                return "Vacia"
            else:
                #prediction = user_ratings_ID['rating'].mean()
                prediction = format(user_ratings['rating'].mean(), '.3f')

                return str(prediction)


    def recomedacionPorTagsUser(self, user_id, n_similares):
        user_id=int(user_id)
        n_similares=int(n_similares)
        df_movies_rating_user = self.df_movies_ratings[self.df_movies_ratings['userId']==user_id]
        self.df_movies[~self.df_movies.movieId.isin(df_movies_rating_user["movieId"])]
        df = pd.DataFrame()
        movies = self.df_movies[~self.df_movies.movieId.isin(df_movies_rating_user["movieId"])]
        df["movieId"] = movies["movieId"]
        df["title"] = movies["title"]
        df["ratingPredict"] = [self.predecirRatingDeUserAPeliculaPorSusTags(j["title"], user_id) for i,j in df.iterrows()]
        df = df.sort_values(by='ratingPredict', ascending = False)

        df_resultados = df["title"].head(n_similares)

        listaPeliculasRecomendadas = []

        for i in df_resultados:
            listaPeliculasRecomendadas.append(i)


        return listaPeliculasRecomendadas