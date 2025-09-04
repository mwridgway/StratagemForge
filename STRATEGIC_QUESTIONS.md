# CS2 Strategic Analysis Questions

## 🎯 **Team Preparation Questions**

### **Map Control & Territory Analysis**
```sql
-- Which areas does each team control most effectively?
SELECT demo_name, m_iTeamNum as team, 
       ROUND(AVG(X), 1) as control_center_x,
       ROUND(AVG(Y), 1) as control_center_y,
       COUNT(*) as presence_strength
FROM all_player_ticks 
WHERE m_iTeamNum IN (2, 3)
GROUP BY demo_name, m_iTeamNum;

-- What are the most contested zones?
SELECT demo_name,
       ROUND(X/300)*300 as zone_x,
       ROUND(Y/300)*300 as zone_y,
       COUNT(DISTINCT m_iTeamNum) as teams_present,
       COUNT(*) as total_activity
FROM all_player_ticks
WHERE m_iTeamNum IN (2, 3)
GROUP BY demo_name, zone_x, zone_y
HAVING teams_present > 1
ORDER BY total_activity DESC;
```

### **Player Role & Positioning Intelligence**
```sql
-- What are each player's preferred zones?
SELECT name, demo_name,
       ROUND(AVG(X), 1) as avg_x,
       ROUND(AVG(Y), 1) as avg_y,
       ROUND(STDDEV(X), 1) as mobility_x,
       ROUND(STDDEV(Y), 1) as mobility_y
FROM all_player_ticks
WHERE name IS NOT NULL
GROUP BY name, demo_name
ORDER BY mobility_x + mobility_y DESC;

-- Who are the most predictable players?
SELECT name,
       ROUND(X/400)*400 as preferred_zone_x,
       ROUND(Y/400)*400 as preferred_zone_y,
       COUNT(*) as time_in_zone,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY name), 2) as zone_percentage
FROM all_player_ticks
WHERE name IS NOT NULL
GROUP BY name, preferred_zone_x, preferred_zone_y
HAVING time_in_zone > 1000
ORDER BY zone_percentage DESC;
```

### **Utility Usage & Coordination**
```sql
-- Which players use grenades most effectively for team support?
SELECT name, grenade_type,
       COUNT(DISTINCT demo_name) as maps_used,
       COUNT(DISTINCT tick) as unique_throws,
       ROUND(AVG(x), 1) as avg_throw_x,
       ROUND(AVG(y), 1) as avg_throw_y
FROM all_grenades
WHERE x IS NOT NULL AND name IS NOT NULL
GROUP BY name, grenade_type
ORDER BY unique_throws DESC;

-- What are the most common utility combinations?
SELECT g1.demo_name, g1.name as player1, g2.name as player2,
       g1.grenade_type as nade1, g2.grenade_type as nade2,
       COUNT(*) as combo_frequency
FROM all_grenades g1
JOIN all_grenades g2 ON g1.demo_name = g2.demo_name
WHERE ABS(g1.tick - g2.tick) <= 64  -- Within 2 seconds
  AND g1.name != g2.name
  AND g1.tick <= g2.tick
GROUP BY g1.demo_name, g1.name, g2.name, g1.grenade_type, g2.grenade_type
HAVING combo_frequency >= 3
ORDER BY combo_frequency DESC;
```

### **Team Coordination Patterns**
```sql
-- How tightly grouped do teams play?
SELECT demo_name, m_iTeamNum as team,
       ROUND(AVG(team_spread), 1) as avg_team_spread,
       ROUND(MIN(team_spread), 1) as tightest_formation,
       ROUND(MAX(team_spread), 1) as most_spread
FROM (
    SELECT demo_name, tick, m_iTeamNum,
           STDDEV(X) + STDDEV(Y) as team_spread
    FROM all_player_ticks
    WHERE m_iTeamNum IN (2, 3) AND tick % 128 = 0
    GROUP BY demo_name, tick, m_iTeamNum
    HAVING COUNT(*) >= 4
) team_formations
GROUP BY demo_name, m_iTeamNum;

-- Which players play closest to each other?
WITH player_distances AS (
    SELECT p1.name as player1, p2.name as player2,
           SQRT(POWER(p1.X - p2.X, 2) + POWER(p1.Y - p2.Y, 2)) as distance
    FROM all_player_ticks p1
    JOIN all_player_ticks p2 ON p1.demo_name = p2.demo_name 
        AND p1.tick = p2.tick 
        AND p1.m_iTeamNum = p2.m_iTeamNum
    WHERE p1.name < p2.name AND p1.tick % 256 = 0
)
SELECT player1, player2,
       ROUND(AVG(distance), 1) as avg_distance,
       COUNT(CASE WHEN distance <= 600 THEN 1 END) as close_proximity_time
FROM player_distances
GROUP BY player1, player2
ORDER BY avg_distance ASC;
```

## 🔍 **Anti-Stratting Questions**

### **Predictable Patterns**
```sql
-- What are the opponent's favorite positions?
SELECT name, demo_name,
       ROUND(X/250)*250 as position_x,
       ROUND(Y/250)*250 as position_y,
       COUNT(*) as time_spent,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY name, demo_name), 2) as position_preference
FROM all_player_ticks
WHERE name IN ('target_player1', 'target_player2')  -- Replace with opponent names
GROUP BY name, demo_name, position_x, position_y
ORDER BY position_preference DESC;

-- Do they have predictable utility patterns?
SELECT name, grenade_type,
       ROUND(x/200)*200 as throw_zone_x,
       ROUND(y/200)*200 as throw_zone_y,
       COUNT(*) as usage_frequency
FROM all_grenades
WHERE name IN ('target_player1', 'target_player2')  -- Replace with opponent names
  AND x IS NOT NULL
GROUP BY name, grenade_type, throw_zone_x, throw_zone_y
HAVING usage_frequency >= 3
ORDER BY usage_frequency DESC;
```

### **Timing Exploits**
```sql
-- When do they typically use utility?
SELECT demo_name,
       FLOOR(tick / 1280) * 10 as time_window_seconds,
       grenade_type,
       COUNT(*) as grenade_frequency,
       STRING_AGG(DISTINCT name, ', ') as players_involved
FROM all_grenades
GROUP BY demo_name, time_window_seconds, grenade_type
HAVING grenade_frequency >= 2
ORDER BY demo_name, time_window_seconds;

-- What are their peak activity periods?
SELECT demo_name,
       FLOOR(tick / 1920) * 15 as time_window_seconds,  -- 15-second windows
       COUNT(DISTINCT name) as active_players,
       COUNT(*) as total_actions,
       ROUND(AVG(X), 1) as activity_center_x,
       ROUND(AVG(Y), 1) as activity_center_y
FROM all_player_ticks
GROUP BY demo_name, time_window_seconds
ORDER BY total_actions DESC;
```

## 🎮 **Performance Analysis Questions**

### **Clutch Situations**
```sql
-- Who performs best in isolation?
WITH isolated_players AS (
    SELECT demo_name, tick, name,
           COUNT(*) OVER (PARTITION BY demo_name, tick, m_iTeamNum) as teammates_alive
    FROM all_player_ticks
    WHERE m_iTeamNum IN (2, 3)
)
SELECT name,
       COUNT(CASE WHEN teammates_alive <= 2 THEN 1 END) as clutch_situations,
       COUNT(*) as total_situations,
       ROUND(COUNT(CASE WHEN teammates_alive <= 2 THEN 1 END) * 100.0 / COUNT(*), 2) as clutch_rate
FROM isolated_players
GROUP BY name
ORDER BY clutch_rate DESC;
```

### **Equipment Preferences & Performance**
```sql
-- What equipment do players prefer and how does it affect their play?
SELECT p.name, s.def_index as weapon_type,
       COUNT(*) as usage_frequency,
       ROUND(AVG(STDDEV(p.X)), 1) as mobility_with_weapon,
       COUNT(DISTINCT p.demo_name) as maps_used
FROM all_player_info p
JOIN all_skins s ON p.steamid = s.steamid
JOIN all_player_ticks pt ON p.steamid = pt.steamid AND p.demo_name = pt.demo_name
GROUP BY p.name, s.def_index
HAVING usage_frequency > 100
ORDER BY usage_frequency DESC;
```

## 🗺️ **Map-Specific Intelligence**

### **Site Control Analysis**
```sql
-- Which areas indicate bomb site control?
SELECT demo_name,
       CASE 
           WHEN X > 0 AND Y > 0 THEN 'Site_A_Area'
           WHEN X < 0 AND Y < 0 THEN 'Site_B_Area'
           WHEN ABS(X) < 500 AND ABS(Y) < 500 THEN 'Mid_Control'
           ELSE 'Other_Area'
       END as map_area,
       m_iTeamNum as team,
       COUNT(*) as control_time,
       COUNT(DISTINCT name) as players_involved
FROM all_player_ticks
WHERE m_iTeamNum IN (2, 3)
GROUP BY demo_name, map_area, m_iTeamNum
ORDER BY demo_name, control_time DESC;
```

### **Rotation Patterns**
```sql
-- How do teams rotate between areas?
WITH position_changes AS (
    SELECT name, demo_name, tick,
           X, Y,
           LAG(X, 32) OVER (PARTITION BY name, demo_name ORDER BY tick) as prev_x,
           LAG(Y, 32) OVER (PARTITION BY name, demo_name ORDER BY tick) as prev_y
    FROM all_player_ticks
    WHERE tick % 32 = 0  -- Sample every second
)
SELECT name, demo_name,
       SQRT(POWER(X - prev_x, 2) + POWER(Y - prev_y, 2)) as movement_distance,
       COUNT(*) as movement_frequency
FROM position_changes
WHERE prev_x IS NOT NULL AND movement_distance > 800  -- Significant rotations
GROUP BY name, demo_name, movement_distance
ORDER BY movement_frequency DESC;
```

## 📊 **Sample Implementation**

To answer these questions with your data:

```python
from duckdb_connector import CSGODataAnalyzer

analyzer = CSGODataAnalyzer()

# Example: Find the most predictable players
predictable_players = analyzer.query("""
SELECT name,
       ROUND(X/300)*300 as zone_x,
       ROUND(Y/300)*300 as zone_y,
       COUNT(*) as time_in_zone,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY name), 2) as predictability
FROM all_player_ticks
WHERE name IS NOT NULL
GROUP BY name, zone_x, zone_y
HAVING time_in_zone > 1000
ORDER BY predictability DESC
LIMIT 20
""")

print("Most Predictable Player Positions:")
print(predictable_players)

analyzer.close()
```

These questions help analysts understand:
- **Opponent weaknesses** to exploit
- **Predictable patterns** to counter  
- **Effective strategies** to adapt
- **Team coordination** to disrupt
- **Individual tendencies** to target
