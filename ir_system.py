import json
import os
from typing import Optional
from movie_description import MovieDescription
from inverted_index import InvertedIndex, tokenize, normalize
from postings_list import PostingsList
from functools import reduce
import re


class IrSystem:
    def __init__(self, corpus: list[MovieDescription], index: InvertedIndex, biword: InvertedIndex, invalid_vec: list[int], max_size_aux=10000) -> None:
        self._corpus = corpus
        self._index = index
        self._biword = biword
        self._invalid_vec = invalid_vec
        self._temp_idx = None
        self._temp_biword = None
        self.max_size_aux = max_size_aux

    # Crea l'indice e il biword
    @classmethod
    def from_corpus(cls, corpus: list[MovieDescription]) -> 'IrSystem':
        index = InvertedIndex.from_corpus(corpus)
        biword = InvertedIndex.from_corpus_biword(corpus)
        invalid_vec = [0] * len(corpus)
        ir = cls(corpus, index, biword, invalid_vec)
        ir.save_index_to_disk()
        ir.save_invalid_vec()
        return ir

    # Segna documenti cancellati
    def delete_docs(self, documents: list[int]) -> 'IrSystem':
        for doc in documents:
            self._invalid_vec[doc] = 1
        return self

    # Aggiungi documenti nuovi all'indice ausiliario
    def add_docs(self, corpus: list[MovieDescription]) -> 'IrSystem':
        # i nuovi documenti usano docID piu' grandi
        aux = InvertedIndex.from_corpus(corpus, len(self._invalid_vec))
        aux_biword = InvertedIndex.from_corpus_biword(
            corpus, len(self._invalid_vec))
        if self._temp_idx is None:  # se non e' presente nell'indice ausiliario
            self._temp_idx = aux  # aggiungilo
        else:  # altrimenti
            self._temp_idx.merge(aux)
        if self._temp_biword is None:
            self._temp_biword = aux_biword
        else:
            self._temp_biword.merge(aux_biword)

        if len(self._temp_idx) > self.max_size_aux:  # se l'indice ausiliario e' troppo grande
            self._merge_idx()  # fai merge

        # aggiorna la dimensione massima attuale
        self.max_size_aux += len(corpus)
        # aggiorna l'invalidation bit vector
        self._invalid_vec += [0] * len(corpus)
        self._corpus += corpus
        return self

    # Merge dell'indice ausilario con l'InvertedIndex
    def _merge_idx(self) -> 'IrSystem':
        if self._index is None:
            self._index = self._temp_idx
        else:
            self._index.merge(self._temp_idx)

        if self._biword is None:
            self._biword = self._temp_biword
        else:
            self._biword.merge(self._temp_biword)
        # rimuovi i documenti cancellati
        self._index.filter_deleted(self._invalid_vec)
        self._biword.filter_deleted(self._invalid_vec)
        # svuota gli indici temporanei
        self._temp_idx = None
        self._temp_biword = None
        self.save_index_to_disk()
        self.save_invalid_vec()
        return self

    # Effettua una query booleana combinando i termini con AND, OR e NOT
    def query(self, query: str) -> list[str]:
        tokens = tokenize_logical_query(query)
        # riscrive la query con gli operatori postfix
        postfix = infix_to_postfix(tokens)
        stack = []  # PostingsList ancora da processare
        for token in postfix:
            if token in ('AND', 'OR', 'NOT'):
                right = stack.pop()
                left = stack.pop()
                if token == 'AND':  # caso AND, conviene ottimizzare la query facendo l'intersezione delle liste più corte in primis
                    if not isinstance(left, list):
                        left = [left]
                    if not isinstance(right, list):
                        right = [right]
                    # aggiungi allo stack una lista [left, right]
                    stack.append(left + right)
                elif token in ('OR', 'NOT'):
                    if isinstance(left, list):  # se left è una lista (catena di AND)
                        # effettua la sequenza di AND
                        left = self._optimize_and_query(left)
                    if isinstance(right, list):  # se right è una lista (catena di AND)
                        # effettua la sequenza di AND
                        right = self._optimize_and_query(right)
                    if token == 'OR':  # effettua l'OR
                        stack.append(left.union(right))
                    else:  # effettua il NOT (AND NOT)
                        stack.append(left.negation(right))
            else:  # aggiungi una PostingsList da processare allo stack
                base = self._index.btree.get(
                    token, PostingsList.from_postings_list([]))
                aux = self._temp_idx.btree.get(token, PostingsList.from_postings_list(
                    [])) if self._temp_idx else PostingsList.from_postings_list([])

                # Controlla se base o aux sono vuoti e evita di chiamare merge su liste vuote
                if not base._postings_list and not aux._postings_list:
                    # lista vuota
                    stack.append(PostingsList.from_postings_list([]))
                elif not base._postings_list:
                    stack.append(aux)
                elif not aux._postings_list:
                    stack.append(base)
                else:
                    stack.append(base.merge(aux))
        result = stack.pop()  # estrai l'ultimo elemento (risultato finale)
        if isinstance(result, list):  # se è tuttora una lista (= catena di AND), fai l'intersezione
            result = self._optimize_and_query(result)
        # elimina i documenti cancellati
        return self._remove_deleted(result).get_from_corpus(self._corpus)

    def _remove_deleted(self, result: PostingsList) -> PostingsList:
        for doc_id, deleted in enumerate(self._invalid_vec):
            if deleted and doc_id in result._postings_list:
                result._postings_list.remove(doc_id)
        return result

    # Effettua operazioni di AND consecutive facendo l'intersezione di PostingsList piu' corte prima
    def _optimize_and_query(self, terms: list[PostingsList]) -> PostingsList:
        # ordina le PostingsList per lunghezza crescente
        plist = sorted(terms, key=lambda x: len(x._postings_list))
        result = reduce(lambda x, y: x.intersection(y), plist)
        return result

    # Ricerca una sequenza specifica di parola nel corpus con biword
    def phrase_query(self, query: str) -> list[str]:
        biword_query = []
        words = normalize(query).split()
        for i in range(len(words)-1):
            # concatena le parole della query in coppie
            biword_query.append(words[i]+words[i+1])
        postings = []
        # cerca le biword nel biword index
        for biword in biword_query:
            base = self._biword.btree.get(
                biword, PostingsList.from_postings_list([]))

            aux = self._temp_biword.btree.get(biword, PostingsList.from_postings_list(
                [])) if self._temp_biword else PostingsList.from_postings_list([])
            postings.append(base.merge(aux))
        # effettua l'intersezione delle PostingsList trovate
        plist = reduce(lambda x, y: x.intersection(y), postings)
        # rimuovi cancellati e ritorna i risultati
        return self._remove_deleted(plist).get_from_corpus(self._corpus)

    #
    #
    #
    # Specify the path where data is saved
    #
    #
    def save_invalid_vec(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self._invalid_vec, f)

    def load_invalid_vec(self, filepath: str) -> None:
        with open(filepath, 'r') as f:
            invalid_vec = json.load(f)
        self._invalid_vec = invalid_vec

    def save_index_to_disk(self, filepath: str):
        if filepath is None:
            filepath = "index_files"  # cartella di default

        # Assicura che la cartella esista
        os.makedirs(filepath, exist_ok=True)

        # Filtra e salva solo gli indici puliti
        self._merge_idx()
        self._index.save_index(os.path.join(filepath, "index.pkl"))
        self._biword.save_index(os.path.join(filepath, "biword.pkl"))

    def load_index_from_disk(self, filepath: str) -> None:
        if filepath is None:
            filepath = "index_files"

        self._index = InvertedIndex.load_index(
            os.path.join(filepath, "index.pkl"))
        self._biword = InvertedIndex.load_index(
            os.path.join(filepath, "biword.pkl"))


# Rende una espressione da infix a postfix: a AND b OR c -> a b AND c OR
def infix_to_postfix(tokens: list[str]) -> list[str]:
    output = []  # risultato finale
    stack = []  # ancora da processare
    for token in tokens:
        if token in ('AND', 'OR', 'NOT'):  # se e' un operatore
            # finche' ci sono parole da processare e non e' una parentesi
            while (stack and stack[-1] != '('):
                # aggiungi al risultato finale le parole una dopo l'altra
                output.append(stack.pop())
            stack.append(token)  # aggiungi l'operatore allo stack
        elif token == '(':  # aggiungi la parentesi allo stack
            stack.append(token)
        elif token == ')':
            # fino a che non incontro la parentesi aperta o si svuota lo stack
            while stack and stack[-1] != '(':
                # aggiungo all'output il contenuto dello stack
                output.append(stack.pop())
            stack.pop()  # remove '('
        else:  # aggiungi un termine all'outpuit
            output.append(token)
    while stack:  # svuota lo stack
        output.append(stack.pop())
    return output


def tokenize_logical_query(query: str):
    # Tokenize by whitespace and keep parentheses and operators
    pattern = r'\b(?:AND|OR|NOT)\b|\(|\)|\w+'
    raw_tokens = re.findall(pattern, query)

    processed_tokens = []
    for token in raw_tokens:
        if token.upper() in {'AND', 'OR', 'NOT', '(', ')'}:
            processed_tokens.append(token.upper())
        else:
            lemmatized = tokenize(token)
            if lemmatized:  # some terms may be stopwords and filtered out
                # assume single-word queries for simplicity
                processed_tokens.append(lemmatized[0])
    return processed_tokens
