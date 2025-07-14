from ir_system import IrSystem
from movie_description import *

def add_document(ir: IrSystem, title: str, description: str):
    """
    Aggiunge un singolo documento all'indice corrente.
    """
    ir.add_docs(new_docs = [MovieDescription(title, description)])
    print("Document successfully added")

def add_documents(ir: IrSystem, metadata_file: str, description_file: str):
    """
    Aggiunge più documenti leggendo da file di metadati e descrizioni.
    """
    corpus = create_corpus(metadata_file, description_file)
    ir.add_docs(corpus)
    print("Documents successfully added")

def delete_documents(docs_to_delete: str, ir: IrSystem) -> None:
    """
    Elimina documenti dall'indice dati gli ID o intervalli di ID (es. '1 5 7-9').
    """
    # crea un set in cui salvare i docID dei documenti da eliminare
    ids_to_delete = set()

    for part in docs_to_delete.split():
        # Caso: è un intervallo (es. 7-9)
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    print(f"Error: Invalid range {part} (start > end)")
                    continue
                # oss. range(start, end) va da start a end-1, quindi fa +1 per includere end
                ids_to_delete.update(range(start, end + 1))
            except ValueError:
                print(f"Error: Invalid range format '{part}'")
        # Caso: è un singolo numero o una lista di numeri
        else:
            try:
                doc_id = int(part)
                ids_to_delete.add(doc_id)
            except ValueError:
                print(f"Error: Invalid document ID '{part}'")

    if not ids_to_delete:
        print("No valid document IDs to delete")
        return

    # ordina la lista e chiama la funzione di IRSystem che segna, nell'invalid vector, 
    # i documenti specificati come eliminati.
    ids_list = sorted(ids_to_delete)
    ir.delete_docs(ids_list)

    # stampa un riassunto delle eliminazioni (singoli numeri o intervalli consecutivi)
    if len(ids_list) == 1:
        print(f"Deleted document: {ids_list[0]}")
    else:
        ranges = []
        start = ids_list[0]
        prev = start

        for doc_id in ids_list[1:]:
            if doc_id != prev + 1:
                ranges.append((start, prev))
                start = doc_id
            prev = doc_id
        ranges.append((start, prev))

        range_strings = [f"{s}-{e}" if s != e else str(s) for s, e in ranges]
        print(f"Deleted documents: {', '.join(range_strings)}")

def help_menu():
    """
    Stampa la lista dei comandi disponibili.
    """
    print("Available commands:")
    print(" - help")
    print(" - build <titles_file> <descriptions_file>")
    print(" - load index")
    print(" - <query>")
    print(' - "<phrase query>"')
    print(' - add <title> | <description>')
    print(" - add <titles_file> <descriptions_file>")
    print(" - del <docIDs> (e.g. 'del 1 5' or 'del 7-9')")
    print(" - len index (i.e. index size)")
    print(" - exit")

def load_index():
    """
    Carica l'indice salvato su disco dalla cartella 'index_files'.
    """
    print("Loading index...")
    try:
        ir = IrSystem.load_ir_system_from_disk("index_files")
        print("Index successfully loaded.")
    except Exception as e:
        print(f"Index loading error: {e}")
        print("Index not found. Type 'build <titles_file> <descriptions_file>' to create it")
    return ir

def build_index(metadata_file, description_file):
    """
    Crea un nuovo indice a partire dai file di metadati e descrizioni.
    """
    print("Creating index and biword index...")
    corpus = create_corpus(metadata_file, description_file)
    ir = IrSystem.create_system(corpus)
    print("Index successfully created.")
    return ir

def search(query: str, ir: IrSystem):
    """
    Esegue una ricerca: phrase query se tra virgolette, altrimenti normale.
    """
    print(f"Performing search for: '{query}'")
    results = []
    # se phrase query
    if query.startswith('"') and query.endswith('"'):
        # rimuove virgolette e cerca come frase
        phrase = query[1:-1]
        results = ir.phrase_query(phrase)
    else:
         # query normale
        results = ir.query(query)
    return results

def print_title():
    ascii_art = r"""
  _    _           _       _       _____           _
 | |  | |         | |     | |     |_   _|         | |
 | |  | |_ __   __| | __ _| |_ ___  | |  _ __   __| | _____  __
 | |  | | '_ \ / _` |/ _` | __/ _ \ | | | '_ \ / _` |/ _ \ \/ /
 | |__| | |_) | (_| | (_| | ||  __/_| |_| | | | (_| |  __/>  <
  \____/| .__/ \__,_|\__,_|\__\___|_____|_| |_|\__,_|\___/_/\_\
        | |
        |_|

 by Alessandro, Cristina and Gabriele
    """
    print(ascii_art)

def main():
    print_title()
    print("Parser started. Type a command (type 'help' for the list of commands):")

    ir = None
    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue

        cmd = user_input.lower()

        # se il comando inizia con "build" (costruzione indice da file)
        if cmd.startswith("build"):
            parts = cmd.split()
            # controlla che ci siano esattamente 3 parti: 'build', <titles_file>, <descriptions_file>
            if len(parts) != 3:
                print("Usage: build <titles_file> <descriptions_file>")
            else:
                metadata, descriptions = parts[1:]
                ir = build_index(metadata, descriptions)
        # se il comando è esattamente "len index", mostra il numero di termini unici indicizzati
        elif cmd == "len index":
            if ir is None:
                continue
            print(f"Index size (number of unique terms): {ir._index.__len__()}")
        # comando per caricare un indice già costruito da disco
        elif cmd in ["load index"]:
            ir = load_index()
        # mostra il menu di aiuto con i comandi disponibili
        elif cmd == "help":
            help_menu()
        # comando per uscire dal programma, salvando l'indice se caricato
        elif cmd == "exit":
            print("Exiting and saving...")
            if ir is not None:
                ir.write_ir_system_to_disk()
            else:
                print("No index to save.")
            # esce dal ciclo principale e termina il programma
            break
        # se l'indice è caricato
        elif ir is not None:
            # comando per eliminare documenti specifici dall'indice
            if cmd.startswith("del "):
                query = user_input[4:].strip()
                if query:
                    delete_documents(query, ir)
                else:
                    print("You must specify a string after 'del'.")
            # comando per aggiungere un singolo documento (titolo + descrizione)
            elif cmd.startswith("add"):
                parts = user_input.strip().split(maxsplit=1)
                if len(parts) < 2:
                    print("Error: Missing arguments after 'add'.")
                    return
                args = parts[1]
                if '|' in args:
                    try:
                        title, description = map(str.strip, args.split('|', 1))
                        add_document(ir, title, description)
                    except ValueError:
                        print("Error: Use '|' to separate title and description.")
                else:
                    try:
                        title_file, description_file = args.split(maxsplit=1)
                        add_documents(ir, title_file, description_file)
                    except ValueError:
                        print("Error: Provide both title_file and description_file.")
            # se il comando non corrisponde a quelli precedenti, lo interpreta come query di ricerca
            else:
                results = search(cmd, ir)
                if results:
                    for result in results:
                        print(result)
                    print(f"{len(results)} result(s) found.")
                else:
                    print("No results found.")
        else:
            print("Index not loaded.")
            continue

if __name__ == "__main__":
    main()
