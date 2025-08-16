import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

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
                    
                    # Map visualization area
                    dcc.Graph(
                        id='map-graph',
                        style={'height': '600px'},
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
    
    # Extract map name from filename if possible
    filename = demo_data['filename'].lower()
    if 'mirage' in filename:
        map_name = 'de_mirage'
    elif 'dust2' in filename:
        map_name = 'de_dust2'
    elif 'inferno' in filename:
        map_name = 'de_inferno'
    elif 'cache' in filename:
        map_name = 'de_cache'
    elif 'overpass' in filename:
        map_name = 'de_overpass'
    elif 'train' in filename:
        map_name = 'de_train'
    elif 'nuke' in filename:
        map_name = 'de_nuke'
    else:
        map_name = 'de_dust2'  # Default fallback
    
    return map_name

@callback(
    Output('map-graph', 'figure'),
    [Input('round-selector', 'value'),
     Input('time-slider', 'value')]
)
def update_map_visualization(selected_round, time_value):
    # Create a basic map visualization
    # This is a placeholder - in a real implementation, you'd load actual demo data
    
    fig = go.Figure()
    
    # Add map background (placeholder)
    fig.add_shape(
        type="rect",
        x0=-2000, y0=-2000, x1=2000, y1=2000,
        fillcolor="lightgray",
        opacity=0.3,
        layer="below",
        line_width=0,
    )
    
    # Sample player positions (T side in orange, CT side in blue)
    t_players = [
        {'name': 'Player1', 'x': 500, 'y': 500},
        {'name': 'Player2', 'x': 600, 'y': 400},
        {'name': 'Player3', 'x': 700, 'y': 300},
        {'name': 'Player4', 'x': 800, 'y': 200},
        {'name': 'Player5', 'x': 900, 'y': 100},
    ]
    
    ct_players = [
        {'name': 'CT1', 'x': -500, 'y': -500},
        {'name': 'CT2', 'x': -600, 'y': -400},
        {'name': 'CT3', 'x': -700, 'y': -300},
        {'name': 'CT4', 'x': -800, 'y': -200},
        {'name': 'CT5', 'x': -900, 'y': -100},
    ]
    
    # Add T side players
    fig.add_scatter(
        x=[p['x'] for p in t_players],
        y=[p['y'] for p in t_players],
        mode='markers+text',
        text=[p['name'] for p in t_players],
        textposition="top center",
        marker=dict(size=15, color='orange', symbol='circle'),
        name='Terrorists',
        hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
    )
    
    # Add CT side players
    fig.add_scatter(
        x=[p['x'] for p in ct_players],
        y=[p['y'] for p in ct_players],
        mode='markers+text',
        text=[p['name'] for p in ct_players],
        textposition="top center",
        marker=dict(size=15, color='blue', symbol='circle'),
        name='Counter-Terrorists',
        hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
    )
    
    fig.update_layout(
        title=f"Round {selected_round} - Time: {time_value}s",
        xaxis_title="X Position",
        yaxis_title="Y Position",
        showlegend=True,
        height=600,
        xaxis=dict(range=[-2500, 2500]),
        yaxis=dict(range=[-2500, 2500], scaleanchor="x", scaleratio=1)
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
