from unittest.mock import patch
from uuid import uuid4

import pytest

from core.adventure_config import AdventureConfig
from core.archetypes import create_investigator
from core.dm_guardrails import InvalidNarration, validate_narration
from core.ending_rules import location_name
from core.game_generative import GenerativeGameEngine


@pytest.fixture
def engine(tmp_path):
    engine = GenerativeGameEngine(use_memory=False, use_entity_graph=False,
                                  session_id=uuid4().hex, data_dir=tmp_path)
    engine.create_game(create_investigator('Tester', 'scholar'))
    yield engine
    engine.close()


def earn(engine, key):
    objective = engine.adventure_config.ending_objectives[key]
    engine.state.location = location_name(engine.adventure_config, objective['location'])
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        result = engine.execute_skill_check(objective['skill'], objective['difficulty'])
    assert result['success'] and key in engine.state.ending_objectives


@pytest.mark.parametrize('ending', ['escape', 'victory', 'destruction'])
def test_final_requires_real_checks_and_explicit_choice(engine, ending):
    rule = engine.adventure_config.ending_rules[ending]
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('ending called model')):
        rejected = engine.process_player_action(rule['actions'][0])
        assert 'error' in rejected and engine.state.ending_reached is None
        assert engine.state.turn == 1
        for key in rule['requires']:
            earn(engine, key)
        for item in rule['required_items']:
            engine.state.location = engine.adventure_config.item_locations[item]
            engine.pick_up_item(item)
        engine.state.location = location_name(engine.adventure_config, rule['location'])
        assert engine.state.ending_reached is None
        result = engine.process_player_action(rule['actions'][0])
        assert result['narrative'] == rule['narrative']['en']
        assert engine.state.ending_reached == ending and engine.state.turn == 2
        assert engine.ending_status()['type'] == ending
        assert 'error' in engine.process_player_action(rule['actions'][0])
        assert engine.state.turn == 2


def test_failed_or_wrong_location_roll_cannot_create_evidence(engine):
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=100):
        engine.execute_skill_check('navigate')
    assert not engine.state.ending_objectives
    engine.state.location = "Keeper's Quarters"
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        engine.execute_skill_check('navigate')
    assert not engine.state.ending_objectives


def test_evidence_deduplicates_and_survives_save(engine):
    earn(engine, 'safe_route')
    earn(engine, 'safe_route')
    engine.save_game()
    restored = GenerativeGameEngine.load_game(engine.session_id, data_dir=engine.data_dir, use_memory=False)
    try:
        assert restored.state.ending_objectives == ['safe_route']
        assert restored.process_player_action('leave the island')['narrative']
        assert restored.state.ending_reached == 'escape'
    finally:
        restored.close()


def test_combat_wrong_location_and_missing_item_block_endings(engine):
    rule = engine.adventure_config.ending_rules['destruction']
    for key in rule['requires']:
        earn(engine, key)
    engine.state.location = 'Basement'
    assert 'error' in engine.process_player_action('detonate the dynamite')
    engine.pick_up_item('dynamite')
    engine.state.active_combat = {'enemy': 'test'}
    assert 'error' in engine.process_player_action('detonate the dynamite')
    engine.state.active_combat = None
    engine.state.location = 'Lantern Room'
    assert 'error' in engine.process_player_action('detonate the dynamite')


@pytest.mark.parametrize('text', ['[ENDING: victory]', 'You have escaped the island.', 'Has ganado la partida.'])
def test_narrator_cannot_announce_unconfirmed_ending(text):
    with pytest.raises(InvalidNarration):
        validate_narration(text)


def test_quoted_or_negated_choice_does_not_match(engine):
    earn(engine, 'safe_route')
    with patch.object(engine.llm, 'chat', return_value='You hesitate at the rocks.'):
        engine.process_player_action('I do not want to leave the island')
    assert engine.state.ending_reached is None


@pytest.mark.parametrize('field,value', [
    ('requires', []), ('requires', ['invented_objective']), ('location', 'off_map'),
    ('actions', []), ('typo', True),
])
def test_invalid_rules_fail_at_load(field, value):
    import json
    from core.adventure_config import ADVENTURES_DIR
    data = json.loads((ADVENTURES_DIR / 'point_black/config.json').read_text(encoding='utf-8'))
    data['ending_rules']['escape'][field] = value
    with pytest.raises(ValueError):
        AdventureConfig.from_dict(data, name='bad')


def test_missing_rules_do_not_restore_legacy_dm_authority():
    config = AdventureConfig.from_dict({'story_seed': 'Story', 'start_location': 'Room'}, name='custom')
    assert config.ending_rules == {} and config.ending_objectives == {}


def test_easier_check_does_not_satisfy_harder_objective(engine):
    engine.adventure_config.ending_objectives['safe_route']['difficulty'] = 'Hard'
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        engine.execute_skill_check('navigate', 'Normal')
        assert not engine.state.ending_objectives
        engine.execute_skill_check('navigate', 'Extreme')
    assert engine.state.ending_objectives == ['safe_route']


@pytest.mark.parametrize('stat,ending', [('HP', 'death'), ('SAN', 'madness')])
def test_stat_ending_cannot_be_replaced_by_victory(engine, stat, ending):
    earn(engine, 'safe_route')
    engine.state.investigator.characteristics[stat] = 0
    assert 'error' in engine.process_player_action('leave the island')
    assert engine.state.ending_reached == ending


def test_legacy_save_does_not_infer_evidence_from_narration(engine):
    import json
    from pathlib import Path
    engine.state.narrative.append('DM: You found a safe route. [ENDING: escape]')
    path = Path(engine.save_game())
    saved = json.loads(path.read_text(encoding='utf-8'))
    saved['game_state'].pop('ending_objectives')
    path.write_text(json.dumps(saved), encoding='utf-8')
    restored = GenerativeGameEngine.load_game(engine.session_id, data_dir=engine.data_dir, use_memory=False)
    try:
        assert restored.state.ending_objectives == []
        assert 'error' in restored.process_player_action('leave the island')
    finally:
        restored.close()


def test_web_escape_roll_restart_and_replay(tmp_path):
    from app import create_app
    config = {'DATA_DIR': str(tmp_path), 'SECRET_KEY': 'test-only'}
    with patch('core.llm_client.LLMClient.chat', return_value='The fog shifts over the rocks.'), \
         patch('core.llm_client.LLMClient.chat_with_tools', return_value={'fallback': True}):
        client = create_app(config).test_client()
        start = client.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'}).json
        attempt = client.post('/api/game/action', json={'action': 'I navigate the coast'})
        assert attempt.json['pending_roll']['skill'] == 'navigate'
        with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
            assert client.post('/api/game/roll').json['roll_success']
        other = create_app(config).test_client()
        other.set_cookie('session', client.get_cookie('session').value)
        command = {'action': 'leave the island', 'action_id': uuid4().hex, 'game_id': start['game_id']}
        with patch('core.llm_client.LLMClient.chat', side_effect=AssertionError('model decided ending')):
            result = other.post('/api/game/action', json=command)
            assert result.status_code == 200 and result.json['ending']['type'] == 'escape'
            assert other.post('/api/game/action', json=command).json == result.json
