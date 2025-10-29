import DB

import math
import os
import re
import shutil
from typing import Callable, Tuple, Iterable

class Helper():
    def __init__(self, db: DB):
        self.db = db
        self.shelf_map = {int : self._format_shelf_id,
                          str : self._format_shelf_label}
        self.part_map = {int : self._format_part_id,
                         str : self._format_part_label}

    def reset_screen(self, heading: str = None):
        print(chr(27) + "[H" + chr(27) + "[J", end="")
        
        print("############################")
        print("##  Paternosterregal CLI  ##")
        print("############################")
        
        if heading is not None:
            # Print heading
            print("\n  " + heading)
            
            # Print heading underline
            print("\u2558", end="")
            for i in range(0, len(remove_color_codes(heading)) + 2):
                print("\u2550", end="")
            print("\u255B")
        else:
            print("")

    def get_integer_places(self, integer: int) -> int:
        if integer == 0:
            return 1
        
        return int(math.log10(integer)) + 1

    def print_selection(self, options: Tuple[Tuple[int, str]]) -> None:
        
        longest = self.get_integer_places(max([option[0] for option in options])) # get number of places of largest number
        
        string = ""
        
        for option in options:
            spacing = longest - self.get_integer_places(option[0])
            string += f" ({option[0]}){' ' * spacing} " + option[1] + "\n"
        print(string, end="")

    def run_selection(self, options: Tuple[Tuple[int, str]], return_on_empty: bool = False) -> int:
        
        numbers = [option[0] for option in options]
        
        while True:

            self.print_selection(options)
            
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
        
    def menu(self, heading: str, options: Tuple[Tuple[str, Callable[[], None]]], pretext: str | None = None, *args):
        self.reset_screen(heading)
        
        if not pretext == None:
            print(pretext + "\n")
        
        # Let user select what to execute
        print("Was möchtest du tun?")
        
        selection = self.run_selection(list(enumerate([option[0] for option in options], start=1)), return_on_empty=True)
        
        if selection is None:
            return 1
        else:
            # Execute it
            return options[selection-1][1](*args)

    def ask_integer(self, question: str = None) -> int:
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

    def ask_confirm(self, question: str = "Bist du dir sicher?", bias: bool = False) -> bool:
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

    def no_results(self, string: str = "Dazu konnte leider nichts gefunden werden :/"):
        input(string + "\n> ")

    def nothing(*_) -> None:
        input("Diese Funktion ist zur Zeit leider noch nicht verfügbar :/")

    def search(self, table: str, column: str, string: str, like: bool = False):
        if like:
            words = string.split()

            conditions = " AND ".join([f"{column} LIKE ?" for _ in words])
            params = [f"%{word}%" for word in words]
            
            return self.db.cursor.execute(f"SELECT * FROM {table} WHERE {conditions} ORDER BY {column} ASC", params).fetchall()
        else:
            return self.db.cursor.execute(f"SELECT * FROM {table} WHERE {column} = ? ORDER BY {column} ASC", [string]).fetchall()
    
    def get_shelves(self, tables: Iterable[str] = ["id", "label"]):
        return self.db.cursor.execute(f"SELECT {', '.join([table for table in tables])} FROM shelves").fetchall()
    
    def copy_and_replace(self, source_path, destination_path):
        if os.path.exists(destination_path):
            os.remove(destination_path)
        shutil.copy2(source_path, destination_path)

    def shelf(self, id_or_label: int | str):
        return color_shelf(self.shelf_map[type(id_or_label)](id_or_label))

    def _format_shelf_label(self, label: str) -> str:
        return f"Regal {label}"

    def _format_shelf_id(self, id: int) -> str:
        label = self.db.cursor.execute("SELECT label FROM shelves WHERE id = ?", [id]).fetchone()[0]
        return self._format_shelf_label(label)

    def compartment(self, id: int, show_shelf: bool = True):
        info = self.db.cursor.execute("""SELECT shelf, position, length FROM compartments WHERE id = ?""", [id]).fetchone()
        if show_shelf:
            return color_compartment(f"Fach #{id}" + " (" + self.shelf(info[0]) + color_compartment(f", {info[1]}-{info[1] + info[2]})"))
        else:
            return color_compartment(f"Fach #{id}" + f" ({info[1]}-{info[1] + info[2]})")

    def part(self, id_or_label: int | str):
        return color_part(self.part_map[type(id_or_label)](id_or_label))

    def _format_part_label(self, label: str):
        return f"Ware \"{label}\""
    
    def _format_part_id(self, id: int):
        info = self.db.cursor.execute("""SELECT label FROM parts WHERE id = ?""", [id]).fetchone()
        return "Ware \"" + color_part(info[0]) + "\""

def color_shelf(string: str = "Regal") -> str:
    return f"\033[91m{string}\033[0m"

def color_compartment(string: str = "Fach") -> str:
    return f"\033[92m{string}\033[0m"

def color_part(string: str = "Ware") -> str:
    return f"\033[96m{string}\033[0m"

def color_part_compartment(string: str = "Fachzuordnung") -> str:
    return f"\033[95m{string}\033[0m"

def remove_color_codes(string: str) -> str:
    return re.sub(r"\033.*?m", "", string)