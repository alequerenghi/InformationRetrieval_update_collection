from ir_system import IrSystem
from movie_description import *


def add_document(ir: IrSystem, metadata: str, description: str):
    print("adding...")
    corpus = read_movie_description(metadata, description)
    ir.add_docs(corpus)


def delete_document(query: str, ir: IrSystem):
    ids = set()
    valid_ranges = []

    for part in query.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start <= end:
                    ids.update(range(start, end + 1))
                    valid_ranges.append((start, end))
                else:
                    print(f"Invalid range (start > end): {part}")
            except ValueError:
                print(f"Invalid range: {part}")
        else:
            try:
                single_id = int(part)
                ids.add(single_id)
            except ValueError:
                print(f"Invalid ID: {part}")

    if ids:
        ir.delete_docs(sorted(ids))
        if len(valid_ranges) == 1 and len(ids) == (valid_ranges[0][1] - valid_ranges[0][0] + 1):
            start, end = valid_ranges[0]
            print(f"Deleted documents: from {start} to {end}")
        else:
            print(f"Deleted documents: {sorted(ids)}")
        number_of_docs(ir)
    else:
        print("No valid ID provided.")


def number_of_docs(ir: IrSystem):
    count = ir._invalid_vec.count(0)
    print(f"Remaining documents: {count}")


def help_menu():
    print("Available commands:")
    print(" - help")
    print(" - search <query>")
    print(' - search "quoted phrase"')
    print(" - len <query>")
    print(" - del <doc_id(s)> (e.g. del 1,3-5)")
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
        answer = input(
            "Index not found. Do you want to create it from scratch? (y/n): ").strip().lower()
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
    answer = input(
        "Created, do you want to save it to disk? (y/n): ").strip().lower()
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
                delete_document(query, ir)
            else:
                print("You must specify a string after 'del'.")

        elif cmd.startswith("add"):
            if ir is None:
                print("Index not loaded.")
            else:
                metadata, description = user_input.split()[1:]
                add_document(ir, metadata, description)

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

        elif cmd == "number of docs":
            if ir is None:
                print("Index not loaded.")
                continue
            number_of_docs(ir)

        else:
            print(f"Unknown command: '{user_input}'")


if __name__ == "__main__":
    main()
