import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup



# Informacion para el web scraping
header = {
    'User-Agent': 'Chrome 108.0.5359.125',
    'Accept-Language': 'es'
}
# Lista donde se almacenaran las sinopsis de las peliculas
columnaSinopsis = []

class extraccionSinopsisPeliculas():

    def __init__(self):
        self.df_links = pd.read_csv('csv/links.csv')

    # Funcion que realiza el web scraping de las sinopsis de las peliculas y las almacena en una lista
    def scrapingSinopsisPeliculas(self):

        self.df_links['tmdbId'] = self.df_links['tmdbId'].fillna(0)
        for idPeli in self.df_links['tmdbId']:

            if idPeli != 0:
                try:
                    url = "https://www.themoviedb.org/movie/" + str(int(idPeli))
                    page = requests.get(url, headers=header)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    sinopsis = soup.find(class_="overview")
                    sinopsis = str(sinopsis.text)
                    columnaSinopsis.append(sinopsis)
                except:
                    columnaSinopsis.append("Sin Informacion")
            else:
                columnaSinopsis.append("Sin Informacion")

    # Funcion que escribe en un fichero de texto las sinopsis de las peliculas
    def escribirSinopsisFichero(self):
        with open(r'sinopsis.txt', "a", encoding="utf-8") as file:
            for i in columnaSinopsis:
                raw = repr(i)
                raw_replace = raw.replace('\\n', "").replace("'", "")
                file.write(raw_replace + "|||")

    # Funcion que carga el fichero de texto con las sinopsis de las peliculas y las almacena en un dataframe
    def cargarFicheroSinopsisDataframe(self):
        self.df_sinopsis = pd.DataFrame(columns=["sinopsis"])
        with open('sinopsis.txt', 'r', encoding="utf-8") as file:
            contents = file.read()
            contents = contents.split('|||')

        file.close()
        self.df_sinopsis["sinopsis"] = contents
        self.df_sinopsis = self.df_sinopsis.iloc[:-1, :]

        return self.df_sinopsis