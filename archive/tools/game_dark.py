#!/usr/bin/env python3
"""
MOTOR DE JUEGO - Alone Against the Dark
Basado en el protocolo probado para "Alone Against the Tide"
"""

import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class RollResult:
    skill: str
    target_value: int
    difficulty: str
    d100_roll: int
    success: bool
    next_entry: int
    message: str = ""

@dataclass
class Investigator:
    name: str
    skills: Dict[str, int]
    characteristics: Dict[str, int]

@dataclass
class GameState:
    investigator: Investigator
    current_entry: int
    roll_history: List[RollResult] = field(default_factory=list)
    visited_entries: List[int] = field(default_factory=list)
    
    def success_rate(self) -> float:
        if not self.roll_history:
            return 0.0
        successes = sum(1 for r in self.roll_history if r.success)
        return successes / len(self.roll_history)

class GameEngine:
    def __init__(self, entries_file: str):
        with open(entries_file, 'r') as f:
            raw_entries = json.load(f)
        
        self.entries = {e['number']: e for e in raw_entries}
        self.total_entries = len(self.entries)
        
        print(f"✓ Motor cargado: {self.total_entries} entradas")
        
        # Investigadores por defecto
        self.investigators = self._create_default_investigators()
    
    def _create_default_investigators(self) -> Dict[str, Investigator]:
        """Crea investigadores predefinidos basados en el libro"""
        return {
            'Louis Grunewald': Investigator(
                name='Louis Grunewald',
                skills={
                    'Anthropology': 50,
                    'Library Use': 55,
                    'Psychology': 40,
                    'Dodge': 35,
                    'Occult': 35,
                    'Languages': 45,
                },
                characteristics={
                    'STR': 50, 'CON': 45, 'DEX': 40,
                    'APP': 55, 'POW': 50, 'SIZ': 50, 'INT': 75, 'EDU': 85
                }
            ),
            'Ernest Holt': Investigator(
                name='Ernest Holt',
                skills={
                    'Dodge': 50,
                    'Firearms': 45,
                    'Brawl': 55,
                    'Stealth': 40,
                    'Psychology': 35,
                },
                characteristics={
                    'STR': 75, 'CON': 70, 'DEX': 65,
                    'APP': 60, 'POW': 35, 'SIZ': 70, 'INT': 45, 'EDU': 50
                }
            ),
            'Lydia Lau': Investigator(
                name='Lydia Lau',
                skills={
                    'Library Use': 55,
                    'Psychology': 50,
                    'Persuade': 60,
                    'Dodge': 40,
                    'Journalism': 65,
                },
                characteristics={
                    'STR': 45, 'CON': 50, 'DEX': 55,
                    'APP': 70, 'POW': 60, 'SIZ': 45, 'INT': 70, 'EDU': 65
                }
            ),
            'Lt. Devon Wilson': Investigator(
                name='Lt. Devon Wilson',
                skills={
                    'Firearms': 70,
                    'Dodge': 60,
                    'Brawl': 65,
                    'Navigation': 50,
                    'Psychology': 30,
                },
                characteristics={
                    'STR': 70, 'CON': 75, 'DEX': 60,
                    'APP': 65, 'POW': 40, 'SIZ': 75, 'INT': 50, 'EDU': 55
                }
            ),
        }
    
    def create_game(self, investigator_name: str) -> GameState:
        """Crea nueva partida"""
        if investigator_name not in self.investigators:
            raise ValueError(f"Investigador no encontrado: {investigator_name}")
        
        return GameState(
            investigator=self.investigators[investigator_name],
            current_entry=1
        )
    
    def display_entry(self, entry_num: int) -> Optional[str]:
        """Muestra una entrada"""
        if entry_num not in self.entries:
            return f"⚠️ Entry {entry_num} no existe"
        
        entry = self.entries[entry_num]
        
        output = f"\n{'='*80}\n"
        output += f"[ENTRY {entry_num}]\n"
        output += f"{'='*80}\n\n"
        output += entry['text'][:500] + "...\n" if len(entry['text']) > 500 else entry['text'] + "\n"
        
        if entry['choices']:
            output += f"\n{'-'*80}\nOpciones:\n"
            for i, choice in enumerate(entry['choices'][:5], 1):
                output += f"{i}. {choice[:70]}\n"
        
        return output
    
    def execute_roll(self, game: GameState, skill: str, difficulty: str, 
                    on_success: int, on_failure: int) -> RollResult:
        """Ejecuta un roll"""
        
        # Obtener valor de habilidad
        skill_value = game.investigator.skills.get(skill, 30)
        
        # Aplicar dificultad
        if difficulty.lower() == 'hard':
            target = skill_value // 2
        elif difficulty.lower() == 'extreme':
            target = skill_value // 5
        else:  # Normal
            target = skill_value
        
        # Tirar d100
        d100 = random.randint(1, 100)
        success = d100 <= target
        next_entry = on_success if success else on_failure
        
        result = RollResult(
            skill=skill,
            target_value=target,
            difficulty=difficulty,
            d100_roll=d100,
            success=success,
            next_entry=next_entry,
            message=f"{'✓ ÉXITO' if success else '✗ FRACASO'}: {d100} vs {target}"
        )
        
        game.roll_history.append(result)
        return result
    
    def validate_adventure(self) -> Tuple[bool, List[str]]:
        """Valida la aventura"""
        errors = []
        
        # Verificar que todos los destinos existen
        for entry_num, entry in self.entries.items():
            # Buscar números en choices (patrón "go to X")
            import re
            refs = re.findall(r'go to (\d+)', entry['text'], re.IGNORECASE)
            for ref in refs:
                ref_num = int(ref)
                if ref_num not in self.entries:
                    errors.append(f"Entry {entry_num} referencia a {ref_num} que no existe")
            
            # Trace numbers
            for trace_num in entry.get('trace_numbers', []):
                if trace_num not in self.entries:
                    errors.append(f"Entry {entry_num} tiene trace_number {trace_num} que no existe")
        
        return len(errors) == 0, errors
    
    def play_interactive(self, game: GameState):
        """Modo interactivo"""
        print(f"\n🎮 COMENZANDO PARTIDA: {game.investigator.name}")
        print(f"{'='*80}\n")
        
        while True:
            # Mostrar entrada actual
            display = self.display_entry(game.current_entry)
            if display:
                print(display)
            
            game.visited_entries.append(game.current_entry)
            
            # Menú
            print("\nOpciones:")
            print("1. Siguiente entrada")
            print("2. Ver estadísticas")
            print("3. Salir")
            
            choice = input("\nElige (1-3): ").strip()
            
            if choice == '1':
                next_entry = int(input("Número de entrada: "))
                game.current_entry = next_entry
            elif choice == '2':
                self._print_stats(game)
            elif choice == '3':
                break
    
    def play_automatic(self, game: GameState, max_moves: int = 100):
        """Juego automático (navegación aleatoria)"""
        print(f"\n🤖 SIMULACIÓN AUTOMÁTICA: {game.investigator.name}\n")
        
        moves = 0
        while moves < max_moves:
            entry = self.entries.get(game.current_entry)
            if not entry:
                print(f"✗ Entrada inválida: {game.current_entry}")
                break
            
            game.visited_entries.append(game.current_entry)
            
            print(f"Entry {game.current_entry}: {entry['text'][:50]}...")
            
            # Buscar destinos
            import re
            refs = re.findall(r'go to (\d+)', entry['text'], re.IGNORECASE)
            
            if refs:
                game.current_entry = int(random.choice(refs))
            else:
                print("✓ FIN DE AVENTURA")
                break
            
            moves += 1
        
        self._print_stats(game)
    
    def _print_stats(self, game: GameState):
        """Imprime estadísticas de la partida"""
        print(f"\n{'='*80}")
        print("ESTADÍSTICAS")
        print(f"{'='*80}")
        print(f"Investigador: {game.investigator.name}")
        print(f"Entradas visitadas: {len(game.visited_entries)}")
        print(f"Rolls realizados: {len(game.roll_history)}")
        if game.roll_history:
            success_count = sum(1 for r in game.roll_history if r.success)
            print(f"Tasa de éxito: {success_count}/{len(game.roll_history)} ({100*game.success_rate():.0f}%)")

if __name__ == '__main__':
    # Crear motor
    engine = GameEngine('entries_dark.json')
    
    # Validar aventura
    is_valid, errors = engine.validate_adventure()
    print(f"\n✓ Validación: {'OK' if is_valid else f'{len(errors)} errores'}")
    if errors:
        for error in errors[:5]:
            print(f"  ⚠️ {error}")
        if len(errors) > 5:
            print(f"  ... y {len(errors)-5} más")
    
    # Crear juego
    game = engine.create_game('Louis Grunewald')
    
    # Jugar automáticamente
    engine.play_automatic(game, max_moves=20)
