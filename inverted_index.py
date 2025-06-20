from postings_list import PostingsList
import pickle
import re
from tqdm import tqdm
from BTrees import OOBTree
from stop_words import get_stop_words

stop_words = get_stop_words('english')

def normalize(text):
    """Remove punctuation and convert text to lowercase"""
    return re.sub(r'[^\w\s^-]', '', text).lower()


def tokenize(content) -> list:
    """Split normalized text into tokens"""
    return normalize(content).split()


class InvertedIndex:

    def __init__(self) -> None:
        self.btree = OOBTree()  # usa un Btree per rendere piu' veloci aggiornamenti dell'indice

    @classmethod
    def from_corpus(cls, corpus, max_size=0) -> 'InvertedIndex':
        terms = {}  # dizionario temporaneo per tenere l'indice iniziale
        # per ogni documento
        for doc_id, content in enumerate(tqdm(corpus, initial=max_size)):
            tokens_list = tokenize(content.description)
            tokens_filtered = [t for t in tokens_list if t not in stop_words]
            tokens = set(tokens_filtered)
            # crea un set dei termini che contiene
            # tokens = set(tokenize(content.description))
            for token in tokens:  # per ogni termine
                plist = PostingsList.from_doc_id(doc_id)
                if token in terms:  # se contenuto
                    terms[token].merge(plist)  # fai merge delle PostingsList
                else:  # altrimenti aggiungi
                    terms[token] = plist
        idx = cls()
        idx.btree.update(terms)
        return idx

    # crea il biword index per le phrase queries
    @classmethod
    def from_corpus_biword(cls, corpus, max_size=0) -> 'InvertedIndex':
        terms = {}
        # per ogni documento
        for doc_id, content in enumerate(tqdm(corpus, initial=max_size)):
            tokens = tokenize(content.description)
            # per ogni parola
            for i in range(len(tokens) - 1):
                biword = tokens[i]+tokens[i+1]
                plist = PostingsList.from_doc_id(doc_id)
                if biword in terms:
                    terms[biword].merge(plist)
                else:
                    terms[biword] = plist
        idx = cls()
        idx.btree.update(terms)
        return idx

    def merge(self, other: 'InvertedIndex') -> 'InvertedIndex':
        for term, postings in other.btree.items():
            if term in self.btree:
                self.btree[term].merge(postings)
            else:
                self.btree[term] = postings
        return self

    def __getitem__(self, key: str) -> PostingsList:
        return self.btree[key]

    def __len__(self) -> int:
        return len(self.btree)

    def __repr__(self) -> str:
        return self.btree1


    def save_index(self, filepath: str):
        # Converte il btree in dizionario semplice per serializzare
        simple_dict = dict(self.btree.items())
        with open(filepath, 'wb') as f:
            pickle.dump(simple_dict, f)

    @classmethod
    def load_index(cls, filepath: str) -> 'InvertedIndex':
        with open(filepath, 'rb') as f:
            simple_dict = pickle.load(f)
        idx = cls()
        # ricrea OOBTree e inserisce tutti i termini
        idx.btree.update(simple_dict)
        return idx
    
    def filter_deleted(self, invalid_vec: list[int]) -> 'InvertedIndex':
        """Crea una nuova InvertedIndex senza i documenti marcati come eliminati"""
        filtered_index = InvertedIndex()
        for term, postings in self.btree.items():
            # Crea una nuova PostingsList filtrata
            filtered_postings = PostingsList.from_postings_list(
                [doc_id for doc_id in postings._postings_list 
                if doc_id < len(invalid_vec) and not invalid_vec[doc_id]]
            )
            if filtered_postings._postings_list:  # Solo se ci sono ancora documenti
                filtered_index.btree[term] = filtered_postings
        return filtered_index
