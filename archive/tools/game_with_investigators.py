#!/usr/bin/env python3
"""
GAME WITH INVESTIGATOR DATA
Carga investigadores reales con sus stats del PDF
"""

import json
import sys
from pathlib import Path
from game_universal import UniversalGameEngine, Investigator, GameState

def load_investigators(investigators_file: str = 'investigators.json'):
    """Carga los 4 investigadores disponibles"""
    if not Path(investigators_file).exists():
        raise FileNotFoundError(f"No encontrado: {investigators_file}")

    with open(investigators_file, 'r') as f:
        data = json.load(f)

    investigators = {}
    for inv_data in data:
        name = inv_data['name']

        # Convertir a objeto Investigator
        inv = Investigator(
            name=name,
            skills=inv_data.get('skills', {}),
            characteristics=inv_data.get('characteristics', {})
        )

        investigators[name] = {
            'object': inv,
            'data': inv_data
        }

    return investigators

def display_investigators(investigators: dict):
    """Muestra lista de investigadores disponibles"""
    print(f"\n{'='*80}")
    print("INVESTIGADORES DISPONIBLES")
    print(f"{'='*80}\n")

    for i, (name, inv_info) in enumerate(investigators.items(), 1):
        data = inv_info['data']
        print(f"{i}. {name}")
        print(f"   Edad: {data['age']} | Ocupación: {data['occupation']}")
        print(f"   SAN: {data['characteristics']['SAN']} | Luck: {data['characteristics']['Luck']}")
        print(f"   Dinero: ${data['available_cash']:,}")
        print()

def select_investigator(investigators: dict):
    """Permite al usuario seleccionar un investigador"""
    display_investigators(investigators)

    while True:
        choice = input("Selecciona investigador (1-4) o nombre: ").strip()

        # Por número
        if choice.isdigit():
            idx = int(choice) - 1
            names = list(investigators.keys())
            if 0 <= idx < len(names):
                return investigators[names[idx]]

        # Por nombre
        for name, inv_info in investigators.items():
            if choice.lower() in name.lower():
                return inv_info

        print("❌ Selección inválida. Intenta de nuevo.")

def display_investigator_sheet(inv_info: dict):
    """Muestra la hoja completa del investigador"""
    data = inv_info['data']

    print(f"\n{'='*80}")
    print(f"{data['name'].upper()}")
    print(f"{'='*80}\n")

    print(f"Ocupación: {data['occupation']}")
    print(f"Residencia: {data['residence']}")
    print(f"Descripción: {data['description']}\n")

    # Características
    print("CARACTERÍSTICAS:")
    chars = data['characteristics']
    print(f"  STR:{chars['STR']:3} CON:{chars['CON']:3} SIZ:{chars['SIZ']:3} DEX:{chars['DEX']:3} INT:{chars['INT']:3}")
    print(f"  APP:{chars['APP']:3} POW:{chars['POW']:3} EDU:{chars['EDU']:3}")
    print(f"  Sanidad: {chars['SAN']} | Luck: {chars['Luck']} | HP: {chars['HP']}")
    print(f"  Magic Points: {chars['Magic_Points']}\n")

    # Combat skills
    if data['combat_skills']:
        print("COMBATE:")
        for skill, value in data['combat_skills'].items():
            print(f"  {skill}: {value}%")
        print()

    # Other skills
    print("SKILLS PRINCIPALES:")
    for skill, value in sorted(data['skills'].items()):
        print(f"  {skill}: {value}%")

    print(f"\nDinero disponible: ${data['available_cash']:,}")
    print(f"Entrada inicial: {data['starting_entry']}")
    print(f"\nNota: Tienes 150 puntos de skill para distribuir como desees.\n")

def show_menu():
    """Muestra el menú principal"""
    print(f"\n{'='*80}")
    print("ALONE AGAINST THE DARK")
    print(f"{'='*80}")
    print("\n1. Jugar 'Alone Against the Tide'")
    print("2. Jugar 'Alone Against the Dark'")
    print("3. Ver investigadores")
    print("4. Salir\n")

def main():
    """Menú principal"""

    # Cargar investigadores
    try:
        investigators = load_investigators()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    while True:
        show_menu()
        choice = input("Selecciona opción: ").strip()

        if choice == '1':
            print("\n🎮 'Alone Against the Tide' - 243 entradas")
            inv_info = select_investigator(investigators)
            display_investigator_sheet(inv_info)
            # Aquí iría la lógica de juego

        elif choice == '2':
            print("\n🎮 'Alone Against the Dark' - 594 entradas")
            inv_info = select_investigator(investigators)
            display_investigator_sheet(inv_info)
            # Aquí iría la lógica de juego

        elif choice == '3':
            display_investigators(investigators)

        elif choice == '4':
            print("\n👋 ¡Hasta luego!\n")
            sys.exit(0)

        else:
            print("❌ Opción inválida")

if __name__ == '__main__':
    main()
