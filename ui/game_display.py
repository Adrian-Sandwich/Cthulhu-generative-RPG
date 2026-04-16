#!/usr/bin/env python3
"""
Unified Game Display Manager
Orchestrates all UI components for the game loop
"""

import sys
from typing import Optional, Callable
from .color_system import get_colors, orange, green, cyan, red, yellow, gray
from .retro_display import (
    RetroDisplay,
    GameStateDisplay,
    NarrativeDisplay,
    InventoryDisplay,
    DialogueDisplay,
    EndingDisplay,
)
from .keeper_thinking import show_keeper_thinking


class GameDisplayManager:
    """Unified display manager for the game"""

    def __init__(self, width: int = 80):
        """
        Initialize display manager.

        Args:
            width: Terminal width
        """
        self.width = width
        self.colors = get_colors()

        # Component instances
        self.base = RetroDisplay(width=width)
        self.game_state = GameStateDisplay(width=width)
        self.narrative = NarrativeDisplay(width=width)
        self.inventory_view = InventoryDisplay(width=width)
        self.dialogue_view = DialogueDisplay(width=width)
        self.ending_view = EndingDisplay(width=width)

    def clear_screen(self) -> None:
        """Clear terminal"""
        self.base.clear()

    def show_game_state(self, engine: 'GenerativeGameEngine') -> None:
        """
        Show current game state with stats.

        Args:
            engine: Game engine instance
        """
        inv = engine.state.investigator
        state = engine.state

        self.base.print_header(f"CHARACTER: {inv.name}", color="orange")

        # Stats in a single line
        hp_max = inv.characteristics.get('max_hp', inv.characteristics['HP'])
        san_max = inv.characteristics.get('max_san', 99)

        stats_line = f"HP: {inv.characteristics['HP']:2d}/{hp_max:2d}  •  " \
                     f"SAN: {inv.characteristics['SAN']:2d}/{san_max:2d}  •  " \
                     f"Turn: {state.turn}"
        print(self.colors.colorize(stats_line, "green"))

        # Stat bars
        print(self.base.print_stat_bar("HP", inv.characteristics['HP'], hp_max, width=15, color="red"))
        print(self.base.print_stat_bar("SAN", inv.characteristics['SAN'], san_max, width=15, color="yellow"))

        # Location and quick info
        self.base.print_divider()
        location = state.location or "Unknown"
        inv_count = len(inv.inventory)
        companions = len(engine.companion_manager.get_active_companions())

        self.base.print_columns([
            f"📍 {location}",
            f"🎒 {inv_count}",
            f"👥 {companions}"
        ], color="cyan")
        self.base.print_divider()

    def show_narrative(self, text: str, speaker: str = "THE KEEPER", thinking: bool = True) -> None:
        """
        Show narrative text with thinking animation.

        Args:
            text: Narrative text
            speaker: Who is speaking
            thinking: Show thinking animation first
        """
        if thinking:
            show_keeper_thinking(preset="action_resolution")

        self.base.print_header(speaker, color="cyan")

        # Wrap and display narrative
        lines = self.narrative._wrap_text(text, self.width - 4)
        for line in lines:
            print(f"  {line}")
        print()

    def show_skill_check_prompt(self, skill: str, difficulty: str) -> None:
        """
        Show skill check prompt.

        Args:
            skill: Skill name
            difficulty: Difficulty level (Normal, Hard, Extreme)
        """
        self.clear_screen()
        self.base.print_header("SKILL CHECK", color="green")

        print(f"  {green(f'Skill: {skill.upper()}', bold=True)}")
        print(f"  {cyan(f'Difficulty: {difficulty.upper()}')}")
        print()
        print(self.colors.colorize("  Press ENTER to roll the dice...", "yellow"))
        print()

    def show_skill_check_result(
        self,
        skill: str,
        rolled: int,
        target: int,
        success: bool,
        consequence: Optional[str] = None
    ) -> None:
        """
        Show skill check result.

        Args:
            skill: Skill name
            rolled: Rolled value
            target: Target value
            success: Whether the check succeeded
            consequence: Optional consequence text
        """
        self.clear_screen()
        self.base.print_header("SKILL CHECK RESULT", color="cyan")

        # Result line
        result_text = "✓ SUCCESS!" if success else "✗ FAILURE!"
        result_color = "green" if success else "red"
        result_line = f"  {self.colors.colorize(result_text, result_color, bold=True)} " \
                      f"(Rolled {rolled}, needed {target})"
        print(result_line)

        if consequence:
            print()
            lines = self.narrative._wrap_text(consequence, self.width - 4)
            for line in lines:
                print(f"  {line}")

        print()

    def show_sanity_check(
        self,
        damage: int,
        reason: str,
        current_san: int,
        max_san: int
    ) -> None:
        """
        Show sanity check result.

        Args:
            damage: Sanity damage taken
            reason: Reason for damage
            current_san: Current sanity
            max_san: Maximum sanity
        """
        self.clear_screen()
        self.base.print_header("SANITY CHECK", color="red")

        print(f"  {reason}")
        print()

        # Sanity bar
        print("  " + self.base.print_stat_bar("SAN", current_san, max_san, width=20, color="yellow"))

        # Damage indicator
        if damage > 0:
            damage_msg = f"  💔 You lose {red(str(damage), bold=True)} sanity points"
            print(damage_msg)

        print()

    def show_inventory(self, items: list) -> None:
        """
        Show inventory screen.

        Args:
            items: List of item dictionaries
        """
        self.clear_screen()
        self.base.print_header("INVENTORY", color="green")

        if not items:
            print(self.colors.colorize("  [Empty]", "gray"))
        else:
            for item in items:
                name = item.get('name', 'Unknown')
                desc = item.get('description', '')
                print(self.colors.colorize(f"  ▸ {name}", "green", bold=True))
                if desc:
                    print(f"    {gray(desc[:60])}")

        print()
        print(self.colors.colorize("  Commands: u <item>  |  d <item>  |  read  to continue", "cyan"))
        print()

    def show_dialogue(
        self,
        npc_name: str,
        npc_role: str,
        dialogue: str,
        reputation: int = 0
    ) -> None:
        """
        Show NPC dialogue.

        Args:
            npc_name: NPC name
            npc_role: NPC role
            dialogue: Dialogue text
            reputation: Reputation level
        """
        self.clear_screen()

        # Show thinking while fetching dialogue
        show_keeper_thinking(preset="npc_dialogue")

        # Reputation indicator
        if reputation > 50:
            rep_text = green(f"[TRUSTED +{reputation}]", bold=True)
        elif reputation > 0:
            rep_text = green(f"[FRIENDLY +{reputation}]", bold=True)
        elif reputation < -50:
            rep_text = red(f"[HOSTILE {reputation}]", bold=True)
        else:
            rep_text = gray("[NEUTRAL]")

        self.base.print_header(f"{npc_name} ({npc_role}) {rep_text}", color="cyan")

        # Dialogue text
        lines = self.narrative._wrap_text(dialogue, self.width - 4)
        for line in lines:
            print(f"  {line}")

        print()

    def show_combat_start(self, enemy_name: str, enemy_desc: str) -> None:
        """
        Show combat start screen.

        Args:
            enemy_name: Enemy name
            enemy_desc: Enemy description
        """
        self.clear_screen()
        self.base.print_header("⚔️  COMBAT INITIATED ⚔️", color="red")

        print(f"  {orange(f'Enemy: {enemy_name}', bold=True)}")
        print()

        lines = self.narrative._wrap_text(enemy_desc, self.width - 4)
        for line in lines:
            print(f"  {line}")

        print()
        print(self.colors.colorize("  Prepare to fight for your life!", "red", bold=True))
        print()

    def show_item_found(self, item_name: str) -> None:
        """
        Show item found message.

        Args:
            item_name: Name of item found
        """
        msg = f"  ✓ You found: {green(item_name, bold=True)}"
        print(msg)

    def show_damage_taken(self, damage: int, source: str) -> None:
        """
        Show damage taken message.

        Args:
            damage: Damage amount
            source: Source of damage
        """
        msg = f"  💔 {red(str(damage), bold=True)} HP damage from {source}!"
        print(msg)

    def show_ending(
        self,
        ending_type: str,
        narrative: str,
        stats: dict
    ) -> None:
        """
        Show game ending.

        Args:
            ending_type: Type of ending
            narrative: Ending narrative
            stats: Final statistics
        """
        self.clear_screen()

        # Title
        self.base.print_centered("◆ GAME OVER ◆", color="orange", bold=True)
        self.base.print_divider(color="orange")

        # Ending type
        self.base.print_centered(
            f"🔮 {ending_type.upper().replace('_', ' ')} 🔮",
            color="orange",
            bold=True
        )
        self.base.print_divider()

        # Narrative
        lines = self.narrative._wrap_text(narrative, self.width - 4)
        for line in lines:
            print(f"  {line}")

        self.base.print_divider()

        # Statistics
        print(self.colors.colorize("FINAL STATISTICS:", "cyan", bold=True))
        for key, value in stats.items():
            print(f"  {key}: {value}")

        self.base.print_divider()
        print()

    def prompt_continue(self, message: str = "Press ENTER to continue...") -> None:
        """
        Show continue prompt.

        Args:
            message: Prompt message
        """
        input(self.colors.colorize(f"\n  {message}", "yellow"))

    def prompt_action(self) -> str:
        """
        Prompt for player action.

        Returns:
            Player input
        """
        return input(self.colors.colorize("\n➜ ", "green", bold=True))

    def show_help(self) -> None:
        """Show help screen"""
        self.clear_screen()
        self.base.print_header("HELP", color="green")

        help_text = """
  COMMANDS:
  • <action>     - Do something (describe what you do)
  • i            - Show inventory
  • s            - Show character stats
  • talk to <npc> - Talk to an NPC
  • use <item>   - Use an item
  • drop <item>  - Drop an item
  • h            - Show this help
  • q            - Quit game

  GAMEPLAY:
  • Make skill checks by trying actions
  • Manage sanity - witnessing horror damages it
  • Collect items and gather clues
  • Talk to NPCs for information
  • Avoid or defeat enemies
        """

        for line in help_text.strip().split('\n'):
            print(line)

        print()
        self.prompt_continue()
