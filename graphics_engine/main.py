#!/usr/bin/env python3
"""
Graphics Engine v1 - Standalone Demo
Test the graphics engine with sample data
"""

import sys
from pathlib import Path

from .snapshot import Snapshot, GameStateSnapshot
from .storage import SnapshotStorage


def create_test_snapshots() -> list:
    """Create test snapshots for demonstration"""

    snapshots = []

    # Snapshot 0: Arrival at lighthouse
    snap0 = Snapshot(
        turn_id=0,
        session_id="test_session_001",
        narrative="""You step out of the taxi onto the rocky shore. Point Black Lighthouse
looms before you, its white paint weathered by salt and time. The structure
stands about 80 feet tall, with a small cottage adjacent to its base. Dark
windows stare down like dead eyes. A cold wind whips across the promontory,
carrying the smell of brine and something else... something ancient and wrong.

The fog is starting to roll in from the sea.""",
        decision="arrive at lighthouse",
        state=GameStateSnapshot(
            investigator_name="Dr. Marcus Webb",
            investigator_hp=12,
            investigator_max_hp=12,
            investigator_san=75,
            investigator_max_san=99,
            investigator_luck=55,
            location="Lighthouse Exterior",
            discoveries=[],
            inventory=["flashlight", "notebook", "pencil"],
            turn=0,
            phase="exploring",
        ),
        commands=["examine lighthouse", "approach cottage", "look around", "take shelter"],
        tags=["atmosphere", "arrival"],
        image_seed=12345,
    )
    snapshots.append(snap0)

    # Snapshot 1: Examine entrance
    snap1 = Snapshot(
        turn_id=1,
        session_id="test_session_001",
        narrative="""The lighthouse entrance is a heavy wooden door, reinforced with iron bands.
Strange symbols are carved into the frame—not any writing you recognize, but
something older, more primal. Your fingers trace the worn grooves. Some instinct
tells you these symbols mean danger.

The lock appears old but still functional. A small brass nameplate reads:
'KEEPER: J. MARSH - EST. 1902'

You hear the faint sound of wind through the rafters above, and underneath it,
something else... a low vibration, almost like a moan.""",
        decision="examine entrance",
        state=GameStateSnapshot(
            investigator_name="Dr. Marcus Webb",
            investigator_hp=12,
            investigator_max_hp=12,
            investigator_san=72,  # Lost 3 SAN from symbols
            investigator_max_san=99,
            investigator_luck=55,
            location="Lighthouse Exterior",
            discoveries=["Strange symbols on lighthouse door"],
            inventory=["flashlight", "notebook", "pencil"],
            turn=1,
            phase="investigation",
        ),
        commands=["try to open door", "examine symbols more closely", "go to cottage", "return to car"],
        tags=["discovery", "horror"],
        image_seed=12346,
    )
    snapshots.append(snap1)

    # Snapshot 2: Inside lighthouse
    snap2 = Snapshot(
        turn_id=2,
        session_id="test_session_001",
        narrative="""The door swings open with a groan of ancient hinges. Inside, the lighthouse
is a spiral of darkness, the only light coming from gaps in the exterior walls.

A spiral staircase winds upward into shadow. The walls are covered with more
of those strange symbols, carved deep into the stone. Some are old, their edges
worn smooth by time. Others are recent—you can see fresh dust in the grooves.

On a table by the entrance sits a logbook, its pages yellowed and brittle.
The cover reads 'KEEPER'S LOG - POINT BLACK STATION'.

A terrible smell fills the air: salt, mold, decay... and something else.
Something that makes your stomach turn.""",
        decision="enter lighthouse",
        state=GameStateSnapshot(
            investigator_name="Dr. Marcus Webb",
            investigator_hp=12,
            investigator_max_hp=12,
            investigator_san=65,  # Lost 7 more SAN (atmosphere)
            investigator_max_san=99,
            investigator_luck=55,
            location="Lighthouse Interior",
            discoveries=["Strange symbols cover the walls", "Keeper's Log exists"],
            inventory=["flashlight", "notebook", "pencil"],
            turn=2,
            phase="investigation",
        ),
        commands=["read logbook", "climb stairs", "search room", "check smell"],
        tags=["discovery", "atmosphere", "horror"],
        image_seed=12347,
    )
    snapshots.append(snap2)

    return snapshots


def main():
    """Main demo function"""

    print("\n" + "="*70)
    print("GRAPHICS ENGINE v1 - STANDALONE DEMO")
    print("="*70 + "\n")

    # Create storage
    storage = SnapshotStorage(
        db_path="graphics_engine/data/snapshots.db",
        images_dir="graphics_engine/data/images"
    )

    # Generate test snapshots
    print("📸 Creating test snapshots...")
    snapshots = create_test_snapshots()

    # Save snapshots
    print(f"💾 Saving {len(snapshots)} snapshots to database...\n")
    for snap in snapshots:
        path = storage.save_snapshot(snap)
        print(f"  ✓ Turn {snap.turn_id}: {snap.state.location}")
        print(f"    HP: {snap.state.investigator_hp}/{snap.state.investigator_max_hp} | "
              f"SAN: {snap.state.investigator_san}/{snap.state.investigator_max_san}")
        print(f"    Narrative: {snap.narrative[:50]}...")
        print()

    # List snapshots
    print("\n📚 Retrieving snapshots from database:\n")
    retrieved = storage.list_snapshots("test_session_001")
    print(f"Found {len(retrieved)} snapshots:\n")
    for snap in retrieved:
        print(f"  {snap}")

    # Retrieve specific snapshot
    print("\n\n🎯 Retrieving specific snapshot (turn 1):\n")
    snap = storage.get_snapshot("test_session_001", 1)
    if snap:
        print(f"✓ {snap}")
        print(f"\nNarrative:\n{snap.narrative}\n")
        print(f"Available commands: {snap.commands}")
        print(f"Tags: {snap.tags}")
    else:
        print("✗ Snapshot not found")

    print("\n" + "="*70)
    print("✅ Graphics Engine v1 - Core Data Structures Working")
    print("="*70)
    print("\n📝 Next Steps:")
    print("  1. Image Generator (procedural Perlin noise)")
    print("  2. Retro Display (terminal rendering)")
    print("  3. Interactive Pager (navigation)")
    print("\n")


if __name__ == "__main__":
    main()
