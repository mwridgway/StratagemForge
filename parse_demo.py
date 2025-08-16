import polars as pl
import awpy
from awpy.plot import plot, PLOT_SETTINGS
from awpy import Demo
from awpy.stats import adr
from awpy.plot import gif
from tqdm import tqdm

dem = Demo("demos/vitality-vs-mouz-m1-mirage-p1.dem")
dem.parse(player_props=["health", "armor_value", "pitch", "yaw"])

print(adr(dem))

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

for tick in tqdm(dem.ticks.filter(pl.col("round_num") == 1)["tick"].unique().to_list()[::16]):
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