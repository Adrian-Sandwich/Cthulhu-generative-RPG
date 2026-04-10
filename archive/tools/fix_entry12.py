import json

# Load current data
with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
    data = json.load(f)

# Find Entry 12
entry12_found = False
for i, entry in enumerate(data['entries']):
    if entry['number'] == 12:
        entry12_found = True
        print(f"Entry 12 (before):")
        print(f"  Text length: {len(entry['text'])}")
        print(f"  Text: {entry['text']}")
        print(f"  Choices: {entry['choices']}")
        
        # The text is too short - it's missing the actual content
        # Let's verify and fix
        break

if not entry12_found:
    print("Entry 12 not found!")
else:
    # We need to re-parse the PDF for Entry 12
    # For now, let's manually add the content
    actual_text = """You settle into a seat with your thin briefcase resting on your lap, noticing that the rest of the passengers are likewise getting comfortable for the short trip across the lake. Glancing around, you catch sight of the ferryman entering the cabin. As you sit patiently and wait for the engine to come to life, you listen to the sounds of idle chatter around you. You look out across the water and notice a thin fog beginning to form over the surface of the water as the temperature drops with the approach of night.

After a few minutes, you hear the engine sputter into action and feel the ferry lurch forward. The conversations around you continue as the ferryman joins you all on deck. You can't help overhearing most of the talk, though it's surprisingly banal. There are almost a dozen passengers on the ferry; most of them are simply looking to spend their money during their weekend in Esbury and to enjoy the various shops and leisure activities the lakeside town has to offer. Many of the passengers seem to come from money, as is common in Esbury.

You notice a strange look from one of the women in the group. She has a full figure and brown hair and eyes. She seems to be looking you over, admiring your features."""

    for entry in data['entries']:
        if entry['number'] == 12:
            entry['text'] = actual_text
            entry['choices'] = [{
                'text': '',
                'destination': 3,
                'type': 'next'
            }]
            print(f"\nEntry 12 (after):")
            print(f"  Text length: {len(entry['text'])}")
            print(f"  Text preview: {entry['text'][:100]}...")
            print(f"  Choices: {entry['choices']}")
            break

# Save
with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n✓ Entry 12 fixed with proper text and routing to Entry 3")
