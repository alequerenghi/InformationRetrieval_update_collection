import os
from movie_description import MovieDescription
from inverted_index import InvertedIndex, tokenize, normalize
from postings_list import PostingsList
from functools import reduce
import re
import pickle


class IrSystem:
    def __init__(
        self,
        corpus: list[MovieDescription],
        index: InvertedIndex,
        biword: InvertedIndex,
        invalid_vec: list[bool],
        max_size_aux=10000,
    ) -> None:
        self._corpus = corpus
        self._index = index
        self._biword = biword
        self._invalid_vec = invalid_vec
        self._aux_idx = None
        self._aux_biword = None
        self.max_size_aux = max_size_aux

    # Crea l'indice e il biword
    @classmethod
    def from_corpus(cls, corpus: list[MovieDescription]) -> "IrSystem":
        index = InvertedIndex.create_idx_from_corpus(corpus)
        biword = InvertedIndex.create_biword_from_corpus(corpus)
        invalid_vec = [False] * len(corpus)
        ir = cls(corpus, index, biword, invalid_vec)
        return ir

    # Segna documenti cancellati
    def delete_docs(self, documents: list[int]) -> "IrSystem":
        for doc in documents:
            self._invalid_vec[doc] = True
        return self

    # Aggiungi documenti nuovi nel sistema
    def add_docs(self, new_docs: list[MovieDescription]) -> "IrSystem":
        # i nuovi documenti usano docID piu' grandi
        aux = InvertedIndex.create_idx_from_corpus(
            new_docs, len(self._invalid_vec) + 1)
        aux_biword = InvertedIndex.create_biword_from_corpus(
            new_docs, len(self._invalid_vec) + 1
        )
        if self._aux_idx is None:  # se non e' presente nell'indice ausiliario
            self._aux_idx = aux  # aggiungilo
            self._aux_biword = aux_biword
        else:  # altrimenti
            self._aux_idx.merge(aux)
            self._aux_biword.merge(aux_biword)

        if (
            len(self._aux_idx) > self.max_size_aux
        ):  # se l'indice ausiliario e' troppo grande
            self._merge_idx()  # fai merge

        # aggiorna l'invalidation bit vector
        self._invalid_vec += [False] * len(new_docs)
        self._corpus += new_docs
        return self

    # Merge dell'indice ausilario con l'InvertedIndex
    def _merge_idx(self) -> "IrSystem":
        if self._index and self._aux_idx:
            self._index.merge(self._aux_idx)
            self._biword.merge(self._aux_biword)
        elif self._aux_idx:
            self._index = self._aux_idx
            self._biword = self._aux_biword

        # rimuovi i documenti cancellati
        self._index.remove_deleted_docs(self._invalid_vec)
        self._biword.remove_deleted_docs(self._invalid_vec)

        # elimina dal corpus i documenti che sono stati rimossi dall'indice
        for doc_id, to_delete in enumerate(self._invalid_vec):
            if to_delete:
                self._corpus[doc_id].title = "REDACTED"
                self._corpus[doc_id].description = ""
        # svuota gli indici temporanei
        self._aux_idx = None
        self._aux_biword = None
        return self

    # Effettua una query booleana combinando i termini con AND, OR e NOT
    def query(self, query: str) -> list[str]:
        tokens = tokenize_logical_query(query)
        # riscrive la query con gli operatori postfix
        postfixes = infix_to_postfix(tokens)
        stack = []  # PostingsList ancora da processare
        to_optimize = []
        for token in postfixes:
            if (
                token == "AND"
            ):  # caso AND, conviene ottimizzare la query facendo l'intersezione delle liste più corte in primis
                right = stack.pop()
                left = stack.pop() if stack else to_optimize.pop()
                to_optimize += [left, right]
            elif token == "OR":
                right = (
                    self._optimize_and_query(to_optimize) if to_optimize
                    else stack.pop()
                )
                left = stack.pop()
                stack.append(left.union(right))
            elif token == "NOT":
                plist = stack.pop() if stack else to_optimize.pop()
                negated = plist.negation(len(self._invalid_vec))
                stack.append(negated)
            else:  # aggiungi una PostingsList da processare allo stack
                base = self._index.btree.get(
                    token, PostingsList.from_postings_list([]))
                aux = (
                    self._aux_idx.btree.get(
                        token, PostingsList.from_postings_list([]))
                    if self._aux_idx
                    else PostingsList.from_postings_list([])
                )

                # Controlla se base o aux sono vuoti e evita di chiamare merge su liste vuote
                if base._postings_list:
                    if aux._postings_list:
                        stack.append(base.merge(aux))
                    else:
                        stack.append(base)
                elif aux._postings_list:
                    stack.append(aux)
        # estrai l'ultimo elemento (risultato finale)
        result = stack.pop() if stack else to_optimize
        if isinstance(result, list):
            # se è tuttora una lista (= catena di AND), fai l'intersezione
            result = self._optimize_and_query(result)
        # elimina i documenti cancellati
        return self._remove_deleted(result).get_from_corpus(self._corpus)

    def _remove_deleted(self, result: PostingsList) -> PostingsList:
        for doc_id, deleted in enumerate(self._invalid_vec):
            if deleted and doc_id in result._postings_list:
                result._postings_list.remove(doc_id)
        return result

    # Effettua operazioni di AND consecutive facendo l'intersezione di PostingsList piu' corte prima
    def _optimize_and_query(self, to_optimize: list[PostingsList]) -> PostingsList:
        # ordina le PostingsList per lunghezza crescente
        plist = sorted(to_optimize, key=lambda x: len(x._postings_list))
        result = reduce(lambda x, y: x.intersection(y), plist)
        return result

    # Ricerca una sequenza specifica di parola nel corpus con biword
    def phrase_query(self, query: str) -> list[str]:
        biword_query = []
        words = normalize(query).split()
        for i in range(len(words) - 1):
            # concatena le parole della query in coppie
            biword_query.append(words[i] + words[i + 1])
        postings = []
        # cerca le biword nel biword index
        for biword in biword_query:
            base = self._biword.btree.get(
                biword, PostingsList.from_postings_list([]))

            aux = (self._aux_biword.btree.get(
                biword, PostingsList.from_postings_list([]))
                if self._aux_biword
                else PostingsList.from_postings_list([])
            )
            postings.append(base.merge(aux))
        # effettua l'intersezione delle PostingsList trovate
        plist = reduce(lambda x, y: x.intersection(y), postings)
        # rimuovi cancellati e ritorna i risultati
        return self._remove_deleted(plist).get_from_corpus(self._corpus)

    def write_ir_system_to_disk(self, filepath: str = None):
        if filepath is None:
            filepath = "index_files"  # cartella di default

        # Assicura che la cartella esista
        os.makedirs(filepath, exist_ok=True)

        # Filtra e salva solo gli indici puliti
        self._merge_idx()
        self._index.write_idx_to_disk(os.path.join(filepath, "index.pkl"))
        self._biword.write_idx_to_disk(os.path.join(filepath, "biword.pkl"))
        with open(os.path.join(filepath, "corpus.pkl"), "wb") as f:
            pickle.dump(self._corpus, f)

    @classmethod
    def load_ir_system_from_disk(cls, filepath: str) -> None:
        if filepath is None:
            filepath = "index_files"
        with open(os.path.join(filepath, "corpus.pkl"), "rb") as f:
            corpus = pickle.load(f)
        index = InvertedIndex.load_idx_from_disk(
            os.path.join(filepath, "index.pkl"))
        biword = InvertedIndex.load_idx_from_disk(
            os.path.join(filepath, "biword.pkl"))
        invalid_vec = [False] * len(index)
        ir = cls(corpus, index, biword, invalid_vec)
        return ir


# Rende una espressione da infix a postfix: a AND b OR c -> a b AND c OR
def infix_to_postfix(tokens: list[str]) -> list[str]:
    output = []  # risultato finale
    stack = []  # ancora da processare
    for token in tokens:
        if token in ("AND", "OR", "NOT"):  # se e' un operatore
            # finche' ci sono parole da processare e non e' una parentesi
            while stack and stack[-1] != "(" and token != "NOT":
                # aggiungi al risultato finale le parole una dopo l'altra
                output.append(stack.pop())
            stack.append(token)  # aggiungi l'operatore allo stack
        elif token == "(":  # aggiungi la parentesi allo stack
            stack.append(token)
        elif token == ")":
            # fino a che non incontro la parentesi aperta o si svuota lo stack
            while stack and stack[-1] != "(":
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
    pattern = r"\b(?:AND|OR|NOT)\b|\(|\)|\w+"
    raw_tokens = re.findall(pattern, query)

    processed_query = []
    for token in raw_tokens:
        if token.upper() in {"AND", "OR", "NOT", "(", ")"}:
            processed_query.append(token.upper())
        else:
            stemmatized = tokenize(token)
            if stemmatized:  # some terms may be stopwords and filtered out
                # assume single-word queries for simplicity
                processed_query.append(stemmatized[0])
    return processed_query
