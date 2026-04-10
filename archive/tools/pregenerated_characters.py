#!/usr/bin/env python3
"""
Pre-generated investigators from "Alone Against the Tide"
"""

from game_engine import Character, Occupation

# Dr. Eleanor Woods - Female Archaeologist
DR_ELEANOR_WOODS = Character(
    name="Dr. Eleanor Woods",
    occupation=Occupation.ARCHAEOLOGIST,
    age=32,
    STR=50,
    CON=55,
    POW=60,
    DEX=65,
    APP=60,
    EDU=75,
    SIZ=45,
    INT=70
)

# Override skills for Eleanor (from "Alone Against the Tide" PDF)
DR_ELEANOR_WOODS.skills = {
    'Accounting': 10,
    'Anthropology': 50,
    'Appraise': 35,
    'Archaeology': 60,
    'Charm': 40,
    'Chemistry': 5,
    'Climb': 55,
    'Cthulhu Mythos': 0,
    'Dodge': 45,
    'Drive Auto': 25,
    'Electrical Repair': 10,
    'Fast Talk': 30,
    'Fighting': 35,
    'Firearms': 30,
    'First Aid': 30,
    'Geology': 45,
    'History': 45,
    'Intimidate': 35,
    'Jump': 30,
    'Law': 10,
    'Listen': 40,
    'Library Use': 55,
    'Locksmith': 25,
    'Medicine': 15,
    'Navigation': 50,
    'Occult': 20,
    'Persuade': 45,
    'Psychology': 35,
    'Sleight of Hand': 15,
    'Spot Hidden': 45,
    'Stealth': 35,
    'Survival': 45,
    'Swim': 30,
    'Throw': 30
}

# Dr. Ellery Woods - Male Archaeologist
DR_ELLERY_WOODS = Character(
    name="Dr. Ellery Woods",
    occupation=Occupation.ARCHAEOLOGIST,
    age=35,
    STR=60,
    CON=50,
    POW=55,
    DEX=60,
    APP=55,
    EDU=80,
    SIZ=55,
    INT=75
)

# Override skills for Ellery (same skills, male version)
DR_ELLERY_WOODS.skills = {
    'Accounting': 10,
    'Anthropology': 50,
    'Appraise': 35,
    'Archaeology': 60,
    'Charm': 35,
    'Chemistry': 5,
    'Climb': 60,
    'Cthulhu Mythos': 0,
    'Dodge': 40,
    'Drive Auto': 30,
    'Electrical Repair': 10,
    'Fast Talk': 25,
    'Fighting': 40,
    'Firearms': 35,
    'First Aid': 25,
    'Geology': 50,
    'History': 50,
    'Intimidate': 40,
    'Jump': 35,
    'Law': 10,
    'Listen': 35,
    'Library Use': 60,
    'Locksmith': 30,
    'Medicine': 10,
    'Navigation': 55,
    'Occult': 20,
    'Persuade': 40,
    'Psychology': 30,
    'Sleight of Hand': 15,
    'Spot Hidden': 50,
    'Stealth': 40,
    'Survival': 50,
    'Swim': 35,
    'Throw': 35
}

# Recalculate derived stats
for char in [DR_ELEANOR_WOODS, DR_ELLERY_WOODS]:
    char._calculate_derived_stats()

PREGENERATED_CHARACTERS = {
    'Eleanor': DR_ELEANOR_WOODS,
    'Ellery': DR_ELLERY_WOODS,
}

if __name__ == '__main__':
    print("=== PRE-GENERATED CHARACTERS ===\n")
    for name, char in PREGENERATED_CHARACTERS.items():
        print(f"{char.name} ({char.occupation.value})")
        print(f"STR:{char.STR} CON:{char.CON} POW:{char.POW} DEX:{char.DEX}")
        print(f"HP:{char.hp} SAN:{char.san} Luck:{char.luck}")
        print()
