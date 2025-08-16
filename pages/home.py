import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Register this page
dash.register_page(__name__, path='/', name='Home')

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("StrategemForge", className="text-center mb-4"),
            html.H3("AI-Powered Counter-Strike 2 Analytics Platform", className="text-center text-muted mb-5"),
            
            dbc.Card([
                dbc.CardBody([
                    html.H4("Welcome to StrategemForge", className="card-title"),
                    html.P([
                        "A comprehensive, self-hostable analytics platform designed to give Counter-Strike 2 teams a competitive edge. ",
                        "This platform leverages advanced AI, including Graph Neural Networks (GNNs) for tactical analysis and ",
                        "Large Language Models (LLMs) for generating actionable insights."
                    ], className="card-text"),
                    
                    html.Hr(),
                    
                    html.H5("Features:", className="mb-3"),
                    html.Ul([
                        html.Li("Automated Demo Parsing - Convert .dem files to structured data"),
                        html.Li("Interactive 2D Replay Viewer - Visualize rounds with player positions"),
                        html.Li("AI-Powered Analysis - Ask questions about your gameplay data"),
                        html.Li("Tactical Classification - Automatically identify team strategies"),
                        html.Li("Opponent Scouting - Generate detailed analysis reports")
                    ]),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("View Matches", color="primary", href="/matches", className="me-2"),
                            dbc.Button("Start Analysis", color="success", href="/analysis"),
                        ])
                    ])
                ])
            ])
        ], width=8)
    ], justify="center"),
    
    html.Hr(className="my-5"),
    
    dbc.Row([
        dbc.Col([
            html.H4("System Status", className="mb-3"),
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                "System initialized and ready for demo analysis"
            ], color="success")
        ], width=8)
    ], justify="center")
])
