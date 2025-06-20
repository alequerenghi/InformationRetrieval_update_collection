# Lista dei postings aka i docID
class PostingsList:

    def __init__(self) -> None:
        self._postings_list = []

    # crea una PostingsList da una lista di docID e la ordina (forse non necssario)
    @classmethod
    def from_postings_list(cls, postings_list: list[int]) -> 'PostingsList':
        plist = cls()
        postings_list.sort()
        plist._postings_list = postings_list
        return plist

    # Crea una PostingsList da un singolo docID
    @classmethod
    def from_doc_id(cls, doc_id: int) -> 'PostingsList':
        plist = cls()
        plist._postings_list = [doc_id]
        return plist

    # Concatena due PostingsList. Le liste sono ordinate e i duplicati rimossi. other contiene una PostingsList creata successivamente a self (i docID saranno piu grandi o uguali)
    def merge(self, other: "PostingsList") -> 'PostingsList':
        if self._postings_list == []:
            self._postings_list = other._postings_list
        i = 0  # Start index for the other PostingList.
        last = self._postings_list[-1]  # The last Posting in the current list.
        # Loop through the other PostingList and skip duplicates.
        while (i < len(other._postings_list) and last == other._postings_list[i]):
            i += 1  # Increment the index if a duplicate is found.
        # Append the non-duplicate postings from the other list.
        self._postings_list += other._postings_list[i:]
        return self

    # Ottiene i titoli di documenti dai docID nella PostingsList
    def get_from_corpus(self, corpus) -> list[str]:
        return list(map(lambda x: corpus[x], self._postings_list))

    # Effettua l'intersezione di due PostgingsList con il metodo del doppio indice
    def intersection(self, other: "PostingsList") -> 'PostingsList':
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
        return PostingsList.from_postings_list(plist)

    # Effettua l'unione di due PostingsList con il metodo del doppio indice
    def union(self, other: "PostingsList") -> 'PostingsList':
        plist = []
        i = 0  # indice riferito a self
        j = 0  # indice riferito a other
        # fintanto che gli indici sono piu' piccoli di entrambe le liste
        while (i < len(self._postings_list)) and (j < len(other._postings_list)):
            # aggiungi il docID e aumenta entrambi
            if self._postings_list[i] == other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
                j += 1
            # altrimenti aggiungi il docID e aumenta il piu' piccolo
            elif self._postings_list[i] < other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
            #  aggiungi l'altro e incrementalo
            else:
                plist.append(other._postings_list[j])
                j += 1
        # aggiungi la porzione restante di lista
        if i < len(self._postings_list):  # nel caso in cui self era piu' lunga
            plist += self._postings_list[i:]
        elif j < len(other._postings_list):  # nel caso in cui other era piu' lunga
            plist += other._postings_list[j:]
        return PostingsList.from_postings_list(plist)

    # Effettua la negazione del tipo AND NOT con il metodo dei due indici
    def negation(self, other: 'PostingsList') -> 'PostingsList':
        plist = []
        i = 0
        j = 0
        while (i < len(self._postings_list)) and (j < len(other._postings_list)):
            # se self contiene il docID, scartalo e incrementa entrambi
            if self._postings_list[i] == other._postings_list[j]:
                i += 1
                j += 1
            # aggiungi il docID da self e incrementa se e' piu' piccolo
            elif self._postings_list[i] < other._postings_list[j]:
                plist.append(self._postings_list[i])
                i += 1
            # incrementa other
            else:
                j += 1
        # aggiungi i documenti mancanti da self
        if i < len(self._postings_list):  # se e' piu' lungo di other
            plist += self._postings_list[i:]
        return PostingsList.from_postings_list(plist)

    def __repr__(self) -> str:
        return ", ".join(map(str, self._postings_list))
