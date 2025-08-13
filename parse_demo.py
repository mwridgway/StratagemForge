# parse_demo.py
import duckdb, pandas as pd
from awpy import Demo

# demo = "demos/vitality-vs-mouz-m1-mirage-p1.dem"
dem = Demo("demos/vitality-vs-mouz-m1-mirage-p1.dem")

dem.parse()

kills = dem.kills.to_pandas()
nades = dem.grenades.to_pandas()

print(kills.columns)

# con = duckdb.connect("cs2.duckdb")
# con.execute("CREATE TABLE IF NOT EXISTS kills AS SELECT * FROM kills LIMIT 0")
# con.execute("INSERT INTO kills SELECT * FROM kills")
# con.execute("CREATE TABLE IF NOT EXISTS nades AS SELECT * FROM nades LIMIT 0")
# con.execute("INSERT INTO nades SELECT * FROM nades")

# # Example feature: flash that led to an entry within 5s
# con.execute("""
# CREATE OR REPLACE TABLE entry_flashes AS
# WITH entries AS (
#   SELECT roundNum, tick, victimSteamID AS ct, attackerSteamID AS t
#   FROM kills WHERE isFirstKill = true
# ),
# flashes AS (
#   SELECT roundNum, tick, throwerSteamID, victimSteamID
#   FROM nades WHERE weapon=='flashbang' AND isFlash==true
# )
# SELECT e.roundNum, e.t, f.throwerSteamID AS flasher, MIN(e.tick - f.tick) AS dt
# FROM entries e
# JOIN flashes f USING(roundNum)
# WHERE e.tick - f.tick BETWEEN 0 AND 5*128
# GROUP BY 1,2,3;
# """)
