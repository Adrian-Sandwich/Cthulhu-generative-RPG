#!/usr/bin/env python3
"""
MOTOR DE JUEGO UNIVERSAL
Funciona con CUALQUIER aventura extraída (entries_*.json)
Soporta rolls, validación, estadísticas, modo interactivo/automático
"""

import json
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

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

class UniversalGameEngine:
    """Motor que funciona con CUALQUIER aventura extraída"""
    
    def __init__(self, entries_file: str):
        """Carga cualquier archivo entries_*.json"""
        if not Path(entries_file).exists():
            raise FileNotFoundError(f"No encontrado: {entries_file}")
        
        with open(entries_file, 'r') as f:
            raw_entries = json.load(f)
        
        # Soportar formato: lista de entries o dict de entries
        if isinstance(raw_entries, list):
            self.entries = {e['number']: e for e in raw_entries}
        else:
            self.entries = raw_entries
        
        self.total_entries = len(self.entries)
        self.title = Path(entries_file).stem
        
        print(f"✓ Motor cargado: {self.title}")
        print(f"  Entradas: {self.total_entries}")
        print(f"  Rango: {min(self.entries.keys())}-{max(self.entries.keys())}")
    
    def create_game(self, investigator: Investigator, starting_entry: int = 1) -> GameState:
        """Crea nueva partida"""
        if starting_entry not in self.entries:
            raise ValueError(f"Entry {starting_entry} no existe")
        
        return GameState(
            investigator=investigator,
            current_entry=starting_entry
        )
    
    def get_entry(self, entry_num: int) -> Optional[Dict]:
        """Obtiene una entrada"""
        return self.entries.get(entry_num)
    
    def display_entry(self, entry_num: int, full: bool = False) -> str:
        """Muestra una entrada"""
        entry = self.get_entry(entry_num)
        if not entry:
            return f"⚠️ Entry {entry_num} no existe"
        
        output = f"\n{'='*80}\n[ENTRY {entry_num}]\n{'='*80}\n\n"
        
        # Texto
        text = entry.get('text', '')
        if full:
            output += text
        else:
            output += text[:400] + ("..." if len(text) > 400 else "")
        
        output += "\n"
        
        # Choices
        choices = entry.get('choices', [])
        if choices:
            output += f"\n{'-'*80}\nOpciones:\n"
            for i, choice in enumerate(choices[:6], 1):
                output += f"{i}. {choice[:70]}\n"
        
        # Trace numbers
        trace = entry.get('trace_numbers', [])
        if trace:
            output += f"\nDestinos: {trace}\n"
        
        return output
    
    def extract_destinations(self, entry_num: int) -> List[int]:
        """Extrae números de destino de una entrada"""
        entry = self.get_entry(entry_num)
        if not entry:
            return []
        
        destinations = set()
        
        # Patrón: "go to X"
        refs = re.findall(r'go to (\d+)', entry.get('text', ''), re.IGNORECASE)
        destinations.update(int(r) for r in refs)
        
        # Trace numbers
        destinations.update(entry.get('trace_numbers', []))
        
        # Choices con números
        for choice in entry.get('choices', []):
            refs = re.findall(r'(\d+)', choice)
            for ref in refs:
                num = int(ref)
                if 1 <= num <= max(self.entries.keys()):
                    destinations.add(num)
        
        return sorted(list(destinations))
    
    def execute_roll(self, game: GameState, skill: str, difficulty: str, 
                    on_success: int, on_failure: int) -> RollResult:
        """Ejecuta un roll según reglas Call of Cthulhu"""
        
        # Obtener skill value (default 30 si no existe)
        skill_value = game.investigator.skills.get(skill, 30)
        
        # Aplicar dificultad (modificador de porcentaje)
        if difficulty.lower() == 'hard':
            target = skill_value // 2
        elif difficulty.lower() == 'extreme':
            target = skill_value // 5
        else:  # Normal
            target = skill_value
        
        # D100
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
            message=f"{'✓ ÉXITO' if success else '✗ FRACASO'}: {d100} vs {target} ({skill})"
        )
        
        game.roll_history.append(result)
        return result
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valida la aventura"""
        errors = []
        missing_destinations = set()
        
        for entry_num, entry in self.entries.items():
            dests = self.extract_destinations(entry_num)
            for dest in dests:
                if dest not in self.entries:
                    missing_destinations.add(dest)
                    if dest not in missing_destinations:  # Reportar solo una vez
                        errors.append(f"Entry {entry_num} → {dest} (no existe)")
        
        return len(errors) == 0, errors
    
    def play_automatic(self, game: GameState, max_moves: int = 100, verbose: bool = True):
        """Simulación automática"""
        if verbose:
            print(f"\n🤖 SIMULACIÓN: {game.investigator.name} | {max_moves} movimientos\n")
        
        moves = 0
        while moves < max_moves and game.current_entry:
            entry = self.get_entry(game.current_entry)
            if not entry:
                if verbose:
                    print(f"✗ Entry {game.current_entry} no existe")
                break
            
            game.visited_entries.append(game.current_entry)
            if verbose:
                print(f"→ Entry {game.current_entry}")
            
            # Buscar destinos
            dests = self.extract_destinations(game.current_entry)
            
            if dests:
                # Elegir destino aleatorio
                game.current_entry = random.choice(dests)
            else:
                if verbose:
                    print("✓ FIN")
                break
            
            moves += 1
        
        if verbose:
            self._print_stats(game)
    
    def _print_stats(self, game: GameState):
        """Imprime estadísticas"""
        print(f"\n{'='*60}")
        print(f"Investigador: {game.investigator.name}")
        print(f"Entradas visitadas: {len(game.visited_entries)}")
        print(f"Rolls: {len(game.roll_history)}")
        if game.roll_history:
            successes = sum(1 for r in game.roll_history if r.success)
            print(f"Tasa éxito: {successes}/{len(game.roll_history)} ({100*game.success_rate():.0f}%)")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    # Cargar CUALQUIER aventura
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python3 game_universal.py <entries_file.json> [--validate]")
        sys.exit(1)
    
    entries_file = sys.argv[1]
    do_validate = '--validate' in sys.argv
    
    # Crear motor
    engine = UniversalGameEngine(entries_file)
    
    # Validar si se solicita
    if do_validate:
        print("\n🔍 Validando...")
        is_valid, errors = engine.validate()
        if is_valid:
            print("✅ Aventura válida")
        else:
            print(f"⚠️ {len(errors)} problemas encontrados")
            for err in errors[:10]:
                print(f"  - {err}")
            if len(errors) > 10:
                print(f"  ... y {len(errors)-10} más")
    
    # Crear investigador de prueba
    test_inv = Investigator(
        name="Tester",
        skills={'Dodge': 50, 'Library Use': 50},
        characteristics={'STR': 50, 'INT': 75}
    )
    
    # Jugar
    game = engine.create_game(test_inv)
    engine.play_automatic(game, max_moves=15)
