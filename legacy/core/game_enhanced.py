#!/usr/bin/env python3
"""
MOTOR MEJORADO CON SAVE/LOAD Y JOURNAL
Extiende el motor universal con features de persistence
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .game_universal import UniversalGameEngine, Investigator, GameState


class Journal:
    """Sistema de journal para registrar eventos"""

    def __init__(self):
        self.entries: List[Dict] = []

    def log(self, entry_num: int, action: str, details: str = ""):
        """Registra un evento en el journal"""
        self.entries.append({
            'timestamp': datetime.now().isoformat(),
            'entry': entry_num,
            'action': action,
            'details': details
        })

    def add_roll_result(self, entry_num: int, skill: str, difficulty: str, success: bool):
        """Registra un resultado de roll"""
        status = "✓ SUCCESS" if success else "✗ FAILED"
        self.log(entry_num, f"ROLL: {skill} ({difficulty})", status)

    def display(self, limit: int = 20):
        """Muestra los últimos N eventos"""
        recent = self.entries[-limit:]
        print(f"\n📖 JOURNAL ({len(self.entries)} eventos):\n")
        for entry in recent:
            ts = entry['timestamp'].split('T')[1][:5]
            print(f"[{ts}] Entry {entry['entry']}: {entry['action']}")
            if entry['details']:
                print(f"      {entry['details']}")

    def to_dict(self) -> Dict:
        """Convierte a dict para guardar"""
        return {'entries': self.entries}

    @staticmethod
    def from_dict(data: Dict) -> 'Journal':
        """Crea desde dict guardado"""
        journal = Journal()
        journal.entries = data.get('entries', [])
        return journal


class GameSave:
    """Maneja save/load de partidas"""

    def __init__(self, game: GameState, engine: UniversalGameEngine,
                 investigator_name: str, journal: Journal, adventure_name: str):
        self.game = game
        self.engine = engine
        self.investigator_name = investigator_name
        self.journal = journal
        self.adventure_name = adventure_name
        self.timestamp = datetime.now().isoformat()

    def save(self, filename: str = None) -> str:
        """Guarda la partida a disco"""
        if filename is None:
            # Generar nombre automático
            safe_name = self.investigator_name.replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"save_{self.adventure_name}_{safe_name}_{timestamp}.json"

        save_data = {
            'metadata': {
                'timestamp': self.timestamp,
                'adventure': self.adventure_name,
                'investigator': self.investigator_name,
                'current_entry': self.game.current_entry,
                'visited_entries_count': len(self.game.visited_entries),
                'rolls_executed': len(self.game.roll_history)
            },
            'game_state': {
                'current_entry': self.game.current_entry,
                'visited_entries': self.game.visited_entries,
                'investigator': {
                    'name': self.game.investigator.name,
                    'skills': self.game.investigator.skills,
                    'characteristics': self.game.investigator.characteristics
                },
                'roll_history': [
                    {
                        'skill': r.skill,
                        'target': r.target_value,
                        'difficulty': r.difficulty,
                        'roll': r.d100_roll,
                        'success': r.success,
                        'next_entry': r.next_entry,
                        'message': r.message
                    }
                    for r in self.game.roll_history
                ]
            },
            'journal': self.journal.to_dict()
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        return filename

    @staticmethod
    def load(filename: str) -> tuple:
        """Carga una partida desde disco"""
        if not Path(filename).exists():
            raise FileNotFoundError(f"No encontrado: {filename}")

        with open(filename, 'r') as f:
            data = json.load(f)

        # Reconstruir investigador
        inv_data = data['game_state']['investigator']
        investigator = Investigator(
            name=inv_data['name'],
            skills=inv_data['skills'],
            characteristics=inv_data['characteristics']
        )

        # Reconstruir game state
        game = GameState(
            investigator=investigator,
            current_entry=data['game_state']['current_entry'],
            visited_entries=data['game_state']['visited_entries'],
            roll_history=[]
        )

        # Reconstruir journal
        journal = Journal.from_dict(data['journal'])

        metadata = data['metadata']

        return game, journal, metadata


class EnhancedGameEngine:
    """Motor mejorado con features extra"""

    def __init__(self, entries_file: str):
        self.base_engine = UniversalGameEngine(entries_file)
        self.game: Optional[GameState] = None
        self.journal = Journal()
        self.investigator_name: str = ""
        self.adventure_name: str = self.base_engine.title

    def create_game(self, investigator: Investigator, starting_entry: int = 1) -> GameState:
        """Crea nueva partida"""
        self.game = self.base_engine.create_game(investigator, starting_entry)
        self.investigator_name = investigator.name
        self.journal.log(starting_entry, "GAME_START", f"Iniciado como {investigator.name}")
        return self.game

    def move_to_entry(self, entry_num: int) -> str:
        """Se mueve a una entrada y la registra"""
        if self.game is None:
            return "❌ No hay partida activa"

        entry = self.base_engine.get_entry(entry_num)
        if not entry:
            return f"❌ Entry {entry_num} no existe"

        self.game.current_entry = entry_num
        if entry_num not in self.game.visited_entries:
            self.game.visited_entries.append(entry_num)

        self.journal.log(entry_num, "VISIT", entry.get('text', '')[:100])

        return self.base_engine.display_entry(entry_num, full=True)

    def execute_roll(self, skill: str, target: int, difficulty: str = "Normal") -> str:
        """Ejecuta un roll y lo registra en journal"""
        result = self.execute_roll_with_result(skill, target, difficulty)
        return result['message']

    def execute_roll_with_result(self, skill: str, target: int, difficulty: str = "Normal") -> dict:
        """Ejecuta un roll y retorna mensaje + resultado"""
        if self.game is None:
            return {"message": "❌ No hay partida activa", "success": False}

        # Simular roll D100
        import random
        d100_roll = random.randint(1, 100)

        # Aplicar modificador de dificultad
        difficulty_mods = {
            "Normal": 1.0,
            "Hard": 0.5,
            "Extreme": 0.2
        }
        mod = difficulty_mods.get(difficulty, 1.0)
        effective_target = int(target * mod)

        success = d100_roll <= effective_target

        result_msg = f"Roll {d100_roll} vs {skill}({effective_target}) - "
        if success:
            result_msg += f"✓ ÉXITO ({d100_roll}/{effective_target})"
        else:
            result_msg += f"✗ FALLO ({d100_roll}/{effective_target})"

        self.journal.add_roll_result(self.game.current_entry, skill, difficulty, success)

        return {"message": result_msg, "success": success}

    def display_status(self) -> str:
        """Muestra estado actual de la partida"""
        if self.game is None:
            return "❌ No hay partida activa"

        output = f"\n{'='*60}\n"
        output += f"ESTADO: {self.investigator_name}\n"
        output += f"{'='*60}\n"
        output += f"Aventura: {self.adventure_name}\n"
        output += f"Entrada actual: {self.game.current_entry}\n"
        output += f"Entradas visitadas: {len(self.game.visited_entries)}\n"
        output += f"Rolls ejecutados: {len(self.game.roll_history)}\n"

        if self.game.roll_history:
            successes = sum(1 for r in self.game.roll_history if r.success)
            output += f"Tasa de éxito: {successes}/{len(self.game.roll_history)} "
            output += f"({100*successes/len(self.game.roll_history):.0f}%)\n"

        output += f"{'='*60}\n"

        return output

    def save_game(self, filename: str = None) -> str:
        """Guarda la partida actual"""
        if self.game is None:
            return "❌ No hay partida activa"

        save = GameSave(
            self.game,
            self.base_engine,
            self.investigator_name,
            self.journal,
            self.adventure_name
        )

        filename = save.save(filename)
        return f"✓ Partida guardada en {filename}"

    @staticmethod
    def load_game(filename: str) -> 'EnhancedGameEngine':
        """Carga una partida guardada"""
        game, journal, metadata = GameSave.load(filename)

        # Crear motor correspondiente
        adventure = metadata['adventure']
        entries_file = f"entries_{adventure.lower().replace(' ', '_')}.json"
        if not Path(entries_file).exists():
            # Intentar con otros nombres
            if "Tide" in adventure:
                entries_file = "entries_with_rolls.json"
            elif "Dark" in adventure:
                entries_file = "entries_dark_594_final.json"

        engine = EnhancedGameEngine(entries_file)
        engine.game = game
        engine.journal = journal
        engine.investigator_name = metadata['investigator']

        return engine

    def show_journal(self, limit: int = 20):
        """Muestra el journal"""
        self.journal.display(limit)


def main():
    """Demo del motor mejorado"""
    print("\n" + "="*80)
    print("MOTOR MEJORADO - DEMO")
    print("="*80 + "\n")

    # Crear motor
    engine = EnhancedGameEngine('entries_with_rolls.json')

    # Crear investigador
    inv = Investigator(
        name="Test Player",
        skills={'Psychology': 50, 'Dodge': 40},
        characteristics={'SAN': 60, 'Luck': 50}
    )

    # Crear partida
    game = engine.create_game(inv, starting_entry=13)
    print(f"✓ Partida creada")

    # Hacer algunas acciones
    print(engine.display_status())

    # Simular algunos movimientos
    print("\n1. Visitando entry 15...")
    print(engine.move_to_entry(15))

    print("\n2. Ejecutando roll...")
    print(engine.execute_roll("Psychology", 50, "Normal"))

    print("\n3. Visitando entry 20...")
    print(engine.move_to_entry(20))

    print("\n4. Estado final...")
    print(engine.display_status())

    print("\n5. Journal...")
    engine.show_journal()

    print("\n6. Guardando partida...")
    print(engine.save_game())

    print("\n✓ Demo completada\n")


if __name__ == '__main__':
    main()
