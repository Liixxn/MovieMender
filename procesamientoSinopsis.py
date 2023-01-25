import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk import word_tokenize, RegexpTokenizer
from nltk.stem import SnowballStemmer





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
    