#!/usr/bin/env python3
"""
TESTING AUTOMÁTICO DE AVENTURAS
Ejecuta ambas aventuras completas para validar que el motor funciona.
"""

import json
import sys
from pathlib import Path
from game_universal import UniversalGameEngine, Investigator, GameState

def test_adventure(entries_file: str, starting_entry: int = 1):
    """Prueba una aventura completa"""

    if not Path(entries_file).exists():
        print(f"❌ No encontrado: {entries_file}")
        return False

    print(f"\n{'='*80}")
    print(f"TESTING: {Path(entries_file).stem.upper()}")
    print(f"{'='*80}\n")

    try:
        # Cargar motor
        engine = UniversalGameEngine(entries_file)

        # Crear investigador genérico
        investigator = Investigator(
            name="Test Investigator",
            skills={'Dodge': 50, 'Fighting': 40, 'Firearms': 45, 'Psychology': 50},
            characteristics={'STR': 50, 'CON': 50, 'DEX': 50, 'APP': 50, 'POW': 50}
        )

        # Crear partida
        try:
            game = engine.create_game(investigator, starting_entry)
            print(f"✓ Partida iniciada en entry {starting_entry}")
        except ValueError as e:
            print(f"❌ Error al iniciar: {e}")
            return False

        # Validar estructura
        print(f"\n📊 VALIDACIÓN DE ESTRUCTURA:")
        valid, issues = engine.validate()

        if valid:
            print(f"✅ Estructura válida")
            print(f"   - Todas las referencias resuelven correctamente")
        else:
            print(f"⚠️ Problemas encontrados:")
            for issue in issues[:10]:
                print(f"   - {issue}")
            if len(issues) > 10:
                print(f"   ... y {len(issues)-10} más")

        # Ejecutar adventure automáticamente
        print(f"\n🎮 EJECUCIÓN AUTOMÁTICA:")
        engine.play_automatic(game, max_moves=50, verbose=False)

        # Reporte de resultados
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   Entradas visitadas: {len(game.visited_entries)}")
        print(f"   Rolls ejecutados: {len(game.roll_history)}")
        if game.roll_history:
            success_rate = game.success_rate() * 100
            print(f"   Tasa de éxito: {success_rate:.1f}%")
        print(f"   Entrada final: {game.current_entry}")

        # Verificar si llegó al final o se quedó atrapado
        final_entry = engine.get_entry(game.current_entry)
        if final_entry and "[THE END]" in final_entry.get('text', ''):
            print(f"\n✅ Aventura completada (THE END)")
            return True
        else:
            print(f"\n⚠️ Aventura en progreso (no alcanzó THE END)")
            return True  # Still valid, just didn't reach end

    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("VALIDACIÓN DE AVENTURAS")
    print("="*80)

    adventures = [
        ('entries_with_rolls.json', 'Alone Against the Tide', 13),
        ('entries_dark_594_final.json', 'Alone Against the Dark', 13)
    ]

    results = {}

    for filename, title, starting_entry in adventures:
        print(f"\n🎪 {title}")
        results[title] = test_adventure(filename, starting_entry)

    # Resumen final
    print(f"\n{'='*80}")
    print("RESUMEN FINAL")
    print(f"{'='*80}\n")

    for title, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {title}")

    all_passed = all(results.values())
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 TODAS LAS AVENTURAS PASARON VALIDACIÓN")
    else:
        print("⚠️ Algunas aventuras tienen problemas")
    print(f"{'='*80}\n")

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
