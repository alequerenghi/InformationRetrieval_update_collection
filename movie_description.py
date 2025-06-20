import csv


class MovieDescription:
    def __init__(self, title: str, description: str) -> None:
        self.title = title
        self.description = description

    def __repr__(self) -> str:
        return self.title

# leggi il file descrizione e metadata e crea un corpus (collection di documenti)


def read_movie_description(movie_metadata, description_file) -> list[MovieDescription]:
    names = {}
    corpus = []
    with open(movie_metadata, 'r') as file:  # leggi i metadati
        movie_names = csv.reader(file, delimiter='\t')
        for description in movie_names:  # aggiungi a names la coppia id_film: titolo
            names[description[0]] = description[2]
    with open(description_file, 'r') as file:  # leggi le descrizioni
        descriptions = csv.reader(file, delimiter='\t')
        for description in descriptions:
            try:
                # aggiungi al corpus il titolo e la descrizione di ciascun film
                corpus.append(MovieDescription(
                    # il docID e' la posizione del documento nel corpus
                    names[description[0]], description[1]))
            except KeyError:
                pass
    return corpus
