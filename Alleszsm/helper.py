import math
import os
import shutil
from typing import Callable, Tuple, Any, List

def reset_screen(heading: str = None):
    print(chr(27) + "[H" + chr(27) + "[J", end="")
    
    print("############################")
    print("##  Paternosterregal CLI  ##")
    print("############################")
    
    if heading is not None:
        # Print heading
        print("\n  " + heading)
        
        # Print heading underline
        print("\u2558", end="")
        for i in range(0, len(heading) + 2):
            print("\u2550", end="")
        print("\u255B")
    else:
        print("")

def get_integer_places(integer: int) -> int:
    if integer == 0:
        return 1
    
    return int(math.log10(integer)) + 1

def print_selection(options: Tuple[Tuple[int, str]]) -> None:
    
    longest = get_integer_places(max([option[0] for option in options])) # get number of places of largest number
    
    string = ""
    
    for option in options:
        spacing = longest - get_integer_places(option[0])
        string += f" ({option[0]}){' ' * spacing} " + option[1] + "\n"
    print(string, end="")

def run_selection(options: Tuple[Tuple[int, str]], return_on_empty: bool = False) -> int:
    
    numbers = [option[0] for option in options]
    
    while True:

        print_selection(options)
        
        response = input("\n> ")
        
        if response == "":
            if return_on_empty:
                return
            else:
                continue

        try:
            selection = int(response)
        except (ValueError, TypeError):
            continue
        
        if selection in numbers:
            return selection
    
def menu(heading: str, options: Tuple[Tuple[str, Callable[[], None]]], pretext: str | None = None, *args):
    reset_screen(heading)
    
    if not pretext == None:
        print(pretext + "\n")
    
    # Let user select what to execute
    selection = run_selection(list(enumerate([option[0] for option in options], start=1)), return_on_empty=True)
    
    if selection is None:
        return
    else:
        # Execute it
        options[selection-1][1](*args)

def ask_integer(question: str = None) -> int:
    while True:
        try:
            if question is None:
                result = int(input("\n> "))
            else:
                result = int(input(f"\n{question}\n> "))
            break
        except ValueError:
            print("")
    
    return result

def ask_confirm(question: str = "Bist du dir sicher?", bias: bool = False) -> bool:
    if bias == False:
        response = input(f"\n{question} [y/N]\n> ")
        
        if response not in ["Y", "y"]:
            return False
        else: 
            return True
    else:
        response = input(f"\n{question} [Y/n]\n> ")
        
        if response not in ["N", "n"]:
            return True
        else:
            return False

def no_results(string: str = "Dazu konnte leider nichts gefunden werden :/"):
    input(string + "\n> ")

def nothing(*_) -> None:
    input("Diese Funktion ist zur Zeit leider noch nicht verfügbar :/")

def search(table: str, column: str, string: str, db, like: bool = False):
    if like:
        words = string.split()

        conditions = " AND ".join([f"{column} LIKE ?" for _ in words])
        params = [f"%{word}%" for word in words]
        
        return db.cursor.execute(f"SELECT * FROM {table} WHERE {conditions} ORDER BY {column} ASC", params).fetchall()
    else:
        return db.cursor.execute(f"SELECT * FROM {table} WHERE {column} = ? ORDER BY {column} ASC", [string]).fetchall()
    
def copy_and_replace(source_path, destination_path):
    if os.path.exists(destination_path):
        os.remove(destination_path)
    shutil.copy2(source_path, destination_path)