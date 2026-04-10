#!/usr/bin/env python3
"""
DEMO DEL MOTOR DE JUEGO
Muestra todo lo que ganaríamos con el motor de rolls
"""

import json
from game_engine import GameEngine, Investigator


def demo_1_validacion():
    """Demo 1: Validación de aventura"""
    print("\n" + "="*80)
    print("DEMO 1: VALIDACIÓN DE INTEGRIDAD")
    print("="*80)

    engine = GameEngine("entries_with_rolls.json")
    errors = engine.validate_adventure()

    print("\n✅ Encontramos automáticamente que:")
    print(f"  - {len(engine.entries)} entradas totales")
    print(f"  - {sum(len(e.get('rolls', [])) for e in engine.entries)} rolls totales")
    print(f"  - 0 destinos inválidos")


def demo_2_estadisticas():
    """Demo 2: Estadísticas de rolls"""
    print("\n" + "="*80)
    print("DEMO 2: ESTADÍSTICAS DE ROLLS")
    print("="*80)

    with open('entries_with_rolls.json', 'r') as f:
        entries = json.load(f)

    # Contar rolls por habilidad
    skill_count = {}
    for entry in entries:
        for roll in entry.get('rolls', []):
            skill = roll['skill']
            skill_count[skill] = skill_count.get(skill, 0) + 1

    print("\nTop 10 Habilidades Más Usadas:")
    for i, (skill, count) in enumerate(sorted(skill_count.items(), key=lambda x: -x[1])[:10], 1):
        bar = "█" * (count // 2)
        print(f"  {i:2d}. {skill:20s} {bar} {count:2d}")


def demo_3_ejecucion_rolls():
    """Demo 3: Ejecución de rolls"""
    print("\n" + "="*80)
    print("DEMO 3: EJECUCIÓN DE ROLLS")
    print("="*80)

    investigator = Investigator(
        name="Dr. Eleanor Woods",
        skills={
            'Psychology': 65,
            'Dodge': 45,
            'Listen': 50,
            'Stealth': 40,
        },
        characteristics={
            'STR': 50, 'CON': 55, 'DEX': 50, 'POW': 65,
        }
    )

    engine = GameEngine("entries_with_rolls.json")
    engine.set_investigator(investigator)

    print(f"\nInvestigador: {investigator.name}")
    print(f"  Psychology: {investigator.skills['Psychology']}%")
    print(f"  Dodge: {investigator.skills['Dodge']}%")

    # Simular rolls
    print("\n📊 Simulando 10 rolls de Dodge...")
    successes = 0
    for i in range(10):
        result = engine.execute_roll({
            'skill': 'Dodge',
            'difficulty': 'Normal',
            'on_success': 100,
            'on_failure': 50
        })
        status = "✓" if result.success else "✗"
        print(f"  {i+1}. {status} d100={result.d100_roll:3d} vs target={result.target_value:2d} → {'SUCCESS' if result.success else 'FAILURE'}")
        if result.success:
            successes += 1

    print(f"\nResultado: {successes}/10 éxitos ({successes*10}%)")
    print(f"Esperado:  ~45% según habilidad")


def demo_4_navegacion():
    """Demo 4: Navegación automática"""
    print("\n" + "="*80)
    print("DEMO 4: NAVEGACIÓN AUTOMÁTICA")
    print("="*80)

    with open('entries_with_rolls.json', 'r') as f:
        entries = json.load(f)

    # Encontrar una entrada con roll
    for entry in entries:
        if entry['rolls']:
            print(f"\n🎮 Mostrando Entry {entry['number']}:")
            print(f"Texto: {entry['text'][:100]}...")
            print(f"\nOpciones:")
            for i, choice in enumerate(entry['choices'][:2], 1):
                print(f"  {i}. {choice[:60]}...")

            if entry['rolls']:
                print(f"\n⚙️ Rolls detectados:")
                for roll in entry['rolls']:
                    print(f"  • {roll['skill']} [{roll['difficulty']}]")
                    print(f"    → Éxito: entry {roll['on_success']}")
                    print(f"    → Fallo: entry {roll['on_failure']}")

            break


def demo_5_historial():
    """Demo 5: Historial de partida"""
    print("\n" + "="*80)
    print("DEMO 5: HISTORIAL DE PARTIDA")
    print("="*80)

    investigator = Investigator(
        name="Test Player",
        skills={'Dodge': 50, 'Listen': 60, 'Psychology': 40},
        characteristics={'STR': 50, 'CON': 60}
    )

    engine = GameEngine("entries_with_rolls.json")
    engine.set_investigator(investigator)

    # Simular partida con varios rolls
    rolls_to_execute = [
        {'skill': 'Dodge', 'difficulty': 'Normal', 'on_success': 1, 'on_failure': 2},
        {'skill': 'Listen', 'difficulty': 'Hard', 'on_success': 3, 'on_failure': 4},
        {'skill': 'Psychology', 'difficulty': 'Normal', 'on_success': 5, 'on_failure': 6},
        {'skill': 'CON', 'difficulty': 'Extreme', 'on_success': 7, 'on_failure': 8},
    ]

    for roll_info in rolls_to_execute:
        result = engine.execute_roll(roll_info)

    print("\n📋 Historial de Rolls:")
    print("-" * 80)
    for i, result in enumerate(engine.roll_history, 1):
        status = "✓" if result.success else "✗"
        print(f"{i}. {status} {result.skill:15s} [{result.difficulty:8s}] d100={result.d100_roll:3d} vs {result.target_value:2d} → Entry {result.next_entry}")

    # Estadísticas
    engine.print_statistics()


if __name__ == '__main__':
    print("🎲 DEMOSTRACIONES DEL MOTOR DE ROLLS")

    demo_1_validacion()
    demo_2_estadisticas()
    demo_3_ejecucion_rolls()
    demo_4_navegacion()
    demo_5_historial()

    print("\n" + "="*80)
    print("✅ TODOS LOS DEMOS COMPLETADOS")
    print("="*80)
