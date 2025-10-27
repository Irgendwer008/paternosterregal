import math
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

def format_options(options: List) -> str:
    num_options = len(options)
    longest = get_integer_places(num_options)
    
    string = ""
    
    try:
        options[0][1]
        for option in options:
            spacing = longest - get_integer_places(option[0])
            string += f" ({option[0]}){' ' * spacing} " + option[1] + "\n"
        return string[:-1]
    except:
        for i, option in enumerate(options):
            spacing = longest - get_integer_places(i + 1)
            string += f" ({i + 1}){' ' * spacing} " + option + "\n"
        return string[:-1]
    
def menu(heading: str, options: Tuple[Tuple[str, Callable[[], None]]], args: Any = None) -> None:
        
    num_options = len(options)
    
    longest = get_integer_places(num_options)
    
    while True:
        reset_screen(heading)

        print(format_options([option[0] for option in options]))
        
        response = input("\n> ")
        
        if response is "":
            return

        try:
            selection = int(response) - 1
        except (ValueError, TypeError):
            continue
        
        if not (0 <= selection < num_options):
            continue
        
        if args is None:
            options[selection][1]()
        else:
            options[selection][1](args)
        break

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

def nothing() -> None:
    return

def search(table: str, column: str, string: str, db, like: bool = False):
    if like:
        words = string.split()

        conditions = " AND ".join([f"{column} LIKE ?" for _ in words])
        params = [f"%{word}%" for word in words]
        
        return db.cursor.execute(f"SELECT * FROM {table} WHERE {conditions} ORDER BY {column} ASC", params).fetchall()
    else:
        return db.cursor.execute(f"SELECT * FROM {table} WHERE {column} = ? ORDER BY {column} ASC", [string]).fetchall()