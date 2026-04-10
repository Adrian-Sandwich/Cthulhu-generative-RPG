#!/usr/bin/env python3
"""
QUICK PLAY - Tutorial paso a paso
Guía interactiva para jugar Alone Against the Dark
"""

import os
import json
from core.game_enhanced import EnhancedGameEngine
from core.game_universal import Investigator

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_step(num, title, content):
    """Show a step with clear formatting"""
    clear()
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                         PASO {num}: {title}
╚═══════════════════════════════════════════════════════════════════════════╝

{content}
    """)
    input("Presiona ENTER para continuar...\n")

def main():
    """Step-by-step tutorial"""

    # Paso 1
    show_step(1, "BIENVENIDO", """
    Te presento: ALONE AGAINST THE DARK

    Una aventura de Call of Cthulhu donde investigarás desapariciones
    misteriosas que llevan a descubrir un terrible secreto cósmico.

    Viajarás desde Nueva York hasta los confines helados de la Antártida,
    y enfrentarás horrores más allá de la comprensión humana.
    """)

    # Paso 2
    show_step(2, "SELECCIONAR INVESTIGADOR", """
    Existen 4 investigadores disponibles:

    1. Louis Grunewald - Profesor de lingüística
       (Entrada inicial: 13, Aventura: Tide)

    2. Ernest Holt - Industrial adinerado
       (Entrada inicial: 36, Aventura: Tide)

    3. Lydia Lau - Reportera del New York Sun
       (Entrada inicial: 37, Aventura: Tide)

    4. Devon Wilson - Marinero de la armada
       (Entrada inicial: 554, Aventura: Dark - ¡la más peligrosa!)

    ¿A cuál quieres jugar? (escribe 1, 2, 3, o 4)
    """)

    with open('investigators.json', 'r') as f:
        invs = {inv['name']: inv for inv in json.load(f)}

    names = ['Louis Grunewald', 'Ernest Holt', 'Lydia Lau', 'Devon Wilson']
    choice = input("Tu elección: ").strip()

    if choice not in ['1', '2', '3', '4']:
        print("Opción inválida")
        return

    inv_name = names[int(choice) - 1]
    inv_data = invs[inv_name]
    adventure_name = "Dark" if inv_data['starting_entry'] == 554 else "Tide"

    # Paso 3
    show_step(3, f"CONOCE A {inv_name.upper()}", f"""
    {inv_data['description']}

    Ocupación: {inv_data['occupation']}
    Residencia: {inv_data['residence']}

    ESTADÍSTICAS:
    ├─ STR: {inv_data['characteristics']['STR']:2}  CON: {inv_data['characteristics']['CON']:2}  SIZ: {inv_data['characteristics']['SIZ']:2}
    ├─ DEX: {inv_data['characteristics']['DEX']:2}  INT: {inv_data['characteristics']['INT']:2}  APP: {inv_data['characteristics']['APP']:2}
    ├─ POW: {inv_data['characteristics']['POW']:2}  EDU: {inv_data['characteristics']['EDU']:2}
    ├─ HP: {inv_data['characteristics']['HP']:2}  (Puntos de Vida)
    ├─ SAN: {inv_data['characteristics']['SAN']:2}  (Sanidad - importante!)
    ├─ Luck: {inv_data['characteristics']['Luck']:2}  (Suerte)
    └─ MP: {inv_data['characteristics']['Magic_Points']:2}  (Magic Points)

    Dinero disponible: ${inv_data['available_cash']:,}
    """)

    # Paso 4
    show_step(4, f"AVENTURA: ALONE AGAINST THE {adventure_name.upper()}", f"""
    {inv_name} comenzará en la entrada {inv_data['starting_entry']}.

    La aventura tiene múltiples ramificaciones y decisiones que
    afectarán tu destino.

    El número de entradas en esta aventura es:
    ├─ Tide: 243 entradas (investigación costera)
    └─ Dark: 594 entradas (expedición antártica - ¡más compleja!)

    Tu aventura: {adventure_name}
    """)

    # Paso 5: Load adventure and show entry
    show_step(5, "¡COMIENZA LA AVENTURA!", f"""
    Cargando la aventura...
    Iniciando en entrada {inv_data['starting_entry']}...
    """)

    # Initialize game
    entries_file = 'entries_dark_594_final.json' if adventure_name == 'Dark' else 'entries_with_rolls.json'
    engine = EnhancedGameEngine(entries_file)

    inv = Investigator(
        name=inv_name,
        skills=inv_data['skills'],
        characteristics=inv_data['characteristics']
    )

    engine.create_game(inv, inv_data['starting_entry'])

    # Paso 6: Show first entry
    entry = engine.base_engine.get_entry(engine.game.current_entry)

    clear()
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                         ENTRADA {engine.game.current_entry}
╚═══════════════════════════════════════════════════════════════════════════╝

{entry['text']}

OPCIONES EN JUEGO:
──────────────────────────────────────────────────────────────────────────────
1. Ver Journal      - Historial de eventos registrados
2. Ver Status       - Estadísticas actuales (HP, SAN, etc)
3. Ir a Entrada     - Navegar manualmente a otra entrada
4. Guardar y Salir  - Guardar progreso y cerrar el juego
──────────────────────────────────────────────────────────────────────────────

Este es un juego de navegación por texto donde tus decisiones importan.
Cada entrada tiene opciones que te llevarán a diferentes escenarios.

¡Buena suerte, investigador!
    """)

    input("Presiona ENTER para comenzar el juego real (python3 play.py)...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tutorial interrumpido.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
