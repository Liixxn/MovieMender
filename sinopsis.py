import nltk
import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from nltk.corpus import stopwords
from nltk import word_tokenize, RegexpTokenizer
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def mensaje_error(self, mensaje):
    QMessageBox.critical(
        self,
        "Error",
        mensaje,
        buttons=QMessageBox.Discard,
        defaultButton=QMessageBox.Discard,
    )


class procesamientoTexto():


    # Funcion que pasa a minusculas y elimina los signos de puntuacion
    def tratamientoBasico(self, df_sinTratar):
        listatokens = []

        for indiceDF, fila in df_sinTratar.iterrows():
            tokenizer = RegexpTokenizer(r'\w+')
            tokens = tokenizer.tokenize(fila["sinopsis"])
            listatokens.append(tokens)

        for i in range(len(listatokens)):
            listatokens[i] = [w.lower() for w in listatokens[i]]
            df_sinTratar["sinopsis"][i] = listatokens[i]

        return df_sinTratar

    # Funcion que aplica las stopwords al datafram que se le pasa
    def quit_stopwords(self, df_conStopwords):
        listaStopwords = []
        stop_words_sp = set(stopwords.words('spanish'))
        try:
            filtered_sentence = []

            for indiceDF, fila in df_conStopwords.iterrows():
                filtered_sentence = [w for w in fila["sinopsis"] if not w in stop_words_sp]
                listaStopwords.append(filtered_sentence)

            for i in range(len(listaStopwords)):
                df_conStopwords["sinopsis"][i] = listaStopwords[i]

        except Exception as e:
            print(e)

        return df_conStopwords

    # Funcion que aplica el stemming al dataframe que se le pasa
    def stemming(self, df_sinStemming):
        listaStemming = []
        lista_stem = []

        # Se establece el idioma
        stemmer = SnowballStemmer('spanish')

        for indiceDF, fila in df_sinStemming.iterrows():
            if indiceDF != 0:
                lista_stem.append(listaStemming)
                listaStemming = []

            for word in range(len(fila["sinopsis"])):
                w = stemmer.stem(fila["sinopsis"][word])
                listaStemming.append(w)

        for i in range(len(lista_stem)):
            df_sinStemming["sinopsis"][i] = lista_stem[i]

        return df_sinStemming

    def prepararSinopsisTfidf(self, df_peliculasConSinopsis):
        listaUnidos = []
        for i in range(len(df_peliculasConSinopsis["sinopsis"])):
            unidos = " ".join(df_peliculasConSinopsis["sinopsis"][i])

            df_peliculasConSinopsis["sinopsis"][i] = str(unidos)

        return df_peliculasConSinopsis




    def recomendarPeliculasSinopsis(self, titulo_pelicula, n_similares, df_peliculasConSinopsis):

        n_similares = int(n_similares)

        # Se crea la instancia del tfidf
        tfidfvec = TfidfVectorizer()
        # Convierte el conjunto de datos en una matriz de tokens counts
        tfidf_movie = tfidfvec.fit_transform((df_peliculasConSinopsis["sinopsis"]))
        # Se obtiene la similitud del coseno
        cos_sim = cosine_similarity(tfidf_movie, tfidf_movie)
        # Se obtienen los indices de las peliculas
        indices = pd.Series(df_peliculasConSinopsis.index)

        recommended_movies = []
        # Se obtiene la pelicula pasada
        selected_movie = df_peliculasConSinopsis[df_peliculasConSinopsis["title"] == titulo_pelicula]
        # Se obtiene el indice de la pelicula
        selected_movie_index = selected_movie.index[0]
        # Se obtienen los puntuajes de las similitudes entre las peliculas ordenados de mayor a menor
        similarity_scores = pd.Series(cos_sim[selected_movie_index]).sort_values(ascending=False)

        listaSimilar = []
        for i in similarity_scores[1:n_similares+1]:
            listaSimilar.append(i)

        # Se escogen el numero de peliculas especificadas
        numero_peliculas = list(similarity_scores.iloc[1:n_similares + 1].index)

        for i in numero_peliculas:
            # Se aniaden a la lista de peliculas recomendadas
            recommended_movies.append(df_peliculasConSinopsis.loc[i]["title"])


        return recommended_movies, listaSimilar




    def predecirRatingUsuarioSinopsis(self, user_id, titulo_pelicula, df_peliculasConSinopsis, df_ratingsUsuarios):

        user_id = int(user_id)

        # Se comrpueba que el usuario exista
        selected_user = df_ratingsUsuarios[df_ratingsUsuarios["userId"] == user_id]

        # Se comprueba que la pelicula exista
        if len(df_peliculasConSinopsis[df_peliculasConSinopsis["title"] == titulo_pelicula]) != 0:
            selected_movie = df_peliculasConSinopsis[df_peliculasConSinopsis["title"] == titulo_pelicula]
            # Se obtiene el id de la pelicula
            selected_movieid = selected_movie["movieId"].values

            # Se comprueba si ese usuario ha votado ya la pelicula
            if len(selected_user[selected_user["movieId"] == selected_movieid[0]]) != 0:
                df_ratingUsuario = selected_user[selected_user["movieId"] == selected_movieid[0]]
                ratingPelicula = df_ratingUsuario["rating"].values
                return str(ratingPelicula[0])

            else:
                # Se unen los dos dataframe de las peliculas que ya ha votado ese usuario con su respectiva sinopsis
                df_userRatings_movies = pd.merge(selected_user, df_peliculasConSinopsis, on="movieId")
                # Se aniade la pelicula a predecir como ultima fila
                df_userRatings_movies = df_userRatings_movies.append(selected_movie, ignore_index=True)

                selected_movie = df_userRatings_movies[df_userRatings_movies["title"] == titulo_pelicula]
                selected_movie_index = selected_movie.index[0]

                # Se crea la instancia del tfidf
                tfidfvec = TfidfVectorizer()
                # Convierte el conjunto de datos en una matriz de tokens counts
                tfidf_movie = tfidfvec.fit_transform((df_userRatings_movies["sinopsis"]))
                # Se obtiene la similitud del coseno
                cos_sim = cosine_similarity(tfidf_movie, tfidf_movie)

                recommended_movies = []
                selected_movie = df_userRatings_movies[df_userRatings_movies["title"] == titulo_pelicula]

                # Se obtienen los puntuajes de las similitudes entre las peliculas ordenados de mayor a menor
                similarity_scores = pd.Series(cos_sim[selected_movie_index]).sort_values(ascending=False)

                # Se obtienen los indices de las peliculas que se parecen, y que no tienen un 0 de similitud
                indices = []
                for i in similarity_scores.index:
                    if similarity_scores.loc[i] != 0:
                        indices.append(i)

                # Se obtienen las peliculas con tal indice
                df_calculateRating = df_userRatings_movies.iloc[indices[1:11]]
                # Se calcula la media de todas ellas
                prediction = format(df_calculateRating['rating'].mean(), '.1f')

                return str(prediction)

        else:
            mensaje_error("La pelicula que desea predecir no contiene una sinopsis en que basarse")


    def recomendarNPeliculasNoVistasSinopsis(self, user_id, n_peliculas, df_peliculasConSinopsis, df_users_ratings):

        user_id = int(user_id)
        n_peliculas = int(n_peliculas)

        usuarioSeleccionado = df_users_ratings[df_users_ratings["userId"] == user_id]
        df_peliculasCopia = df_peliculasConSinopsis.copy()

        peliculasVistas = []
        for i in usuarioSeleccionado["movieId"]:
            peliculasVistas.append(i)

        df_userMovies_vistas = pd.merge(usuarioSeleccionado, df_peliculasConSinopsis, on="movieId")
        df_userMovies_vistas = df_userMovies_vistas.sort_values(by=["rating"], ascending=False)

        sinopsisPeliculas = ""
        for i in df_userMovies_vistas["sinopsis"][:5]:
            sinopsisPeliculas += i

        df_movies_no_rating_user = df_peliculasConSinopsis[
            df_peliculasConSinopsis['movieId'].isin(usuarioSeleccionado['movieId']) == False]

        movieAniadir = pd.DataFrame(columns=["movieId", "title", "genres", "sinopsis"])
        movieAniadir.loc[0] = [0, "pelicula", "genero", sinopsisPeliculas]
        df_movies_no_rating_user = df_movies_no_rating_user.append(movieAniadir, ignore_index=True)
        selected_movie_index = df_movies_no_rating_user[df_movies_no_rating_user["movieId"] == 0].index

        # Se crea la instancia del tfidf
        tfidfvec = TfidfVectorizer()
        # Convierte el conjunto de datos en una matriz de tokens counts
        tfidf_movie = tfidfvec.fit_transform((df_movies_no_rating_user["sinopsis"]))
        # Se obtiene la similitud del coseno
        cos_sim = cosine_similarity(tfidf_movie, tfidf_movie)

        recommended_movies = []

        # Se obtienen los puntuajes de las similitudes entre las peliculas ordenados de mayor a menor
        similarity_scores = pd.Series(cos_sim[selected_movie_index[0]]).sort_values(ascending=False)

        indices = []
        for i in similarity_scores.index[1:n_peliculas + 1]:
            if similarity_scores.loc[i] != 0:
                indices.append(i)

        # Se obtienen las peliculas con tal indice
        df_top_movies_novistas = df_movies_no_rating_user.iloc[indices]

        contador = 1
        listaPeliculasRecomendadas = []
        for i in range(len(df_top_movies_novistas["title"])):
            listaPeliculasRecomendadas.append(df_top_movies_novistas.loc[indices[i]]["title"])
            contador += 1

        return listaPeliculasRecomendadas
