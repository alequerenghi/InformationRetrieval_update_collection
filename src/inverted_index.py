import re
import pickle
# barra di avanzamento per visualizzare lo stato durante la creazione dell'indice
from tqdm import tqdm
from BTrees._OOBTree import OOBTree
from stop_words import get_stop_words
# per memorizzare i risultati dello stemming ed evitare calcoli ripetuti
from functools import lru_cache
# stemmer per ridurre le parole alla loro radice
from nltk.stem import SnowballStemmer

from src.postings_list import PostingsList
from src.movie_description import MovieDescription

STOP_WORDS = set(get_stop_words('english'))


class InvertedIndex:
    """
    Classe che rappresenta un inverted index:
    mappa ogni termine a una PostingsList che contiene gli ID dei documenti in cui il termine appare.
    """

    def __init__(self) -> None:
        # Inizializza l'indice come un BTree per rendere più efficienti le operazioni di aggiornamento e ricerca
        self.btree = OOBTree()

    @classmethod
    def create_idx_from_corpus(cls, corpus: list[MovieDescription], max_size=0) -> 'InvertedIndex':
        """
        Crea un InvertedIndex a partire da un corpus di descrizioni di film.
        """
        # dizionario temporaneo per tenere l'indice che stiamo creando
        terms = {}
        # per ogni documento
        for doc_id, content in enumerate(tqdm(corpus), start=max_size):
            # tokenizza la descrizione (normalizzazione + stop word + stemming)
            tokens_list = tokenize(content.description)
            # crea un set per rimuovere i duplicati
            tokens = set(tokens_list)
            # per ogni termine
            for token in tokens:
                # crea una PostingsList con solo questo documento
                plist = PostingsList.create_posting_list_from_single_docID(
                    doc_id)
                # se contenuto
                if token in terms:
                    # aggiunge doc_id alla PostingsList esistente
                    terms[token].merge(plist)
                else:
                    # altrimenti crea una nuova PostingsList
                    terms[token] = plist
        # carica tutto nel BTree
        idx = cls()
        idx.btree.update(terms)
        return idx

    @classmethod
    def create_biword_from_corpus(cls, corpus: list[MovieDescription], max_size=0) -> 'InvertedIndex':
        """
        Crea un biword index: ogni termine dell'indice è una coppia di parole consecutive (per le phrase queries).
        """
        # dizionario temporaneo per tenere l'indice che stiamo creando
        terms = {}
        # per ogni documento
        for doc_id, content in enumerate(tqdm(corpus), start=max_size):
            # normalizza e divide la descrizione in token
            tokens = normalize(content.description).split()
            # per ogni parola
            for i in range(len(tokens) - 1):
                # crea il biword concatenando due token consecutivi
                biword = tokens[i]+tokens[i + 1]
                # crea una PostingsList con solo questo documento
                plist = PostingsList.create_posting_list_from_single_docID(
                    doc_id)
                # se contenuto
                if biword in terms:
                    # aggiunge doc_id alla PostingsList esistente
                    terms[biword].merge(plist)
                else:
                    # altrimenti crea una nuova PostingsList
                    terms[biword] = plist
        # carica tutto nel BTree
        idx = cls()
        idx.btree.update(terms)
        return idx

    def merge(self, other: 'InvertedIndex') -> 'InvertedIndex':
        """
        Unisce questo InvertedIndex con un altro.
        """
        for term, postings in other.btree.items():
            if term in self.btree:
                self.btree[term].merge(postings)
            else:
                self.btree[term] = postings
        return self

    def remove_deleted_docs(self, invalid_vec: list[bool]) -> 'InvertedIndex':
        """
        Rimuove dall'indice i documenti marcati come eliminati (invalid_vec[i] == True).
        """
        # dizionario temporaneo per tenere l'indice che stiamo creando
        filtered_index = {}
        # per ogni entry dell'inverted index, aka per ogni PostingList di ogni termine
        for term, postings in self.btree.items():
            # crea una nuova PostingsList che conterrà solo i documenti validi, ovvero
            # include solo i doc_id che non sono marcati come eliminati
            filtered_postings = PostingsList.create_posting_list(
                [doc_id for doc_id in postings._postings_list
                    if doc_id < len(invalid_vec) and not invalid_vec[doc_id]]
            )
            # solo se sono rimasti docID nella PostingList del temine
            if filtered_postings._postings_list:
                # aggiunge all'indice filtrato temini e relative PostingList
                filtered_index[term] = filtered_postings
        # aggiorna l'albero con l'indice filtrato
        self.btree.clear()
        self.btree.update(filtered_index)
        return self

    def write_idx_to_disk(self, filepath: str) -> None:
        """
        Salva l'InvertedIndex su disco usando pickle.
        """
        dictionary = dict(self.btree.items())
        with open(filepath, 'wb') as f:
            pickle.dump(dictionary, f)

    @classmethod
    def load_idx_from_disk(cls, filepath: str) -> 'InvertedIndex':
        """
        Carica un InvertedIndex da disco.
        """
        with open(filepath, 'rb') as f:
            dictionary = pickle.load(f)
        idx = cls()
        idx.btree.update(dictionary)
        return idx

    def __getitem__(self, key: str) -> PostingsList:
        return self.btree[key]

    def __len__(self) -> int:
        return len(self.btree)

    def __repr__(self) -> str:
        return str(self.btree)


def normalize(text: str) -> str:
    """
    Rimuove la punteggiatura e converte il testo in minuscolo.
    """
    return re.sub(r'[^\w\s^-]', '', text).lower()


@lru_cache(maxsize=100_000)
def cached_stem(word):
    """
    Calcola lo stem di una parola e memorizza il risultato in cache per migliorare le prestazioni.
    """
    stemmer = SnowballStemmer("english")
    return stemmer.stem(word)


def tokenize(text: str) -> list[str]:
    """
    Normalizza il testo, rimuove le stop words e applica lo stemming a ogni parola.
    """
    normalized = normalize(text).split()
    stop_removed = [word for word in normalized if word not in STOP_WORDS]
    return [cached_stem(token) for token in stop_removed]
