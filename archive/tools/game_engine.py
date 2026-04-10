#!/usr/bin/env python3
"""
MOTOR DE AVENTURA SOLITARIA - Alone Against the Tide

Ejecuta la aventura paso a paso:
1. Lee entradas del JSON
2. Maneja investigador
3. Ejecuta rolls
4. Navega automáticamente
5. Mantiene historial
"""

import json
import random
from dataclasses import dataclass
from typing import Optional, List, Dict
import re


@dataclass
class Investigator:
    """Datos del investigador"""
    name: str
    skills: Dict[str, int]  # {skill_name: percentile_value}
    characteristics: Dict[str, int]  # {STR, CON, DEX, etc: value}
    sanity: int = 99
    health: int = 10

    def get_skill_value(self, skill_name: str) -> Optional[int]:
        """Obtiene valor de habilidad o característica"""
        # Buscar en skills
        if skill_name in self.skills:
            return self.skills[skill_name]

        # Buscar en características (sin case sensitivity)
        for char_name, value in self.characteristics.items():
            if char_name.upper() == skill_name.upper():
                return value

        return None

    def __repr__(self):
        return f"{self.name} (Sanity: {self.sanity}, Health: {self.health})"


@dataclass
class RollResult:
    """Resultado de un roll"""
    skill: str
    difficulty: str
    target_value: int
    d100_roll: int
    success: bool
    next_entry: int


class GameEngine:
    """Motor principal de la aventura"""

    def __init__(self, entries_file: str = "entries_with_rolls.json"):
        """Carga las entradas de aventura"""
        with open(entries_file, 'r') as f:
            self.entries = json.load(f)

        # Crear índice para acceso rápido
        self.entry_map = {e['number']: e for e in self.entries}

        self.investigator: Optional[Investigator] = None
        self.current_entry_number: int = 1
        self.roll_history: List[RollResult] = []

        print(f"✓ Motor cargado: {len(self.entries)} entradas")

    def set_investigator(self, investigator: Investigator):
        """Define el investigador para la partida"""
        self.investigator = investigator
        print(f"✓ Investigador: {investigator}")

    def get_entry(self, entry_num: int) -> Optional[Dict]:
        """Obtiene una entrada por número"""
        return self.entry_map.get(entry_num)

    def validate_adventure(self) -> Dict:
        """Valida integridad de la aventura"""
        print("\n🔍 VALIDANDO INTEGRIDAD DE LA AVENTURA...")
        print("="*80)

        errors = {
            'missing_entries': [],
            'invalid_destinations': [],
        }

        # Verificar que todos los destinos de rolls existan
        for entry in self.entries:
            for roll in entry.get('rolls', []):
                for dest in [roll['on_success'], roll['on_failure']]:
                    if dest and dest not in self.entry_map:
                        errors['invalid_destinations'].append(
                            f"Entry {entry['number']}: roll apunta a {dest} (NO EXISTE)"
                        )

        # Verificar entradas faltantes
        for i in range(1, 244):
            if i not in self.entry_map:
                errors['missing_entries'].append(i)

        # Mostrar resultados
        if errors['missing_entries']:
            print(f"⚠ Entradas faltantes: {errors['missing_entries']}")
        if errors['invalid_destinations']:
            for error in errors['invalid_destinations']:
                print(f"⚠ {error}")
        else:
            print("✓ Todos los destinos de rolls son válidos")

        if not errors['missing_entries'] and not errors['invalid_destinations']:
            print("\n✅ AVENTURA VALIDADA: Sin errores detectados")

        return errors

    def execute_roll(self, roll_info: Dict) -> RollResult:
        """Ejecuta un roll según las instrucciones"""
        if not self.investigator:
            raise Exception("No hay investigador asignado")

        # 1. Obtener valor de habilidad
        skill_name = roll_info['skill']
        base_value = self.investigator.get_skill_value(skill_name)

        if base_value is None:
            raise ValueError(f"Habilidad '{skill_name}' no encontrada")

        # 2. Aplicar modificador de dificultad
        difficulty = roll_info['difficulty']
        if difficulty == "Hard":
            target_value = base_value // 2
        elif difficulty == "Extreme":
            target_value = base_value // 5
        else:
            target_value = base_value

        # 3. Tirar d100
        d100_result = random.randint(1, 100)

        # 4. Determinar éxito
        success = d100_result <= target_value
        next_entry = roll_info['on_success'] if success else roll_info['on_failure']

        # 5. Crear resultado
        result = RollResult(
            skill=skill_name,
            difficulty=difficulty,
            target_value=target_value,
            d100_roll=d100_result,
            success=success,
            next_entry=next_entry
        )

        # 6. Guardar en historial
        self.roll_history.append(result)

        return result

    def display_entry(self, entry_num: int) -> bool:
        """Muestra una entrada. Retorna False si es THE END"""
        entry = self.get_entry(entry_num)
        if not entry:
            print(f"❌ Entrada {entry_num} no encontrada")
            return False

        self.current_entry_number = entry_num

        # Mostrar entrada
        print(f"\n{'='*80}")
        print(f"ENTRY {entry_num}")
        print(f"{'='*80}")

        if entry['character_name']:
            print(f"\n{entry['character_name']}\n")

        print(entry['text'])
        print()

        # Mostrar opciones
        if entry['choices']:
            print("OPTIONS:")
            print("-"*80)
            for i, choice in enumerate(entry['choices'], 1):
                print(f"{i}. {choice}")
        else:
            print("(No more choices - THE END)")
            return False

        # Verificar si es el final
        if 'THE END' in entry['text'].upper():
            return False

        return True

    def print_statistics(self):
        """Imprime estadísticas de la partida"""
        print("\n" + "="*80)
        print("GAME STATISTICS")
        print("="*80)
        print(f"Rolls executed: {len(self.roll_history)}")

        if self.roll_history:
            successes = sum(1 for r in self.roll_history if r.success)
            pct = 100*successes//len(self.roll_history) if self.roll_history else 0
            print(f"Successes: {successes}/{len(self.roll_history)} ({pct}%)")
            
            print(f"\nRolls by skill:")
            skill_stats = {}
            for r in self.roll_history:
                if r.skill not in skill_stats:
                    skill_stats[r.skill] = {'success': 0, 'fail': 0}
                if r.success:
                    skill_stats[r.skill]['success'] += 1
                else:
                    skill_stats[r.skill]['fail'] += 1

            for skill, stats in sorted(skill_stats.items()):
                total = stats['success'] + stats['fail']
                pct = 100 * stats['success'] // total if total > 0 else 0
                print(f"  {skill}: {stats['success']}/{total} ({pct}%)")


if __name__ == '__main__':
    print("MOTOR DE JUEGO - Alone Against the Tide\n")

    # Crear investigador de prueba
    investigator = Investigator(
        name="Dr. Eleanor Woods",
        skills={
            'Psychology': 65,
            'Appraise': 45,
            'Locksmith': 35,
            'Dodge': 45,
            'Stealth': 40,
            'Listen': 50,
            'Persuade': 45,
            'Charm': 50,
            'Navigate': 45,
        },
        characteristics={
            'STR': 50,
            'CON': 55,
            'DEX': 50,
            'APP': 60,
            'POW': 65,
            'SIZ': 50,
            'INT': 75,
            'EDU': 80,
        }
    )

    # Crear y validar motor
    engine = GameEngine("entries_with_rolls.json")
    engine.set_investigator(investigator)
    engine.validate_adventure()

    print("\n✅ Motor listo para usar")
