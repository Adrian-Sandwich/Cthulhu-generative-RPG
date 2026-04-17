#!/usr/bin/env python3
"""
Interactive ASCII Scene Viewer
Navigate through all lighthouse scenes
"""

from ascii_scenes import list_scenes, get_scene
import os


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def scene_viewer():
    """Interactive scene viewer"""
    scenes = list(list_scenes().keys())
    current_idx = 0

    while True:
        clear_screen()

        # Show current scene
        scene_key = scenes[current_idx]
        print(get_scene(scene_key))

        # Navigation menu
        print("\n" + "="*80)
        print(f"Scene {current_idx + 1}/{len(scenes)}: {scene_key}")
        print("="*80)
        print("\n  [←/h] Previous  |  [→/l] Next  |  [q] Quit  |  [list] All scenes\n")

        try:
            cmd = input("> ").lower().strip()

            if cmd in ['q', 'quit', 'exit']:
                print("\n👋 Goodbye!\n")
                break
            elif cmd in ['list', 'ls']:
                print("\n📜 Available Scenes:")
                for i, key in enumerate(scenes, 1):
                    marker = "→" if i-1 == current_idx else " "
                    print(f"  {marker} {i:2d}. {key}")
                input("\nPress ENTER to continue...")
            elif cmd in ['←', 'h', 'prev', 'previous']:
                current_idx = (current_idx - 1) % len(scenes)
            elif cmd in ['→', 'l', 'next']:
                current_idx = (current_idx + 1) % len(scenes)
            elif cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(scenes):
                    current_idx = idx
                else:
                    print(f"\n❌ Scene {cmd} not found (1-{len(scenes)})")
                    input("Press ENTER to continue...")
            elif cmd in ['exterior_storm', 'exterior_clear', 'exterior_fog',
                         'exterior_dawn', 'interior_stairs', 'interior_library',
                         'beacon_room', 'keeper_chamber']:
                current_idx = scenes.index(cmd)
            else:
                if cmd:
                    print(f"\n❓ Unknown command: {cmd}")
                input("Press ENTER to continue...")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press ENTER to continue...")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🏮 LIGHTHOUSE ASCII SCENE VIEWER")
    print("="*80)
    print("\nLoading scenes...\n")

    try:
        scene_viewer()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
