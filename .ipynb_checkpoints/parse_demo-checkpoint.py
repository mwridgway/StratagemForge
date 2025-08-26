import polars as pl
import awpy
from awpy.plot import plot, PLOT_SETTINGS
from awpy import Demo
from awpy.stats import adr
from awpy.plot import gif
from tqdm import tqdm

dem = Demo("demos/vitality-vs-mouz-m1-mirage-p1.dem")
dem.parse(player_props=["health", "armor_value", "pitch", "yaw"])

# print(adr(dem))

# Get the map name from the demo
# Try different methods to extract map name
if hasattr(dem, 'header') and 'mapName' in dem.header:
    map_name = dem.header['mapName']
elif hasattr(dem, 'map'):
    map_name = dem.map
else:
    # Fallback: extract from demo file name
    import os
    demo_filename = os.path.basename("demos/vitality-vs-mouz-m1-mirage-p1.dem")
    if "mirage" in demo_filename.lower():
        map_name = "de_mirage"
    elif "dust2" in demo_filename.lower():
        map_name = "de_dust2"
    elif "inferno" in demo_filename.lower():
        map_name = "de_inferno"
    else:
        map_name = "de_dust2"  # Default fallback
        
print(f"Map: {map_name}")


# iterate through the first 200 ticks and print out player name and position data for each tick
prev_positions = {}

for tick in dem.ticks["tick"].unique().to_list()[:2000]:
    frame_df = dem.ticks.filter(pl.col("tick") == tick)
    for row in frame_df.iter_rows(named=True):
        # just print for ropz, only when position changes
        if row['name'] == "ropz":
            current_position = (row['X'], row['Y'], row['Z'])
            player_name = row['name']
            
            if player_name not in prev_positions or current_position != prev_positions[player_name]:
                print(f"Tick {tick}: {row['name']} ({row['side']}) at {row['X']}, {row['Y']}, {row['Z']}")
                prev_positions[player_name] = current_position

# calculate the total distance traveled by ropz
total_distance = 0
prev_position = None

# for tick in dem.ticks["tick"].unique().to_list()[:200]:
#     frame_df = dem.ticks.filter(pl.col("tick") == tick)
#     for row in frame_df.iter_rows(named=True):
#         if row['name'] == "ropz":
#             curr_x, curr_y, curr_z = row['X'], row['Y'], row['Z']
            
#             if prev_position is not None:
#                 prev_x, prev_y, prev_z = prev_position
#                 distance = ((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2 + (curr_z - prev_z) ** 2) ** 0.5
#                 total_distance += distance
            
#             prev_position = (curr_x, curr_y, curr_z)

# print(f"Total distance traveled by ropz: {total_distance:.2f} units")

# print(f"\nHeader: \n{dem.header}")
# print(f"\nRounds: \n{dem.rounds.head(n=3)}")
# print(f"\nKills: \n{dem.kills.head(n=3)}")
# print(f"\nDamages: \n{dem.damages.head(n=3)}")
# print(f"\nWeapon Fires: \n{dem.shots.head(n=3)}")
# print(f"\nBomb: \n{dem.bomb.head(n=3)}")
# print(f"\nSmokes: \n{dem.smokes.head(n=3)}")
# print(f"\nInfernos: \n{dem.infernos.head(n=3)}")
# print(f"\nGrenades: \n{dem.grenades.head(n=3)}")
# print(f"\nFootsteps: \n{dem.footsteps.head(n=3)}")
# print(f"\nTicks: \n{dem.ticks.head(n=3000)}")
# print(f"\nTickrate: \n{dem.tickrate}")



# Get a random tick
frame_df = dem.ticks.filter(pl.col("tick") == dem.ticks["tick"].unique()[14345])
frame_df = frame_df[
    ["X", "Y", "Z", "health", "armor", "pitch", "yaw", "side", "name"]
]

points = []
point_settings = []

for row in frame_df.iter_rows(named=True):
    points.append((row["X"], row["Y"], row["Z"]))
    print(f"plotting {row['name']} ({row['side']}) at {row['X']}, {row['Y']}, {row['Z']}")

    # Determine team and corresponding settings
    settings = PLOT_SETTINGS[row["side"]].copy()

    # Add additional settings
    settings.update(
        {
            "hp": row["health"],
            "armor": row["armor"],
            "direction": (row["pitch"], row["yaw"]),
            "label": row["name"],
        }
    )

    point_settings.append(settings)

plot(map_name=map_name, points=points, point_settings=point_settings)

frames = []

for tick in tqdm(dem.ticks.filter(pl.col("round_num") == 1)["tick"].unique().to_list()[::128]):
    frame_df = dem.ticks.filter(pl.col("tick") == tick)
    frame_df = frame_df[
        ["X", "Y", "Z", "health", "armor", "pitch", "yaw", "side", "name"]
    ]

    points = []
    point_settings = []

    for row in frame_df.iter_rows(named=True):
        points.append((row["X"], row["Y"], row["Z"]))

        # Determine team and corresponding settings
        settings = PLOT_SETTINGS[row["side"]].copy()

        # Add additional settings
        settings.update(
            {
                "hp": row["health"],
                "armor": row["armor"],
                "direction": (row["pitch"], row["yaw"]),
                "label": row["name"],
            }
        )

        point_settings.append(settings)

    frames.append({"points": points, "point_settings": point_settings})

print("Finished processing frames. Creating gif...")
gif(map_name, frames, f"{map_name}.gif", duration=100)