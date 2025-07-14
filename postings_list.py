# Lista dei postings aka i docID
class PostingsList:
    """
    Classe che rappresenta una posting list. Una PostingsList è una lista di interi
    dove ogni intero è un posting, ovvero il docID di un documento.
    """
    def __init__(self) -> None:
        self._postings_list: list[int] = []

    @classmethod
    def create_posting_list(cls, postings_list: list[int]) -> 'PostingsList':
        """
        Crea una PostingsList a partire da una lista di docID.
        Ordina i docID per garantire che siano sempre in ordine crescente.
        """
        plist = cls()
        postings_list.sort()
        plist._postings_list = postings_list
        return plist

    @classmethod
    def create_posting_list_from_single_docID(cls, doc_id: int) -> 'PostingsList':
        """
        Crea una PostingsList che contiene un singolo docID.
        """
        plist = cls()
        plist._postings_list = [doc_id]
        return plist

    def merge(self, other: "PostingsList") -> 'PostingsList':
        """
        Concatena due PostingsList ordinate evitando duplicati.
        other contiene una PostingsList creata successivamente a self (i docID saranno piu grandi o uguali)
        """
        # se la lista corrente è vuota
        if self._postings_list == []:
            # e se anche other è vuota, ritorna direttamente una nuova PostingsList vuota
            if other._postings_list == []:
                return PostingsList.create_posting_list([])
            else:
                # altrimenti copia direttamente l'altra
                self._postings_list = other._postings_list
        # start index per la posting list other
        i = 0
        # ultimo docID nella lista corrente
        last = self._postings_list[-1] 
        # loop su i. Salta i duplicati in 'other' che coincidono con l'ultimo docID di self
        while(i < len(other._postings_list) and last == other._postings_list[i]):
            i += 1
        # aggiunge tutti i restanti docID (quelli non duplicati)
        self._postings_list += other._postings_list[i:]
        return self

    def get_from_corpus(self, corpus) -> list[str]:
        """
        Ritorna una lista di stringhe descrittive per ciascun docID nella lista,
        nella forma "docID: titolo".
        """
        return list(map(lambda x: str(x) + ": " + str(corpus[x]), self._postings_list))

    def intersection(self, other: "PostingsList") -> 'PostingsList':
        """
        Effettua l'intersezione (AND) tra due PostingsList usando l'algoritmo a doppio indice.
        Ritorna una nuova PostingsList con i docID presenti in entrambe le liste.
        """
        plist = []
        i = 0  # indice riferito a self
        j = 0  # indice riferito a other
        # finché non si eccede la dimensione di ciascuna lista:
        while (i < len(self._postings_list)) and (j < len(other._postings_list)):
            # se c'e' un match aggiungi l'elemento e incrmeneta entrambi
            if self._postings_list[i] == other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
                j += 1
            # altrimenti aumenta il piu piccolo dei due
            elif self._postings_list[i] <= other._postings_list[j]:
                i += 1
            # altrimenti aumenta l'altro
            else:
                j += 1
        return PostingsList.create_posting_list(plist)

    def union(self, other: "PostingsList") -> 'PostingsList':
        """
        Effettua l'unione (OR) tra due PostingsList usando l'algoritmo a doppio indice.
        Ritorna una nuova PostingsList con tutti i docID presenti almeno in una delle due liste.
        """
        plist = []
        # indice riferito a self
        i = 0  
        # indice riferito a other
        j = 0  
        # fintanto che gli indici sono più piccoli di entrambe le liste
        while(i < len(self._postings_list)) and (j < len(other._postings_list)):
            # Caso docID presente in entrambe: lo aggiunge una sola volta
            if self._postings_list[i] == other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
                j += 1
            # Caso aggiunta docID solo da self o solo da other: 
            # aggiunge il docID e aumenta il più piccolo
            elif self._postings_list[i] < other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
            else:
                plist.append(other._postings_list[j])
                j += 1
        # aggiunge eventuali docID rimasti nella lista più lunga
        if i < len(self._postings_list):
            plist += self._postings_list[i:]
        elif j < len(other._postings_list):
            plist += other._postings_list[j:]
        return PostingsList.create_posting_list(plist)

    def negation(self, max_doc: int) -> 'PostingsList':
        """
        Ritorna una nuova PostingsList che rappresenta la negazione:
        tutti i docID possibili [0, ..., max_doc - 1] esclusi quelli presenti in self.
        """
        # crea una lista iniziale con tutti i docID possibili
        plist = [i for i in range(max_doc)]
        # rimuove i docID presenti in self
        for i in self._postings_list:
            plist.remove(i)
        return PostingsList.create_posting_list(plist)

    def __repr__(self) -> str:
        return ", ".join(map(str, self._postings_list))