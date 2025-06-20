from ir_system import IrSystem
from movie_description import read_movie_description

def add_document():
    print("adding...")

def delete_document():
    print("deleting...")

def help_menu():
    print("Available commands:")
    for command in command_map:
        print(f" - {command}")
    print('Per effettuare una single query puoi scrivere "search" seguito dalla query')
    print('Per effettuare una phrase query puoi scrivere "search" seguito dalla query tra doppi apici (es: search "speak during meetings")')
    print('Comando "esci" per uscire.')


def load_index():
    print("wait...")
    corpus = read_movie_description(
        '/Users/gabriele/Desktop/data/movie.metadata.tsv',
        '/Users/gabriele/Desktop/data/plot_summaries.txt'
    )
    ir = IrSystem(corpus)  # Inizializzo solo con il corpus
    try:
        ir.load_index_from_disk()
        print("Indice caricato con successo.")
    except Exception as e:
        print(f"Errore caricamento indice: {e}")
        risposta = input("Indice non trovato. Vuoi creare l'indice da zero? (y/n): ").strip().lower()
        if risposta == 'y':
            ir = IrSystem.from_corpus(corpus)
            ir.save_index_to_disk()
            print("Indice creato da zero.")
        else:
            print("Uscita dalla funzione senza creare l'indice.")
            return None
    return ir

def build_index():
    print("wait...")
    corpus = read_movie_description(
        '/Users/gabriele/Desktop/data/movie.metadata.tsv',
        '/Users/gabriele/Desktop/data/plot_summaries.txt'
    )
    ir = IrSystem.from_corpus(corpus)
    return ir

def search(query: str, ir: IrSystem):
    if ir is None:
        print("Indice non caricato. Esegui 'build index' o 'load index' prima.")
        return
    print(f"Eseguo la ricerca per: '{query}'")
    if query.startswith('"') and query.endswith('"'):
        phrase = query[1:-1]
        results = ir.phrase_query(phrase)
    else:
        results = ir.query(query)
    print("Risultati:", results)

# Mappa dei comandi; build_index ritorna ir, gli altri no
command_map = {
    "aiuto": help_menu,
    "add d": add_document,
    "del d": delete_document,
    "load index": load_index,
    "build index": build_index,
    "esci": lambda: print("Uscita..."),
}

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

    by Alessandro, Cristina, Gabriele                                               
    """
    print(ascii_art)

def main():
    print_title()
    print("Parser avviato. Digita un comando (scrivi 'aiuto' per la lista comandi):")

    ir = None  # Stato globale dell'indice

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue

        # Gestione del comando "search ..."
        if user_input.lower().startswith("search "):
            query = user_input[7:].strip()
            if query:
                search(query, ir)
            else:
                print("Devi specificare una stringa dopo 'search'.")
            continue

        command = user_input.lower()
        if command == "load index" or command == "ld":
            ir = load_index()  # aggiorna ir
        elif command == "build index":
                ir = build_index()  # aggiorna ir
        else:
                if ir is None:
                    print("Indice non caricato. Esegui 'build index' o 'load index' prima.")
                    continue
                command_map[command]()  # esegue la funzione senza ritorno

        if command == "esci":
                break
        else:
            print(f"Comando sconosciuto: '{user_input}'")

if __name__ == "__main__":
    main()
