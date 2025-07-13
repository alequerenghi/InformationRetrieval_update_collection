import csv

class MovieDescription:
    def __init__(self, title: str, description: str) -> None:
        self.title = title
        self.description = description

    def __repr__(self) -> str:
        return self.title

def read_movie_description(movie_metadata, description_file) -> list[MovieDescription]:
    '''
    La funzione che crea il corpus, ogni entry del corpus è la coppia titolo-descrizione
    '''
    names = {}
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
