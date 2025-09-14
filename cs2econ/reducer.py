"""Economic State Reducer for CS2 Demo Analysis.

This module implements the core deterministic reducer that processes
game events into economic state transitions.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

import polars as pl

from .rules import Rules, DEFAULT_RULES, kill_reward_for, get_loss_bonus, get_win_reward, clamp_money

logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Economic state for a single player."""
    steamid: str
    team: str
    bank: int
    equipment_value: int
    zero_income_next_round: bool = False


@dataclass
class TeamState:
    """Economic state for a team."""
    team: str
    loss_streak: int = 0


@dataclass
class RoundResult:
    """Result of processing a single round."""
    balance_rows: List[Dict[str, Any]]
    snapshot_row: Dict[str, Any]
    new_team_states: Dict[str, TeamState]
    new_player_states: Dict[str, PlayerState]
    event_ids: List[str]


def create_initial_player_state(steamid: str, team: str, rules: Rules = DEFAULT_RULES) -> PlayerState:
    """Create initial player state with starting money.
    
    Args:
        steamid: Player Steam ID
        team: Team ("T" or "CT")
        rules: Rules to use for starting money
        
    Returns:
        Initial player state
    """
    return PlayerState(
        steamid=steamid,
        team=team,
        bank=rules.start_money,
        equipment_value=0,
        zero_income_next_round=False
    )


def create_initial_team_state(team: str) -> TeamState:
    """Create initial team state.
    
    Args:
        team: Team name ("T" or "CT")
        
    Returns:
        Initial team state
    """
    return TeamState(team=team, loss_streak=0)


def reduce_round(
    prev_team_states: Dict[str, TeamState],
    prev_player_states: Dict[str, PlayerState],
    round_df: pl.DataFrame,
    rules: Rules = DEFAULT_RULES
) -> RoundResult:
    """Reduce a single round's events into economic state changes.
    
    Args:
        prev_team_states: Team states from previous round
        prev_player_states: Player states from previous round  
        round_df: DataFrame containing events for this round
        rules: Economic rules to apply
        
    Returns:
        RoundResult with new states and output rows
    """
    if round_df.is_empty():
        logger.warning("Empty round DataFrame")
        return RoundResult([], {}, prev_team_states.copy(), prev_player_states.copy(), [])
    
    # Extract round metadata
    match_id = round_df["match_id"][0]
    round_number = round_df["round_number"][0]
    
    # Get sorted event IDs for lineage
    event_ids = sorted(round_df["event_id"].to_list())
    
    # Initialize working states (copy from previous round)
    team_states = {k: TeamState(team=v.team, loss_streak=v.loss_streak) for k, v in prev_team_states.items()}
    player_states = {k: PlayerState(
        steamid=v.steamid,
        team=v.team,
        bank=v.bank,
        equipment_value=v.equipment_value,
        zero_income_next_round=v.zero_income_next_round
    ) for k, v in prev_player_states.items()}
    
    # Initialize new players if they appear in this round
    for row in round_df.iter_rows(named=True):
        steamid = row["actor_steamid"]
        team = row["team"]
        
        if steamid and steamid not in player_states:
            player_states[steamid] = create_initial_player_state(steamid, team, rules)
        
        if team and team not in team_states:
            team_states[team] = create_initial_team_state(team)
    
    # Track round-specific metrics
    round_metrics = {
        team: {
            "spend_sum": 0,
            "kill_reward_sum": 0,
            "win_reward": 0,
            "loss_bonus": 0,
            "plant_bonus_team": 0,
            "planter_bonus": 0,
            "defuse_bonus": 0,
            "planter_steamid": None,
            "defuser_steamid": None,
            "planted": False,
            "defused": False,
            "winner": None,
            "win_type": None,
        }
        for team in team_states.keys()
    }
    
    # Capture starting balances
    balance_rows = []
    for steamid, state in player_states.items():
        balance_rows.append({
            "match_id": match_id,
            "round_number": round_number,
            "player_steamid": steamid,
            "team": state.team,
            "at": "start",
            "bank": state.bank,
            "equipment_value": state.equipment_value,
            "loss_streak": team_states[state.team].loss_streak,
            "cap_hit": 0,
            "rules_version": rules.version,
        })
    
    # Process events in order
    for row in round_df.iter_rows(named=True):
        _process_event(row, player_states, team_states, round_metrics, rules)
    
    # Apply zero income penalties first
    _apply_zero_income_penalties(player_states, rules)
    
    # Apply end-of-round rewards and bonuses
    _apply_round_end_rewards(player_states, team_states, round_metrics, rules)
    
    # Clamp money to valid ranges and calculate cap hits
    cap_hits = {}
    for steamid, state in player_states.items():
        original_bank = state.bank
        state.bank = clamp_money(state.bank, rules)
        cap_hits[steamid] = max(0, original_bank - state.bank)
    
    # Add ending balances
    for steamid, state in player_states.items():
        balance_rows.append({
            "match_id": match_id,
            "round_number": round_number,
            "player_steamid": steamid,
            "team": state.team,
            "at": "end",
            "bank": state.bank,
            "equipment_value": state.equipment_value,
            "loss_streak": team_states[state.team].loss_streak,
            "cap_hit": cap_hits[steamid],
            "rules_version": rules.version,
        })
    
    # Create team snapshots
    snapshots = {}
    for team, metrics in round_metrics.items():
        team_players = [p for p in player_states.values() if p.team == team]
        
        bank_total_start = sum(balance["bank"] for balance in balance_rows 
                              if balance["team"] == team and balance["at"] == "start")
        equip_total_start = sum(balance["equipment_value"] for balance in balance_rows 
                               if balance["team"] == team and balance["at"] == "start")
        bank_total_end = sum(balance["bank"] for balance in balance_rows 
                            if balance["team"] == team and balance["at"] == "end")
        equip_total_end = sum(balance["equipment_value"] for balance in balance_rows 
                             if balance["team"] == team and balance["at"] == "end")
        
        # Generate checksum
        checksum_input = "".join(event_ids) + rules.version
        checksum = hashlib.sha256(checksum_input.encode()).hexdigest()
        
        snapshots[team] = {
            "match_id": match_id,
            "round_number": round_number,
            "team": team,
            "bank_total_start": bank_total_start,
            "equip_total_start": equip_total_start,
            "spend_sum": metrics["spend_sum"],
            "kill_reward_sum": metrics["kill_reward_sum"],
            "win_reward": metrics["win_reward"],
            "loss_bonus": metrics["loss_bonus"],
            "plant_bonus_team": metrics["plant_bonus_team"],
            "planter_bonus": metrics["planter_bonus"],
            "defuse_bonus": metrics["defuse_bonus"],
            "bank_total_end": bank_total_end,
            "equip_total_end": equip_total_end,
            "inputs_event_ids": event_ids,
            "checksum": checksum,
            "rules_version": rules.version,
        }
    
    # Convert to list for output
    snapshot_rows = list(snapshots.values())
    
    return RoundResult(
        balance_rows=balance_rows,
        snapshot_row=snapshot_rows[0] if snapshot_rows else {},
        new_team_states=team_states,
        new_player_states=player_states,
        event_ids=event_ids
    )


def _process_event(
    event: Dict[str, Any],
    player_states: Dict[str, PlayerState],
    team_states: Dict[str, TeamState],
    round_metrics: Dict[str, Dict[str, Any]],
    rules: Rules
) -> None:
    """Process a single event and update states.
    
    Args:
        event: Event data
        player_states: Current player states (modified in place)
        team_states: Current team states (modified in place)
        round_metrics: Round metrics tracking (modified in place)
        rules: Economic rules
    """
    event_type = event["type"]
    actor_steamid = event["actor_steamid"]
    team = event["team"]
    
    if not actor_steamid or actor_steamid not in player_states:
        return
    
    player = player_states[actor_steamid]
    metrics = round_metrics.get(team, {})
    
    if event_type == "buy":
        _handle_buy_event(event, player, metrics, rules)
    elif event_type == "kill":
        _handle_kill_event(event, player, metrics, rules)
    elif event_type == "plant":
        _handle_plant_event(event, player, metrics, rules)
    elif event_type == "defuse":
        _handle_defuse_event(event, player, metrics, rules)
    elif event_type == "round_end":
        _handle_round_end_event(event, team_states, metrics, rules)
    elif event_type == "death_after_time":
        _handle_death_after_time_event(event, player, metrics, rules)


def _handle_buy_event(
    event: Dict[str, Any],
    player: PlayerState,
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle buy event."""
    price = event.get("price", 0)
    if price and price > 0:
        player.bank = max(0, player.bank - price)
        player.equipment_value += price
        metrics["spend_sum"] += price


def _handle_kill_event(
    event: Dict[str, Any],
    player: PlayerState,
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle kill event."""
    weapon = event.get("weapon", "")
    kill_reward = kill_reward_for(weapon, rules)
    
    if not player.zero_income_next_round:
        player.bank += kill_reward
        metrics["kill_reward_sum"] += kill_reward


def _handle_plant_event(
    event: Dict[str, Any],
    player: PlayerState,
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle bomb plant event."""
    metrics["planted"] = True
    metrics["planter_steamid"] = player.steamid


def _handle_defuse_event(
    event: Dict[str, Any],
    player: PlayerState,
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle bomb defuse event."""
    metrics["defused"] = True
    metrics["defuser_steamid"] = player.steamid


def _handle_round_end_event(
    event: Dict[str, Any],
    team_states: Dict[str, TeamState],
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle round end event."""
    payload = event.get("payload", {})
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {}
    
    winner = payload.get("winner", "")
    win_type = payload.get("win_type", "")
    
    # Update team metrics
    if winner in metrics:
        metrics[winner]["winner"] = winner
        metrics[winner]["win_type"] = win_type
        metrics[winner]["win_reward"] = get_win_reward(win_type, rules)
    
    # Update loss streaks
    for team_name, team_state in team_states.items():
        if team_name == winner:
            team_state.loss_streak = 0
        else:
            team_state.loss_streak += 1


def _handle_death_after_time_event(
    event: Dict[str, Any],
    player: PlayerState,
    metrics: Dict[str, Any],
    rules: Rules
) -> None:
    """Handle death after time event."""
    if not metrics.get("planted", False):
        player.zero_income_next_round = True


def _apply_zero_income_penalties(
    player_states: Dict[str, PlayerState],
    rules: Rules
) -> None:
    """Apply zero income penalties to flagged players."""
    for player in player_states.values():
        if player.zero_income_next_round:
            # Reset equipment value to 0 (they lose equipment)
            player.equipment_value = 0
            # Reset flag
            player.zero_income_next_round = False


def _apply_round_end_rewards(
    player_states: Dict[str, PlayerState],
    team_states: Dict[str, TeamState],
    round_metrics: Dict[str, Dict[str, Any]],
    rules: Rules
) -> None:
    """Apply end-of-round rewards and bonuses."""
    for team_name, metrics in round_metrics.items():
        team_players = [p for p in player_states.values() if p.team == team_name]
        team_state = team_states[team_name]
        
        # Apply win/loss rewards
        if metrics.get("winner") == team_name:
            # Team won - distribute win reward
            win_reward = metrics["win_reward"]
            for player in team_players:
                if not player.zero_income_next_round:
                    player.bank += win_reward
        else:
            # Team lost - apply loss bonus
            loss_bonus = get_loss_bonus(team_state.loss_streak, rules)
            metrics["loss_bonus"] = loss_bonus
            
            for player in team_players:
                if not player.zero_income_next_round:
                    player.bank += loss_bonus
        
        # Apply objective bonuses
        if metrics.get("planted") and metrics.get("planter_steamid"):
            planter = player_states.get(metrics["planter_steamid"])
            if planter and not planter.zero_income_next_round:
                planter.bank += rules.actor_objective_bonus
                metrics["planter_bonus"] = rules.actor_objective_bonus
        
        if metrics.get("defused") and metrics.get("defuser_steamid"):
            defuser = player_states.get(metrics["defuser_steamid"])
            if defuser and not defuser.zero_income_next_round:
                defuser.bank += rules.actor_objective_bonus
                metrics["defuse_bonus"] = rules.actor_objective_bonus
        
        # Apply T plant team bonus on loss
        if (team_name == "T" and 
            metrics.get("planted") and 
            metrics.get("winner") != "T"):
            
            plant_bonus = rules.t_plant_team_bonus_on_loss
            metrics["plant_bonus_team"] = plant_bonus
            
            for player in team_players:
                if not player.zero_income_next_round:
                    player.bank += plant_bonus


def reduce_match(events_df: pl.DataFrame, rules: Rules = DEFAULT_RULES) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Reduce an entire match into economic data.
    
    Args:
        events_df: DataFrame with all events for the match
        rules: Economic rules to apply
        
    Returns:
        Tuple of (balances_df, snapshots_df, state_df)
    """
    if events_df.is_empty():
        from .schemas import create_empty_balance_df, create_empty_snapshot_df, create_empty_state_df
        return create_empty_balance_df(), create_empty_snapshot_df(), create_empty_state_df()
    
    # Group by match and round
    rounds = events_df.group_by(["match_id", "round_number"], maintain_order=True)
    
    # Initialize states
    team_states: Dict[str, TeamState] = {}
    player_states: Dict[str, PlayerState] = {}
    
    all_balance_rows = []
    all_snapshot_rows = []
    all_state_rows = []
    
    # Process rounds in order
    for (match_id, round_number), round_df in rounds:
        logger.debug(f"Processing round {round_number} of match {match_id}")
        
        result = reduce_round(team_states, player_states, round_df, rules)
        
        # Accumulate results
        all_balance_rows.extend(result.balance_rows)
        if result.snapshot_row:
            if isinstance(result.snapshot_row, list):
                all_snapshot_rows.extend(result.snapshot_row)
            else:
                all_snapshot_rows.append(result.snapshot_row)
        
        # Update states for next round
        team_states = result.new_team_states
        player_states = result.new_player_states
        
        # Record state for lineage
        for team_name, team_state in team_states.items():
            all_state_rows.append({
                "match_id": match_id,
                "round_number": round_number,
                "team": team_name,
                "player_steamid": None,
                "loss_streak_after": team_state.loss_streak,
                "zero_income_next_round": None,
            })
        
        for steamid, player_state in player_states.items():
            all_state_rows.append({
                "match_id": match_id,
                "round_number": round_number,
                "team": None,
                "player_steamid": steamid,
                "loss_streak_after": None,
                "zero_income_next_round": player_state.zero_income_next_round,
            })
    
    # Convert to DataFrames
    from .schemas import create_empty_balance_df, create_empty_snapshot_df, create_empty_state_df
    
    balances_df = pl.DataFrame(all_balance_rows) if all_balance_rows else create_empty_balance_df()
    snapshots_df = pl.DataFrame(all_snapshot_rows) if all_snapshot_rows else create_empty_snapshot_df()
    state_df = pl.DataFrame(all_state_rows) if all_state_rows else create_empty_state_df()
    
    logger.info(f"Reduced match to {len(balances_df)} balance records, {len(snapshots_df)} snapshots")
    
    return balances_df, snapshots_df, state_df
