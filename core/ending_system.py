#!/usr/bin/env python3
"""
Tragedy/Madness Ending System for Call of Cthulhu.
Generates rich non-death endings based on final game state.
"""

from typing import Dict, Optional
from enum import Enum


class EndingType(Enum):
    """Types of possible endings"""
    HOLLOW_VICTORY = "hollow_victory"  # Won but traumatized
    PYRRHIC_VICTORY = "pyrrhic_victory"  # Won with major losses
    BROKEN_SURVIVOR = "broken_survivor"  # Survived but permanently damaged
    KNOWLEDGE_CURSE = "knowledge_curse"  # Survived knowing too much
    ISOLATION = "isolation"  # Survived but alone/separated
    MADNESS = "madness"  # Survived but insane
    TRANSFORMATION = "transformation"  # Survived but fundamentally changed
    TRIUMPH = "triumph"  # Genuine victory despite horrors


class TragedyEndingEngine:
    """Generates tragedy and madness-themed endings"""

    @staticmethod
    def determine_ending_type(
        final_sanity: int,
        companions_alive: int,
        discoveries_count: int,
        breaking_points: int,
        turns_played: int
    ) -> EndingType:
        """Determine which ending type to use based on game state"""

        # Critical sanity → madness
        if final_sanity < 15:
            return EndingType.MADNESS

        # Low sanity + lost companions → broken survivor
        if final_sanity < 30 and companions_alive == 0:
            return EndingType.BROKEN_SURVIVOR

        # Multiple breaking points → knowledge curse
        if breaking_points >= 3:
            return EndingType.KNOWLEDGE_CURSE

        # Lone survivor → isolation
        if final_sanity >= 30 and companions_alive == 0 and turns_played > 20:
            return EndingType.ISOLATION

        # Many discoveries + decent sanity → triumph
        if discoveries_count >= 5 and final_sanity >= 50:
            return EndingType.TRIUMPH

        # Lost companion → pyrrhic victory
        if companions_alive < 1:
            return EndingType.PYRRHIC_VICTORY

        # Default → hollow victory
        return EndingType.HOLLOW_VICTORY

    @staticmethod
    def generate_ending_narrative(
        investigator_name: str,
        ending_type: EndingType,
        final_sanity: int,
        discoveries: list,
        companions_alive: int,
        insanities: list
    ) -> Dict:
        """Generate rich ending narrative based on game state"""

        narratives = {
            EndingType.MADNESS: f"""
The Darkness Consumes

You stand alone in the aftermath, unable to remember what happened. The investigators find you three days later, still screaming about the things you saw. Dr. {investigator_name} is admitted to Arkham Sanitarium, where you spend the rest of your days in a padded room, your mind shattered beyond recovery.

The truth of what lurks beneath the ocean remains with you—a terrible knowledge you can never quite articulate. The doctors assume it's just trauma. They don't understand. YOU understand. And that understanding is a prison far worse than any cell.

Some nights, you hear them. In the walls. In the deep places. They're calling.

ENDING: Complete Insanity
""",

            EndingType.BROKEN_SURVIVOR: f"""
Alone in the Dark

You stumble out of that cursed place, alive but broken. Your companion didn't make it—their final moments haunt your waking hours and invade your dreams. The authorities find your story too incredible to believe.

Years pass. You work menial jobs, speak to no one, trust nothing. The world feels thin—like you could fall through reality at any moment. Every shadow could hide something from those depths. You're alone in a world that cannot comprehend what you've witnessed.

The surviving investigators who would believe you are gone. You're left with only fragments of sanity and the weight of secrets no one would accept.

ENDING: Scarred Survivor
""",

            EndingType.KNOWLEDGE_CURSE: f"""
The Burden of Truth

You survived. That's what they'll say. But survival comes at a cost.

You know too much. The investigation uncovered truths that aren't meant to be known—cosmic horrors that reduce humanity to insignificance. No amount of therapy or time erases this knowledge. You see the world differently now, noticing the thin places where reality breaks down, the signs that something vast and alien watches from the depths.

Some nights you stand on cliffs overlooking the ocean and wonder if jumping would be an act of surrender or transcendence. You attend support group meetings where no one understands. They talk about car accidents and health scares. You've glimpsed infinity and found it utterly indifferent to human suffering.

You're functional. You can work. You can smile. But inside, you're slowly coming to terms with a terrible truth: we're all insignificant.

ENDING: Cursed with Knowledge
""",

            EndingType.ISOLATION: f"""
A Solitary Witness

You made it out. You're alive. You're sane enough to function.

But you're alone. Your companion abandoned you in the final moments, unable to bear what they saw. You don't blame them. Sometimes you envy their escape, even though they fled into darkness and terror. At least they had someone once.

Now, years later, you've learned not to form attachments. Everyone leaves. Everyone breaks. You've tried to tell people what happened, but their eyes glaze over. They don't want to know. So you stopped telling.

You live quietly, work consistently, and try not to think about the ocean. Some weeks you succeed. Other weeks, you find yourself driving toward the coast with no memory of deciding to do so.

You're alive. You're free. You're also utterly alone with a truth you can't share.

ENDING: Solitary Survivor
""",

            EndingType.PYRRHIC_VICTORY: f"""
The Cost of Survival

You stopped the ritual. You prevented something catastrophic. By all objective measures, you won.

But victory tastes like ash.

Your companions are dead. {investigator_name} watches their final moments play back in vivid detail every night. The psychological weight crushes you under an unbearable burden—the knowledge that their deaths purchased your ability to prevent something worse.

You're lauded as a hero by the few who know what happened. But heroes are supposed to feel noble. You just feel hollow.

The nightmares never stop. The guilt metastasizes. You took human lives—good people—to accomplish something that 99% of humanity will never know happened. You saved the world in a way that guarantees you'll never be truly happy again.

ENDING: Pyrrhic Triumph
""",

            EndingType.HOLLOW_VICTORY: f"""
Hollow Triumph

It's over. You won. The threat has been neutralized. You're alive. Relatively sane.

But the victory feels empty.

The people involved are scattered—some dead, some traumatized, some simply unable to process what they experienced. The authorities cover it up with mundane explanations. Society continues, indifferent to the cosmic horrors that lurk just beyond perception.

You tried to tell people. They didn't believe you. Or worse, they did believe you and immediately began psychological evaluation. You've learned to keep quiet, to smile at the right times, to pretend you're normal.

But you're not. You've glimpsed behind the curtain, and now you're stuck in a world of comfortable lies, knowing the truth no one else accepts.

ENDING: Pyrrhic Peace
""",

            EndingType.TRANSFORMATION: f"""
Changed Forever

You survived. You're alive. But you're not the same person who started this investigation.

Something fundamental shifted inside you during the final confrontation. You've glimpsed something cosmic, something that defies human understanding—and you've integrated that knowledge into your worldview. Most people would call that madness. Maybe it is.

But you've also found clarity in the chaos. Life suddenly seems precious and fragile. You understand what truly matters in ways most people never will. The petty concerns of ordinary society seem almost laughable in comparison.

You've changed. Your relationships are different now—people sense something altered about you, something they can't quite articulate. Some are drawn to you. Others instinctively pull away.

You're no longer entirely human. You're something more, and something less. But you're alive, and you're fundamentally, irreversibly transformed.

ENDING: Transcendent Transformation
""",

            EndingType.TRIUMPH: f"""
Against All Odds

You made it. Against impossible odds, you uncovered the truth and stopped something genuinely catastrophic.

Your companions survived. Your sanity, though tested, remains largely intact. The ritual is broken. The entity is contained or banished. The immediate threat has been neutralized.

More importantly, you've proven that human determination, intelligence, and courage can prevail even against cosmic horrors. It's a qualified victory—you know there are larger forces in the universe indifferent to human welfare—but it's genuine.

Life will never be the same. The nightmares will come. The knowledge won't fade. But you have something most people never achieve: proof that you were equal to something truly apocalyptic and won.

You're changed, but not broken. Traumatized, but not destroyed. You've earned the right to rest.

ENDING: Triumph Through Sacrifice
"""
        }

        ending_text = narratives.get(
            ending_type,
            "You survived. What happens next is your story to write."
        )

        return {
            "ending_type": ending_type.value,
            "narrative": ending_text,
            "final_sanity": final_sanity,
            "companions_lost": max(0, 3 - companions_alive),  # Assuming max 3 companions
            "discoveries": len(discoveries),
            "sanity_broken": len(insanities)
        }

    @staticmethod
    def get_epilogue(ending_type: EndingType, years_later: int = 5) -> str:
        """Generate an epilogue showing long-term consequences"""

        epilogues = {
            EndingType.MADNESS: f"""
EPILOGUE — Five Years Later

You're still in the Sanitarium. The doctors have tried everything. Nothing works. You've become something of a curiosity—a patient who experiences vivid, consistent hallucinations about an entire investigation into impossible phenomena.

Some of the newer staff think you're faking it for attention. The older nurses know better. They've seen the terror in your eyes on nights when you wake up screaming.

You don't remember who you were before. That seems like mercy.
""",

            EndingType.BROKEN_SURVIVOR: f"""
EPILOGUE — Five Years Later

You still avoid the ocean. Loud noises trigger panic attacks. You've been hospitalized twice for suicide attempts.

But you're also taking new medication that seems to help. A therapist who specializes in trauma and PTSD has started making a difference. You're not happy, but you're stable.

Sometimes you wonder if your companion would have approved of you surviving when they couldn't. You've decided to honor their memory by living—truly living, not just existing.

It's a slow process. But it's something.
""",

            EndingType.TRIUMPH: f"""
EPILOGUE — Five Years Later

Life has returned to a semblance of normalcy, though "normal" will never mean the same thing it once did.

Your companion is doing well—they still have nightmares, but they're building a life. You've both found strength in knowing you survived something genuinely apocalyptic and won.

You've started writing about your experiences in the form of fiction—a way of processing without revealing the truth. Readers are captivated by the authenticity of the horror. They have no idea how real it all was.

You stand on the edge of the ocean occasionally, no longer with dread but with respect for something larger than yourself.

You're alive. Your companion is alive. The world continues, protected by knowledge of events it will never fully understand.

That's enough.
"""
        }

        return epilogues.get(
            ending_type,
            "Life continued. You adjusted. Time moved forward.\n\nThat's all any of us can do."
        )
