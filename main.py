from ir_system import IrSystem
from movie_description import *

def add_document(ir: IrSystem):
    print("adding...")
    single_doc = MovieDescription(
        title="The Example Movie",
        description="A fascinating example movie used to test the IR system."
    )
    second_doc = MovieDescription(
        title="The Example Movie",
        description="A fascinating example movie used to test the IR system."
    )

    # Metti il documento in una lista (anche se è solo uno)
    corpus_single = [single_doc, second_doc]

    # Aggiungi il documento singolo all'indice
    ir.add_docs(corpus_single)
    print("added")

def delete_documents(doc_ids: str, ir: IrSystem) -> None:
    ids_to_delete = set()
    
    for part in doc_ids.split(","):
        part = part.strip()
        
        # Handle range (e.g., '10-15')
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    print(f"Error: Invalid range {part} (start > end)")
                    continue
                # Note: range(start, end) goes from start to end-1
                ids_to_delete.update(range(start, end + 1))  # +1 to include end
            except ValueError:
                print(f"Error: Invalid range format '{part}'")
        
        # Handle single number
        else:
            try:
                doc_id = int(part)
                ids_to_delete.add(doc_id)
            except ValueError:
                print(f"Error: Invalid document ID '{part}'")
    
    if not ids_to_delete:
        print("No valid document IDs to delete")
        return
    
    # Convert to sorted list and delete
    ids_list = sorted(ids_to_delete)
    ir.delete_docs(ids_list)
    
    # Print summary
    if len(ids_list) == 1:
        print(f"Deleted document: {ids_list[0]}")
    else:
        # Find consecutive ranges for cleaner output
        ranges = []
        start = ids_list[0]
        prev = start
        
        for doc_id in ids_list[1:]:
            if doc_id != prev + 1:
                ranges.append((start, prev))
                start = doc_id
            prev = doc_id
        ranges.append((start, prev))
        
        # Format output
        range_strings = [f"{s}-{e}" if s != e else str(s) for s, e in ranges]
        print(f"Deleted documents: {', '.join(range_strings)}")

    # Print remaining count
    remaining = len([x for x in ir._invalid_vec if x == 0])
    print(f"Remaining documents: {remaining}")
    print(f"Index size (number of unique terms): {ir._index.__len__()}")



def help_menu():
    print("Available commands:")
    print(" - help")
    print(" - search <query>")
    print(' - search "quoted phrase"')
    print(" - len <query>")
    print(" - del <doc_id(s)> (e.g. 'del 1,3' or 'del 1-5')")
    print(" - add")
    print(" - build index (or bi)")
    print(" - load index (or li)")
    print(" - save index (or si)")
    print(" - number of docs")
    print(" - exit")

def load_index():
    print("wait...")
    corpus = read_movie_description(
        '/Users/gabriele/Desktop/data/movie.metadata.tsv',
        '/Users/gabriele/Desktop/data/plot_summaries.txt'
    )
    ir = IrSystem(corpus)
    try:
        ir.load_index_from_disk()
        print("Index successfully loaded.")
    except Exception as e:
        print(f"Index loading error: {e}")
        answer = input("Index not found. Do you want to create it from scratch? (y/n): ").strip().lower()
        if answer == 'y':
            ir = IrSystem.from_corpus(corpus)
            ir.save_index_to_disk()
            print("Index created from scratch.")
        else:
            print("Exited without creating the index.")
            return None
    return ir

def build_index():
    print("wait...")
    corpus = read_movie_description(
        '/Users/gabriele/Desktop/data/movie.metadata.tsv',
        '/Users/gabriele/Desktop/data/plot_summaries.txt'
    )
    ir = IrSystem.from_corpus(corpus)
    answer = input("Created, do you want to save it to disk? (y/n): ").strip().lower()
    if answer == 'y':
        ir.save_index_to_disk()
        print("saved")
    return ir

def save_index(ir: IrSystem):
    print("wait...")
    ir.save_index_to_disk()
    print("Index saved")

def search(query: str, ir: IrSystem):
    if ir is None:
        print("Index not loaded. Run 'build index' or 'load index' first.")
        return
    print(f"Performing search for: '{query}'")
    if query.startswith('"') and query.endswith('"'):
        phrase = query[1:-1]
        results = ir.phrase_query(phrase)
    else:
        results = ir.query(query)
    return results

def count_results(query: str, ir: IrSystem):
    results = search(query, ir)
    return len(results) if results else 0

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
    print("Parser started. Type a command (type 'help' for the list of commands):")

    ir = None
    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "exit":
            print("Exiting...")
            break

        elif cmd.startswith("search "):
            if ir is None:
                print("Index not loaded.")
                continue
            query = user_input[7:].strip()
            if query:
                results = search(query, ir)
                print(results)
            else:
                print("You must specify a string after 'search'.")

        elif cmd == "len index":
            if ir is None:
                continue
            print(f"Index size (number of unique terms): {ir._index.__len__()}")

        elif cmd.startswith("len "):
            if ir is None:
                print("Index not loaded.")
                continue
            query = user_input[4:].strip()
            if query:
                print(count_results(query, ir))
            else:
                print("You must specify a string after 'len'.")

        elif cmd.startswith("del "):
            if ir is None:
                print("Index not loaded.")
                continue
            query = user_input[4:].strip()
            if query:
                delete_documents(query, ir)
            else:
                print("You must specify a string after 'del'.")

        elif cmd == "add":
            if ir is None:
                print("Index not loaded.")
                continue
            add_document(ir)

        elif cmd in ["build index", "bi"]:
            ir = build_index()

        elif cmd in ["load index", "li"]:
            ir = load_index()

        elif cmd in ["save index", "si"]:
            if ir is None:
                print("Index not loaded.")
                continue
            save_index(ir)

        elif cmd == "help":
            help_menu()

        else:
            print(f"Unknown command: '{user_input}'")

if __name__ == "__main__":
    main()
