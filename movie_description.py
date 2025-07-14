import csv

class MovieDescription:
    """
    Classe che rappresenta una coppia titolo-descrizione di un film.
    """

    def __init__(self, title: str, description: str) -> None:
        self.title = title
        self.description = description

    def __repr__(self) -> str:
        return self.title

def create_corpus(movie_metadata, description_file) -> list[MovieDescription]:
    """
    Crea il corpus di film a partire da due file:
    - movie_metadata: file TSV che contiene informazioni sui film (compreso l'ID e il titolo)
    - description_file: file TSV che contiene l'ID del film e la sua descrizione
    """
    # dizionario che mapperà l'ID del film al suo titolo
    names = {}
    # lista finale che conterrà gli oggetti MovieDescription
    corpus = []
    with open(movie_metadata, 'r') as file: 
        movie_names = csv.reader(file, delimiter='\t')
        for description in movie_names:
            names[description[0]] = description[2]
    with open(description_file, 'r') as file:
        descriptions = csv.reader(file, delimiter='\t')
        for description in descriptions:
            try:
                corpus.append(MovieDescription(
                    names[description[0]], description[1]))
            except KeyError:
                pass
    return corpus
