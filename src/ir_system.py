import os
from functools import reduce
import re
import pickle

from src.movie_description import MovieDescription
from src.inverted_index import InvertedIndex, tokenize, normalize
from src.postings_list import PostingsList


class IrSystem:
    """
    Sistema di Information Retrieval che gestisce:
    - InvertedIndex per ricerca booleana
    - biword index per le ricerche di frasi
    - documenti cancellati e aggiunti dinamicamente
    """

    def __init__(self, corpus: list[MovieDescription], index: InvertedIndex, biword: InvertedIndex,
                 invalid_vec: list[bool], max_size_aux=80000) -> None:
        """
        Inizializza il sistema IR con corpus, InvertedIndex principale e secondario,
        indice biword principale e secondario, vettore di invalidazione e massima dimensione dell'indice ausiliario.
        """
        self._corpus = corpus
        self._index = index
        self._biword = biword
        self._invalid_vec = invalid_vec
        self._aux_idx = None
        self._aux_biword = None
        self.max_size_aux = max_size_aux

    @classmethod
    def create_system(cls, corpus: list[MovieDescription]) -> "IrSystem":
        """
        Crea un sistema IR generando InvertedIndex e biword dal corpus e l'invalid vetor relativo.
        """
        index = InvertedIndex.create_idx_from_corpus(corpus)
        biword = InvertedIndex.create_biword_from_corpus(corpus)
        invalid_vec = [False] * len(corpus)
        ir = cls(corpus, index, biword, invalid_vec)
        return ir

    def delete_docs(self, documents: list[int]) -> "IrSystem":
        """
        Segna, nell'invalid vector, i documenti specificati come eliminati.
        """
        for doc in documents:
            self._invalid_vec[doc] = True
        return self

    def add_docs(self, new_docs: list[MovieDescription]) -> "IrSystem":
        """
        Aggiunge nuovi documenti al sistema, aggiornando l'indice ausiliario.
        """
        # crea un InvertedIndex dai nuovi documenti passati,
        # i nuovi docID partiranno dall'ultimo utlizzato (dalla fine del corpus attuale)
        aux = InvertedIndex.create_idx_from_corpus(
            new_docs, len(self._invalid_vec))
        # crea anche l'indice biword
        aux_biword = InvertedIndex.create_biword_from_corpus(
            new_docs, len(self._invalid_vec))
        # se l'indice ausiliario è vuoto
        if self._aux_idx is None:
            # gli indici appena creati diventano quelli ausiliari
            self._aux_idx = aux
            self._aux_biword = aux_biword
        else:
            # altrimenti fa il merge con quelli già presenti
            self._aux_idx.merge(aux)
            self._aux_biword.merge(aux_biword)

        # se l'indice ausiliario è troppo grande
        if (len(self._aux_idx) > self.max_size_aux):
            # fa merge con quello principale
            self._merge_idx()

        # aumenta l'invalidation bit vector tante volta quante il numero di nuovi documenti aggiunti
        self._invalid_vec += [False] * len(new_docs)
        # aggiunge al corpus i nuovi documenti
        self._corpus += new_docs
        return self

    def _merge_idx(self) -> "IrSystem":
        """
        Effettua il merge dell'indice ausiliario con quello principale e rimuove documenti cancellati.
        """
        # se esistono entrambi, fa merge
        if self._index and self._aux_idx:
            self._index.merge(self._aux_idx)
            self._biword.merge(self._aux_biword)
        # se non esiste l'indice principale (caso raro)
        elif self._aux_idx:
            self._index = self._aux_idx
            self._biword = self._aux_biword

        # aggiorna le PostingList dell'inverted index (toglie i docID segnati come eliminati)
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

    def query(self, query: str) -> list[str]:
        """
        Esegue una query booleana sul corpus, usando operatori AND, OR e NOT. 
        Ritorna la lista di titoli/descrizioni dei documenti trovati.
        """
        # tokenizza la query
        tokens = tokenize_logical_query(query)
        # converte da infix a postfix (per calcolo più semplice)
        postfixes = infix_to_postfix(tokens)
        # stack per PostingList ancora da processare
        stack = []
        # lista di PostingList da ottimizzare con AND multipli
        to_optimize = []
        # per ogni token dell’espressione in notazione postfix
        for token in postfixes:
            # Caso in cui il token è l’operatore AND:
            # per migliorare l’efficienza conviene prima accumulare le posting list da confrontare,
            # per poi eseguire l'intersezione fra tutte le liste più corte alla fine (_optimize_and_query)
            if (token == "AND"):
                # estrae la posting list più a destra dallo stack
                right = stack.pop()
                # se lo stack non è vuoto, estrae la posting list di sinistra;
                # altrimenti la prende da 'to_optimize' (accumulatore usato in precedenza)
                left = stack.pop() if stack else to_optimize.pop()
                # aggiunge entrambe alla lista da ottimizzare, dove alla fine farà un AND multiplo
                to_optimize += [left, right]
            # Caso in cui il token è l’operatore OR
            elif token == "OR":
                # se ha già posting list da ottimizzare, prima esegue l’AND multiplo su di esse;
                # altrimenti prende semplicemente la posting list più a destra dallo stack
                right = (
                    self._optimize_and_query(to_optimize) if to_optimize
                    else stack.pop()
                )
                # prende la posting list più a sinistra dallo stack
                left = stack.pop()
                # esegue l’unione tra le due posting list ottenute e rimette il risultato nello stack
                stack.append(left.union(right))
            # Caso in cui il token è l’operatore NOT
            elif token == "NOT":
                # prende la posting list su cui applicare la negazione:
                # se lo stack non è vuoto, la prende da lì;
                # altrimenti da to_optimize
                plist = stack.pop() if stack else to_optimize.pop()
                # crea la posting list negata rispetto a tutti i documenti disponibili
                negated = plist.negation(len(self._invalid_vec))
                # inserisce il risultato nello stack
                stack.append(negated)
            # Caso in cui il token è un termine normale (non un operatore)
            else:
                # cerca la posting list di quel termine nell’indice principale e in quello ausiliario
                # se non c'è, usa una lista vuota
                base = self._index.btree.get(
                    token, PostingsList.create_posting_list([]))
                aux = (self._aux_idx.btree.get(token, PostingsList.create_posting_list([]))
                       if self._aux_idx
                       else PostingsList.create_posting_list([])
                       )
                # controlla se le posting list trovate sono non vuote
                if base._postings_list:
                    if aux._postings_list:
                        # entrambe le liste hanno risultati: fa il merge per combinarle
                        stack.append(base.merge(aux))
                    else:
                        # solo la lista principale ha risultati: usa quella
                        stack.append(base)
                elif aux._postings_list:
                    # solo la lista ausiliaria ha risultati: usa quella
                    stack.append(aux)

        # estrae l'ultimo elemento (che rappresenta il risultato finale della query) dallo stack,
        # oppure, se lo stack è vuoto (può succedere se abbiamo solo operatori AND accumulati),
        # prende direttamente la lista 'to_optimize' che contiene le posting list da intersecare
        result = stack.pop() if stack else to_optimize
        # se è tuttora una lista (= catena di AND), fa l'intersezione
        if isinstance(result, list):
            result = self._optimize_and_query(result)

        # a questo punto ha una sola PostingsList con i docID validi.
        # rimuove eventuali docID che erano stati marcati come cancellati (invalid_vec)
        # e infine estrae dal corpus i titoli dei documenti corrispondenti
        return self._remove_deleted(result).get_from_corpus(self._corpus)

    def _remove_deleted(self, result: PostingsList) -> PostingsList:
        """
        Rimuove dai risultati i documenti marcati come eliminati nell'invalid vector.
        """
        for doc_id, deleted in enumerate(self._invalid_vec):
            if deleted and doc_id in result._postings_list:
                result._postings_list.remove(doc_id)
        return result

    def _optimize_and_query(self, to_optimize: list[PostingsList]) -> PostingsList:
        """
        Esegue più operazioni AND ottimizzando l'ordine per intersecare prima le liste più piccole.
        Ritorna la PostingsList risultante dall'intersezione.
        """
        # ordina le PostingsList per lunghezza crescente
        plist = sorted(to_optimize, key=lambda x: len(x._postings_list))
        # applica l'operatore AND (intersection) a tutte le posting list ordinate.

        # se non sono stati trovari risultati ritorna una lista vuota
        if not plist:
            return PostingsList.create_posting_list([])

        result = reduce(lambda x, y: x.intersection(y), plist)
        return result

    def phrase_query(self, query: str) -> list[str]:
        """
        Esegue una ricerca esatta di una frase usando l'indice biword.
        Ritorna la lista dei documenti che contengono la frase. 
        """
        # lista che conterrà le coppie di parole (biword) generate dalla frase
        biword_query = []
        # normalizza la query
        words = normalize(query).split()

        for i in range(len(words) - 1):
            # concatena le parole successive della query per formare le biword
            biword_query.append(words[i] + words[i + 1])
        # lista che conterrà le PostingsList trovate per ciascuna biword
        postings = []
        # per ogni biword della query
        for biword in biword_query:
            # cerca le biword nell'indice principale e nell'ausiliario
            # se non le trova, ritorna lista vuota
            base = self._biword.btree.get(
                biword, PostingsList.create_posting_list([]))

            aux = (self._aux_biword.btree.get(biword, PostingsList.create_posting_list([]))
                   if self._aux_biword
                   else PostingsList.create_posting_list([])
                   )
            # unisce (merge) le PostingsList dei due indici per la specifica biword
            postings.append(base.merge(aux))

        # se non trova risultati restituisce una stringa vuota
        if not postings:
            return []
        # se trova una sola biword (frase di 2 parole),
        # restituisce direttamente i docID dopo aver rimosso i cancellati
        if len(postings) == 1:
            return self._remove_deleted(postings[0]).get_from_corpus(self._corpus)

        # se invece ci sono più biword, calcola l'intersezione:
        plist = reduce(lambda x, y: x.intersection(y), postings)

        # a questo punto ha una sola PostingsList con i docID validi.
        # rimuove eventuali docID che erano stati marcati come cancellati (invalid_vec)
        # e infine estrae dal corpus i titoli dei documenti corrispondenti
        return self._remove_deleted(plist).get_from_corpus(self._corpus)

    def write_ir_system_to_disk(self, filepath: str = None):
        """
        Salva su disco l'indice principale, il biword index e il corpus.
        """
        # se non viene passato un path
        if filepath is None:
            # crea una cartella di default
            filepath = "index_files"
        # si assicura che la cartella esista
        os.makedirs(filepath, exist_ok=True)
        # prima di srivere su disco si fa il merge degli indici (principale e ausiliario)
        self._merge_idx()

        self._index.write_idx_to_disk(os.path.join(filepath, "index.pkl"))
        self._biword.write_idx_to_disk(os.path.join(filepath, "biword.pkl"))
        with open(os.path.join(filepath, "corpus.pkl"), "wb") as f:
            pickle.dump(self._corpus, f)

    @classmethod
    def load_ir_system_from_disk(cls, filepath: str = None) -> None:
        """
        Carica il sistema IR da disco.
        """
        if filepath is None:
            filepath = "index_files"
        with open(os.path.join(filepath, "corpus.pkl"), "rb") as f:
            corpus = pickle.load(f)
        index = InvertedIndex.load_idx_from_disk(
            os.path.join(filepath, "index.pkl"))
        biword = InvertedIndex.load_idx_from_disk(
            os.path.join(filepath, "biword.pkl"))
        invalid_vec = [False] * len(corpus)
        ir = cls(corpus, index, biword, invalid_vec)
        return ir

    def __len__(self):
        return sum(x.title != "REDACTED" for x in self._corpus)


def infix_to_postfix(tokens: list[str]) -> list[str]:
    """
    Converte una lista di token da notazione infix a postfix.
    a AND b OR c -> a b AND c OR
    """
    # query risultato finale
    output = []
    # token ancora da processare
    stack = []
    for token in tokens:
        # Caso il token è un operatore
        if token in ("AND", "OR", "NOT"):
            # finchè ci sono token da processare e il token non è una parentesi, né un NOT
            while stack and stack[-1] != "(" and token != "NOT":
                # aggiungi alla query finale un token dopo l'altro
                output.append(stack.pop())
            # poi aggiungi l'operatore allo stack
            stack.append(token)
        # Caso il token è aperta parentesi
        elif token == "(":
            # aggiungi la parentesi allo stack
            stack.append(token)
        # Caso il token è chiusa parentesi
        elif token == ")":
            # fino a che non incontri la parentesi aperta o si svuota lo stack
            while stack and stack[-1] != "(":
                # aggiungi all'output il contenuto dello stack
                output.append(stack.pop())
            # poi rimuovi dallo stak '('
            stack.pop()
        # Caso in cui il token è un termine normale (non un operatore)
        else:
            # aggiungi il termine all'outpuit
            output.append(token)
    # svuota lo stack mettendo in output
    while stack:
        output.append(stack.pop())
    return output


def tokenize_logical_query(query: str):
    """
    Tokenizza una query, mantenendo operatori e parentesi.
    """
    # RegEx per parole, operatori e parentesi
    pattern = r"\b(?:AND|OR|NOT)\b|\(|\)|\w+"
    raw_tokens = re.findall(pattern, query)

    # lista processata di token della query
    processed_query = []
    # per ogni token della query
    for token in raw_tokens:
        # se sono operatori logici li mantiene
        if token.upper() in {"AND", "OR", "NOT", "(", ")"}:
            processed_query.append(token.upper())
        else:
            # altrimenti tokenizza, normalizza, stemma e rimuove le stop words
            stemmatized = tokenize(token)
            if stemmatized:
                # salva il token (se non è una stop word)
                processed_query.append(stemmatized[0])
    return processed_query
