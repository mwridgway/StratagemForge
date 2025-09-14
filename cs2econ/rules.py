"""CS2 Economy Rules and Constants.

This module defines the economic rules for CS2, including money caps,
kill rewards, win rewards, and loss bonus calculations.
"""

from dataclasses import dataclass
from typing import Dict, Final


@dataclass(frozen=True)
class Rules:
    """CS2 Economy Rules.
    
    All monetary values and game economic constants for deterministic
    economy calculations.
    """
    
    # Money constraints
    money_cap: int = 16000
    start_money: int = 800
    
    # Kill rewards by weapon category
    knife_reward: int = 1500
    smg_default_reward: int = 600
    p90_reward: int = 300
    shotgun_default_reward: int = 900
    xm1014_reward: int = 600
    rifle_reward: int = 300
    pistol_reward: int = 300
    grenade_reward: int = 300
    awp_reward: int = 100
    zeus_reward: int = 100
    
    # Win rewards by condition
    elimination_reward: int = 3250
    t_bomb_explosion_reward: int = 3500
    ct_defuse_reward: int = 3500
    ct_time_expired_no_plant_reward: int = 3250
    
    # Loss bonus progression (indexed by loss streak - 1)
    loss_bonus_ladder: tuple[int, ...] = (1400, 1900, 2400, 2900, 3400)
    
    # Objective bonuses
    t_plant_team_bonus_on_loss: int = 800
    actor_objective_bonus: int = 300  # for planter/defuser
    
    # Special conditions
    zero_income_condition: str = "t_dies_after_time_no_plant"
    
    # Version for lineage tracking
    version: str = "2025_09"


# Weapon categorization mappings
KNIFE_WEAPONS: Final[set[str]] = {
    "knife", "knife_t", "knife_ct", "bayonet", "knife_karambit", 
    "knife_m9_bayonet", "knife_flip", "knife_gut", "knife_falchion",
    "knife_bowie", "knife_butterfly", "knife_push", "knife_cord",
    "knife_canis", "knife_ursus", "knife_gypsy_jackknife", "knife_outdoor",
    "knife_stiletto", "knife_widowmaker", "knife_css", "knife_skeleton"
}

SMG_WEAPONS: Final[set[str]] = {
    "mac10", "mp7", "mp5sd", "mp9", "bizon", "ump45"
}

SHOTGUN_WEAPONS: Final[set[str]] = {
    "nova", "mag7", "sawedoff"
}

RIFLE_WEAPONS: Final[set[str]] = {
    "ak47", "m4a1", "m4a1_silencer", "famas", "galil", "aug", "sg556", "scar20", "g3sg1"
}

PISTOL_WEAPONS: Final[set[str]] = {
    "glock", "usp_silencer", "p2000", "p250", "fiveseven", "tec9", "cz75a", 
    "deagle", "revolver", "elite", "hkp2000"
}

GRENADE_WEAPONS: Final[set[str]] = {
    "hegrenade", "flashbang", "smokegrenade", "incgrenade", "molotov", "decoy"
}

# Default rules instance
DEFAULT_RULES: Final[Rules] = Rules()


def kill_reward_for(weapon_name: str, rules: Rules = DEFAULT_RULES) -> int:
    """Get kill reward for a weapon.
    
    Args:
        weapon_name: Name of the weapon used for the kill
        rules: Rules instance to use for calculations
        
    Returns:
        Kill reward amount in dollars
    """
    if not weapon_name:
        return rules.rifle_reward  # Default for unknown weapons
    
    weapon_lower = weapon_name.lower()
    
    # Knife weapons
    if weapon_lower in KNIFE_WEAPONS:
        return rules.knife_reward
    
    # Special cases first
    if weapon_lower == "p90":
        return rules.p90_reward
    if weapon_lower == "xm1014":
        return rules.xm1014_reward
    if weapon_lower == "awp":
        return rules.awp_reward
    if weapon_lower == "zeus" or weapon_lower == "taser":
        return rules.zeus_reward
    
    # Weapon categories
    if weapon_lower in SMG_WEAPONS:
        return rules.smg_default_reward
    if weapon_lower in SHOTGUN_WEAPONS:
        return rules.shotgun_default_reward
    if weapon_lower in RIFLE_WEAPONS:
        return rules.rifle_reward
    if weapon_lower in PISTOL_WEAPONS:
        return rules.pistol_reward
    if weapon_lower in GRENADE_WEAPONS:
        return rules.grenade_reward
    
    # Default to rifle reward for unknown weapons
    return rules.rifle_reward


def get_loss_bonus(loss_streak: int, rules: Rules = DEFAULT_RULES) -> int:
    """Get loss bonus amount based on current loss streak.
    
    Args:
        loss_streak: Current consecutive losses (0-based)
        rules: Rules instance to use for calculations
        
    Returns:
        Loss bonus amount in dollars
    """
    if loss_streak <= 0:
        return 0
    
    # Loss streak is 1-indexed in game, but our ladder is 0-indexed
    ladder_index = min(loss_streak - 1, len(rules.loss_bonus_ladder) - 1)
    return rules.loss_bonus_ladder[ladder_index]


def get_win_reward(win_type: str, rules: Rules = DEFAULT_RULES) -> int:
    """Get win reward based on how the round was won.
    
    Args:
        win_type: Type of round win (elimination, bomb_explosion, defuse, time_expired)
        rules: Rules instance to use for calculations
        
    Returns:
        Win reward amount in dollars
    """
    win_type_lower = win_type.lower() if win_type else ""
    
    if win_type_lower == "elimination":
        return rules.elimination_reward
    elif win_type_lower == "bomb_explosion" or win_type_lower == "t_bomb_explosion":
        return rules.t_bomb_explosion_reward
    elif win_type_lower == "defuse" or win_type_lower == "ct_defuse":
        return rules.ct_defuse_reward
    elif win_type_lower == "time_expired" or win_type_lower == "ct_time_expired_no_plant":
        return rules.ct_time_expired_no_plant_reward
    else:
        # Default to elimination reward for unknown win types
        return rules.elimination_reward


def clamp_money(amount: int, rules: Rules = DEFAULT_RULES) -> int:
    """Clamp money amount to valid range [0, money_cap].
    
    Args:
        amount: Money amount to clamp
        rules: Rules instance to use for calculations
        
    Returns:
        Clamped money amount
    """
    return max(0, min(amount, rules.money_cap))
