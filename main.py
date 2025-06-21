from ir_system import IrSystem
from movie_description import *


def add_document(ir: IrSystem, title: str, description: str):
    print("adding...")
    ir.add_docs(corpus=MovieDescription(title, description))
    print("added")


def add_documents(ir: IrSystem, metadata_file: str, description_file: str):
    corpus = read_movie_description(metadata_file, description_file)
    ir.add_docs(corpus)


def delete_documents(docs_to_delete: str, ir: IrSystem) -> None:
    ids_to_delete = set()

    for part in docs_to_delete.split():
        part = part

        # Handle range (e.g., '10-15')
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    print(f"Error: Invalid range {part} (start > end)")
                    continue
                # Note: range(start, end) goes from start to end-1
                ids_to_delete.update(range(start, end + 1)
                                     )  # +1 to include end
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
    # corpus = read_movie_description(metadata_file, description_file)
    # ir = IrSystem(corpus)
    try:
        ir = IrSystem.load_index_from_disk("index_files")
        print("Index successfully loaded.")
    except Exception as e:
        print(f"Index loading error: {e}")
        answer = input(
            "Index not found. Do you want to create it from scratch? (y/n): ").strip().lower()
        if answer == 'y':
            ir = IrSystem.from_corpus(corpus)
            print("Index created from scratch.")
        else:
            print("Exited without creating the index.")
            return None
    return ir


def build_index(metadata_file, description_file):
    print("wait...")
    corpus = read_movie_description(metadata_file, description_file)
    ir = IrSystem.from_corpus(corpus)
    return ir


def search(query: str, ir: IrSystem):
    print(f"Performing search for: '{query}'")
    results = []
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

        if cmd.startswith("build"):
            metadat, titles = cmd.split()[1:]
            ir = build_index(metadat, titles)
        elif cmd in ["load index", "li"]:
            ir = load_index()
        elif cmd == "help":
            help_menu()
        elif cmd == "exit":
            print("Exiting...")
            if ir is not None:
                ir.save_index_to_disk()
            break
        elif ir is not None:
            if cmd.startswith("del "):
                query = user_input[4:].strip()
                if query:
                    delete_documents(query, ir)
                else:
                    print("You must specify a string after 'del'.")
            elif cmd.startswith("add"):
                metadata, description = user_input.split()[1:]
                add_document(ir, metadata, description)
            else:
                results = search(cmd, ir)
                for result in results:
                    print(result)
        else:
            print("Index not loaded.")
            continue


if __name__ == "__main__":
    main()
