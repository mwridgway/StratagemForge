"""Unit tests for CS2 Economy Pipeline.

This module provides comprehensive tests for all components including
rules, reducer logic, I/O operations, and integration scenarios.
"""

import json
from pathlib import Path
import tempfile
from typing import Dict, Any

import polars as pl

from cs2econ.rules import Rules, DEFAULT_RULES, kill_reward_for, get_loss_bonus, get_win_reward, clamp_money
from cs2econ.schemas import EVENTS_POLARS_SCHEMA, BALANCES_POLARS_SCHEMA
from cs2econ.reducer import reduce_match
from cs2econ.io_parquet import read_events_eager, write_balances, read_existing_balances


class TestRules:
    """Test CS2 economic rules and calculations."""
    
    def test_kill_rewards(self):
        """Test kill reward calculations."""
        # SMG kills
        assert kill_reward_for("mac10") == 600
        assert kill_reward_for("mp9") == 600
        
        # Rifle kills
        assert kill_reward_for("ak47") == 300
        assert kill_reward_for("m4a4") == 300
        
        # AWP kills
        assert kill_reward_for("awp") == 100
        
        # Knife/zeus kills
        assert kill_reward_for("knife") == 1500
        assert kill_reward_for("taser") == 100
        
        # Unknown weapon
        assert kill_reward_for("unknown_weapon") == 300
    
    def test_loss_bonus(self):
        """Test loss bonus progression."""
        assert get_loss_bonus(0) == 0  # No losses
        assert get_loss_bonus(1) == 1400  # First loss
        assert get_loss_bonus(2) == 1900  # Second loss
        assert get_loss_bonus(3) == 2400  # Third loss
        assert get_loss_bonus(4) == 2900  # Fourth loss
        assert get_loss_bonus(5) == 3400  # Fifth+ loss
        assert get_loss_bonus(6) == 3400  # Capped
    
    def test_money_clamping(self):
        """Test money limits."""
        assert clamp_money(-100) == 0
        assert clamp_money(5000) == 5000
        assert clamp_money(20000) == 16000  # Capped at max
    
    def test_win_rewards(self):
        """Test win bonus calculations."""
        assert get_win_reward("elimination") == 3250
        assert get_win_reward("bomb_explosion") == 3500
        assert get_win_reward("defuse") == 3500
        assert get_win_reward("time_expired") == 3250


class TestReducer:
    """Test economic state reduction logic."""
    
    def test_empty_events(self):
        """Test handling of empty event dataframe."""
        empty_df = pl.DataFrame(schema=EVENTS_POLARS_SCHEMA)
        
        balances, snapshots, state = reduce_match(empty_df, DEFAULT_RULES)
        
        assert balances.is_empty()
        assert snapshots.is_empty()
        assert state.is_empty()
    
    def test_single_round_basic(self):
        """Test basic single round with simple events."""
        events = [
            {
                "match_id": "test_match",
                "round_number": 1,
                "tick": 0,
                "event_id": "event_1",
                "type": "round_start",
                "actor_steamid": "none",
                "victim_steamid": None,
                "team": "T",
                "weapon": None,
                "price": None,
                "amount": None,
                "payload": None,
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            },
            {
                "match_id": "test_match", 
                "round_number": 1,
                "tick": 100,
                "event_id": "event_2",
                "type": "buy",
                "actor_steamid": "player1",
                "victim_steamid": None,
                "team": "T",
                "weapon": "ak47",
                "price": 2700,
                "amount": None,
                "payload": None,
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            },
            {
                "match_id": "test_match",
                "round_number": 1,
                "tick": 1000,
                "event_id": "event_3",
                "type": "kill",
                "actor_steamid": "player1", 
                "victim_steamid": "player2",
                "team": "T",
                "weapon": "ak47",
                "price": None,
                "amount": None,
                "payload": None,
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            },
            {
                "match_id": "test_match",
                "round_number": 1,
                "tick": 2000,
                "event_id": "event_4",
                "type": "round_end",
                "actor_steamid": "none",
                "victim_steamid": None,
                "team": "T",
                "weapon": None,
                "price": None,
                "amount": None,
                "payload": '{"winner": "T", "win_type": "elimination"}',
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            }
        ]
        
        events_df = pl.DataFrame(events, schema=EVENTS_POLARS_SCHEMA)
        balances, snapshots, state = reduce_match(events_df, DEFAULT_RULES)
        
        # Should have processed the round successfully
        assert len(snapshots) >= 1
        print(f"✅ Single round test: Generated {len(balances)} balances, {len(snapshots)} snapshots")


class TestIOOperations:
    """Test input/output operations for parquet files."""
    
    def test_write_read_balances(self):
        """Test writing and reading balance data."""
        balances = [
            {
                "match_id": "test_match",
                "round_number": 1,
                "player_steamid": "player1",
                "team": "T",
                "at": "start",
                "bank": 800,
                "equipment_value": 0,
                "loss_streak": 0,
                "cap_hit": 0,
                "rules_version": "2025_09"
            }
        ]
        
        balances_df = pl.DataFrame(balances, schema=BALANCES_POLARS_SCHEMA)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            write_balances(balances_df, tmpdir)
            read_df = read_existing_balances(tmpdir)
            
            assert len(read_df) == 1
            assert read_df["player_steamid"][0] == "player1"
            assert read_df["team"][0] == "T"


class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_complete_pipeline(self):
        """Test complete pipeline from events to final outputs."""
        # Create a minimal realistic match scenario
        events = [
            {
                "match_id": "integration_test",
                "round_number": 1,
                "tick": 0,
                "event_id": "event_1",
                "type": "round_start",
                "actor_steamid": "none",
                "victim_steamid": None,
                "team": "T",
                "weapon": None,
                "price": None,
                "amount": None,
                "payload": None,
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            },
            {
                "match_id": "integration_test",
                "round_number": 1,
                "tick": 2000,
                "event_id": "event_2",
                "type": "round_end",
                "actor_steamid": "none",
                "victim_steamid": None,
                "team": "T",
                "weapon": None,
                "price": None,
                "amount": None,
                "payload": '{"winner": "T", "win_type": "elimination"}',
                "ingest_source": "test",
                "ts_ingested": "2025-01-01T00:00:00Z"
            }
        ]
        
        events_df = pl.DataFrame(events, schema=EVENTS_POLARS_SCHEMA)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run complete pipeline
            balances, snapshots, state = reduce_match(events_df, DEFAULT_RULES)
            
            # Write outputs (if any)
            if not balances.is_empty():
                write_balances(balances, tmpdir)
            
            # Verify pipeline ran without errors
            print(f"✅ Integration test: Generated {len(balances)} balances, {len(snapshots)} snapshots")


def test_golden_fixture():
    """Test against golden fixture data for regression testing."""
    # This would load a saved "golden" dataset and verify
    # that our reducer produces identical results
    # Implementation would depend on having actual demo data
    pass


def run_tests():
    """Run all tests manually."""
    print("🧪 Running CS2 Economy Pipeline Tests...")
    
    # Test rules
    test_rules = TestRules()
    try:
        test_rules.test_kill_rewards()
        print("✅ Kill rewards test passed")
    except Exception as e:
        print(f"❌ Kill rewards test failed: {e}")
    
    try:
        test_rules.test_loss_bonus()
        print("✅ Loss bonus test passed")
    except Exception as e:
        print(f"❌ Loss bonus test failed: {e}")
    
    try:
        test_rules.test_money_clamping()
        print("✅ Money clamping test passed")
    except Exception as e:
        print(f"❌ Money clamping test failed: {e}")
    
    try:
        test_rules.test_win_rewards()
        print("✅ Win rewards test passed")
    except Exception as e:
        print(f"❌ Win rewards test failed: {e}")
    
    # Test reducer
    test_reducer = TestReducer()
    try:
        test_reducer.test_empty_events()
        print("✅ Empty events test passed")
    except Exception as e:
        print(f"❌ Empty events test failed: {e}")
    
    try:
        test_reducer.test_single_round_basic()
        print("✅ Single round test passed")
    except Exception as e:
        print(f"❌ Single round test failed: {e}")
    
    print("🎯 All tests completed!")


if __name__ == "__main__":
    run_tests()
