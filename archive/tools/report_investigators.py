#!/usr/bin/env python3
"""
REPORTE DE INVESTIGADORES
Valida y muestra todos los investigadores extraídos del PDF
"""

import json
from pathlib import Path

def main():
    investigators_file = 'investigators.json'

    if not Path(investigators_file).exists():
        print(f"❌ No encontrado: {investigators_file}")
        return False

    with open(investigators_file, 'r') as f:
        investigators = json.load(f)

    print(f"\n{'='*80}")
    print("REPORTE DE INVESTIGADORES")
    print(f"{'='*80}\n")

    print(f"Total de investigadores: {len(investigators)}\n")

    for inv in investigators:
        name = inv['name']
        chars = inv['characteristics']

        print(f"{'='*80}")
        print(f"{name.upper()} (Orden: {inv['order']})")
        print(f"{'='*80}")

        print(f"\n📋 INFORMACIÓN BÁSICA:")
        print(f"   Edad: {inv['age']}")
        print(f"   Ocupación: {inv['occupation']}")
        print(f"   Residencia: {inv['residence']}")
        print(f"   Descripción: {inv['description']}")
        print(f"   Dinero: ${inv['available_cash']:,}")
        print(f"   Entrada inicial: {inv['starting_entry']}")

        print(f"\n📊 CARACTERÍSTICAS:")
        print(f"   STR:{chars['STR']:3} CON:{chars['CON']:3} SIZ:{chars['SIZ']:3} DEX:{chars['DEX']:3} INT:{chars['INT']:3}")
        print(f"   APP:{chars['APP']:3} POW:{chars['POW']:3} EDU:{chars['EDU']:3}")
        print(f"   SAN:{chars['SAN']:3} Luck:{chars['Luck']:3} HP:{chars['HP']:3} MP:{chars['Magic_Points']:3}")

        print(f"\n⚔️ COMBATE:")
        for skill, value in inv['combat_skills'].items():
            print(f"   {skill}: {value}%")

        db = inv['combat_bonuses']['DB']
        build = inv['combat_bonuses']['Build']
        move = inv['combat_bonuses']['Move']
        print(f"   DB: {db} | Build: {build} | Move: {move}")

        print(f"\n🎯 SKILLS ({len(inv['skills'])} habilidades):")
        for skill, value in sorted(inv['skills'].items()):
            print(f"   {skill}: {value}%")

        print(f"\n👥 RELACIONES:")
        print(f"   {inv['significant_people']}")

        print(f"\n💾 PUNTOS DE SKILL:")
        print(f"   +150 puntos para distribuir como desees\n")

    # Validaciones
    print(f"{'='*80}")
    print("VALIDACIÓN")
    print(f"{'='*80}\n")

    errors = []

    # Verificar que hay 4 investigadores
    if len(investigators) != 4:
        errors.append(f"❌ Se esperaban 4 investigadores, se encontraron {len(investigators)}")
    else:
        print("✅ 4 investigadores cargados correctamente")

    # Verificar que tienen orden 1-4
    orders = [inv['order'] for inv in investigators]
    if sorted(orders) == [1, 2, 3, 4]:
        print("✅ Orden de investigadores correcto (1-4)")
    else:
        errors.append(f"❌ Orden inválido: {orders}")

    # Verificar que todos tienen stats
    for inv in investigators:
        name = inv['name']
        required_fields = ['characteristics', 'combat_skills', 'skills']
        missing = [f for f in required_fields if not inv.get(f)]
        if missing:
            errors.append(f"❌ {name}: campos faltantes {missing}")

    # Verificar que todos tienen entrada inicial
    entries = [inv.get('starting_entry') for inv in investigators]
    if all(e for e in entries):
        print(f"✅ Todas las entradas iniciales definidas: {entries}")
    else:
        errors.append(f"❌ Entradas iniciales incompletas: {entries}")

    # Verificar stats realistas (0-100, excepto HP)
    for inv in investigators:
        name = inv['name']
        for skill, value in inv['skills'].items():
            if not (0 <= value <= 100):
                errors.append(f"❌ {name}: skill {skill} = {value}% (fuera de rango)")
        for skill, value in inv['combat_skills'].items():
            if not (0 <= value <= 100):
                errors.append(f"❌ {name}: combat skill {skill} = {value}% (fuera de rango)")

    if errors:
        print("\n⚠️ ERRORES ENCONTRADOS:")
        for error in errors:
            print(f"   {error}")
    else:
        print("✅ Todos los investigadores tienen datos válidos")

    print(f"\n{'='*80}\n")

    return len(errors) == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
