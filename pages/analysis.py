from awpy import Demo
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from flask import json
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
from awpy.plot import plot, PLOT_SETTINGS
import polars as pl

from utils.demo_utils import extract_map_name_from_filename

# Register this page
dash.register_page(__name__, path='/analysis', name='Round Analysis')

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Round Analysis", className="mb-4"),
            
            # Demo info display
            html.Div(id="selected-demo-display", className="mb-3"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Interactive 2D Replay Viewer", className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Round:"),
                            dcc.Dropdown(
                                id='round-selector',
                                options=[
                                    {'label': f'Round {i}', 'value': i} for i in range(1, 31)
                                ],
                                value=1,
                                className="mb-3"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Map:"),
                            html.P(id="map-display", className="font-weight-bold")
                        ], width=4),
                        dbc.Col([
                            html.Label("Round Time:"),
                            dcc.Slider(
                                id='time-slider',
                                min=0,
                                max=115,  # Typical round length in seconds
                                step=1,
                                value=0,
                                marks={i: f'{i}s' for i in range(0, 116, 15)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=4)
                    ]),
                    
                    html.Hr(),

                    # Graph should be square and centered, zoomed out 
                    dcc.Graph(
                        id='map-graph',
                        style={'height': '1024px', 'width': '1024px', 'margin': '0 auto'},
                        config={'displayModeBar': True}
                    ),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H5("Round Information"),
                            html.Div(id="round-info")
                        ], width=6),
                        dbc.Col([
                            html.H5("Event Timeline"),
                            html.Div(id="event-timeline")
                        ], width=6)
                    ])
                ])
            ])
        ])
    ])
])

@callback(
    Output('selected-demo-display', 'children'),
    Input('selected-demo-store', 'data')
)
def display_selected_demo_info(demo_data):
    if not demo_data:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "No demo selected. Please go to ",
            html.A("Match Selection", href="/matches", className="alert-link"),
            " to choose a demo file for analysis."
        ], color="warning")
    
    return dbc.Alert([
        html.I(className="fas fa-file me-2"),
        html.Strong(f"Analyzing: {demo_data['filename']}"),
        html.Br(),
        html.Small(f"Size: {demo_data['size_mb']} MB | Modified: {demo_data['modified']}")
    ], color="info")

@callback(
    Output('map-display', 'children'),
    [Input('round-selector', 'value'),
     Input('selected-demo-store', 'data')]
)
def update_map_display(selected_round, demo_data):
    if not demo_data:
        return "No demo selected"

    map_name = extract_map_name_from_filename(demo_data['filename'])
    
    return map_name

@callback(
    Output('map-graph', 'figure'),
    [Input('round-selector', 'value'),
     Input('time-slider', 'value'),
     Input('selected-demo-store', 'data')]
)
def update_map_visualization(selected_round, time_value, demo_data):
    # Create a basic map visualization
    # This is a placeholder - in a real implementation, you'd load actual demo data
    
    fig = go.Figure()

    map_name = extract_map_name_from_filename(demo_data['filename'])
    map_image = Image.open(f"maps/{map_name}.png")

        # load the map-data.json file and get the pos_x and pos_y
    # for the current map
    with open("maps/map-data.json") as f:
        map_data = json.load(f)

    pos_x = 0
    pos_y = 0
    scale = 1
    if map_name in map_data:
        pos_x = map_data[map_name]["pos_x"]
        pos_y = map_data[map_name]["pos_y"]
        scale = map_data[map_name].get("scale", 1)

    # get the map size from PLOT_SETTINGS
    map_size = PLOT_SETTINGS.get("map_size", 1024)

    fig.add_layout_image(
        dict(
            source=map_image,
            xref="x",
            yref="y",
            x=pos_x/scale,
            y=pos_y/scale, # Y-axis is often inverted
            sizex=map_size,
            sizey=map_size,
            sizing="stretch",
            layer="below"
        )
    )


    dem = Demo(f"demos/{demo_data['filename']}")
    dem.parse(player_props=["health", "armor_value", "pitch", "yaw"])

    # Get a random tick
    frame_df = dem.ticks.filter(pl.col("tick") == dem.ticks["tick"].unique()[1])
    frame_df = frame_df[
        ["X", "Y", "Z", "health", "armor", "pitch", "yaw", "side", "name"]
    ]

    all_players = []

    for row in frame_df.iter_rows(named=True):
        all_players.append({'name': f"{row['name']} ({row['side']})", 'x': row['X']/scale, 'y': row['Y']/scale})

    fig.add_scatter(
        x=[p['x'] for p in all_players],
        y=[p['y'] for p in all_players],
        mode='markers+text',
        text=[p['name'] for p in all_players],
        textposition="top center",
        marker=dict(size=15, color='gray', symbol='circle'),
        name='All Players',
        hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
    )

    # special_points = []
    # special_points.append({'name': 'Origin', 'x': pos_x/scale, 'y': pos_y/scale})
    # special_points.append({'name': 'Zero', 'x': 0, 'y': 0})
    # fig.add_scatter(
    #     x=[p['x'] for p in special_points],
    #     y=[p['y'] for p in special_points],
    #     mode='markers+text',
    #     text=[p['name'] for p in special_points],
    #     textposition="top center",
    #     marker=dict(size=15, color='red', symbol='circle'),
    #     name='Special Points',
    #     hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
    # )

    map_range = []

    # Update layout to make the graph perfectly square
    fig.update_layout(
        title=f"Round {selected_round} - Time: {time_value}s - {map_name}",
        xaxis=dict(
            range=[-512, 512],
            constrain="domain",
            scaleanchor="y",
            scaleratio=1
        ),
        yaxis=dict(
            range=[-512, 512],
            constrain="domain"
        ),
        width=600,
        height=600,
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

@callback(
    Output('round-info', 'children'),
    Input('round-selector', 'value')
)
def update_round_info(selected_round):
    return dbc.Card([
        dbc.CardBody([
            html.P(f"Round: {selected_round}"),
            html.P("Score: T 7 - 8 CT"),
            html.P("Winner: Counter-Terrorists"),
            html.P("Round Type: Bomb Defusal"),
            html.P("Duration: 1:45")
        ])
    ])

@callback(
    Output('event-timeline', 'children'),
    Input('time-slider', 'value')
)
def update_event_timeline(time_value):
    events = [
        {"time": 10, "event": "First contact - A site"},
        {"time": 25, "event": "Kill - Player1 -> CT1"},
        {"time": 40, "event": "Bomb planted"},
        {"time": 65, "event": "Kill - CT2 -> Player2"},
        {"time": 90, "event": "Bomb defused"}
    ]
    
    current_events = [e for e in events if e["time"] <= time_value]
    
    if not current_events:
        return html.P("No events yet...", className="text-muted")
    
    return dbc.ListGroup([
        dbc.ListGroupItem(f"{e['time']}s - {e['event']}") 
        for e in current_events
    ])
