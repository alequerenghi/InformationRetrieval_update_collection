from movie_description import read_movie_description
import csv
import unittest
from ir_system import IrSystem

from movie_description import read_movie_description
import csv

# File originali
full_metadata_path = '../Code IR/data/movie.metadata.tsv'
full_description_path = '../Code IR/data/plot_summaries.txt'

# File di output ridotti
sample_metadata_path = "movie_metadata_sample.tsv"
sample_description_path = "plot_summaries_sample.txt"

# Numero di elementi da campionare
N = 42204

# Leggi corpus completo
corpus = read_movie_description(full_metadata_path, full_description_path)

# Prendi i primi N
sample_corpus = corpus[:N]

# Salva gli ID dei film selezionati
movie_id_set = set(md.movie_id for md in sample_corpus)

# Scrivi descrizioni basate su ID (non descrizione)
with open(full_description_path, 'r', encoding='utf-8') as infile, \
     open(sample_description_path, 'w', encoding='utf-8') as outfile:
    for line in infile:
        try:
            movie_id, _ = line.strip().split('\t', 1)
        except ValueError:
            continue
        if movie_id in movie_id_set:
            outfile.write(line)

# Scrivi metadati basati su ID (più robusto che usare il titolo)
with open(full_metadata_path, 'r', encoding='utf-8') as infile, \
     open(sample_metadata_path, 'w', encoding='utf-8') as outfile:
    reader = csv.reader(infile, delimiter='\t')
    writer = csv.writer(outfile, delimiter='\t')
    for row in reader:
        if len(row) > 0 and row[0] in movie_id_set:
            writer.writerow(row)

print(f"Creati file ridotti con {len(sample_corpus)} film.")

class TestIrSystemWithDataFiles(unittest.TestCase):

    def setUp(self):
        # File di input reali
        self.metadata_path = "movie_metadata_sample.tsv"
        self.description_path = "plot_summaries_sample.txt"

        # Legge tutto il corpus completo
        full_corpus = read_movie_description(self.metadata_path, self.description_path)

        print(f"Documenti caricati: {len(full_corpus)}")


        # Divide il corpus in 3 parti: A (0-49), B (50-99), C (100-149)
        self.part_A = full_corpus[0:50]
        self.part_B = full_corpus[50:100]
        self.part_C = full_corpus[100:150]

        # Inizializza il sistema IR con A + B
        self.ir = IrSystem.from_corpus(self.part_A + self.part_B)
        #print(f"Doc nel sistema IR iniziale: {len(self.ir)}")  # o metodo simile


        # Salva i titoli di riferimento per i test
        self.deleted_titles = [movie.title for movie in self.part_B]
        self.added_titles = [movie.title for movie in self.part_C]

    def test_add_and_delete_docs(self):
        # Aggiunge C
        self.ir.add_docs(self.part_C)


        # Elimina B
        self.ir.delete_docs(list(range(50, 100)))  # B occupa docID 50-99

        # Verifica che tutti i documenti di C siano presenti tramite una parola chiave
        sample_word = self.part_C[0].description.split()[0]  # prima parola della descrizione
        results = self.ir.query(sample_word)

        found_titles = set(results)
        
        for title in self.added_titles:
            self.assertIn(title, found_titles, f"'{title}' non trovato nei risultati")

        # Verifica che i documenti di B siano stati rimossi
        sample_word_b = self.part_B[0].description.split()[0]
        results_after_delete = self.ir.query(sample_word_b)

        removed_titles = set(results_after_delete)
        for title in self.deleted_titles:
            self.assertNotIn(title, removed_titles, f"'{title}' non dovrebbe essere nei risultati")

        results = self.ir.query(sample_word)
        print("Risultati query per parola C:", results)
        results_after_delete = self.ir.query(sample_word_b)
        print("Risultati query per parola B dopo delete:", results_after_delete)


if __name__ == '__main__':
    unittest.main()




