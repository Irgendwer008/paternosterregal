import math
from typing import Callable, Tuple, Any

def reset_screen(heading: str = None):
    print(chr(27) + "[H" + chr(27) + "[J", end="")
    
    print("######################################")
    print("##  Paternosterregal Datenbank CLI  ##")
    print("######################################")
    
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

def menu(heading: str, options: Tuple[Tuple[str, Callable[[], None]]], args: Any = None) -> None:
        
    num_options = len(options)
    
    while True:
        reset_screen(heading)

        for i, option in enumerate(options):
            print(f" ({i+1}) " + option[0])
        
        response = input("\n> ")

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

def ask_integer(question: str) -> int:
    while True:
        try:
            result = int(input(f"\n{question}\n> "))
            break
        except ValueError:
            print("")
    
    return result

def ask_confirm(bias: bool = False) -> bool:
    if bias == False:
        response = input(f"\nBist du dir Sicher? [y/N]\n> ")
        
        if response not in ["Y", "y"]:
            return False
        else: 
            return True
    else:
        response = input(f"\nBist du dir Sicher? [Y/n]\n> ")
        
        if response not in ["N", "n"]:
            return True
        else:
            return False

def nothing() -> None:
    return