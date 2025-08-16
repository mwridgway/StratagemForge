import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

# Register this page
dash.register_page(__name__, path='/ai-analyst', name='AI Analyst')

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("AI Analyst", className="mb-4"),
            html.P("Ask natural language questions about your CS2 gameplay data", 
                   className="text-muted mb-4"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Query Your Demos", className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.Input(
                                    id="question-input",
                                    placeholder="Ask a question about your gameplay... (e.g., 'How many rounds have we won on Inferno T-side when we get the first kill?')",
                                    type="text"
                                ),
                                dbc.Button("Ask", id="ask-btn", color="primary")
                            ])
                        ])
                    ]),
                    
                    html.Hr(),
                    
                    # Chat area
                    html.Div(id="chat-area", children=[
                        dbc.Alert([
                            html.I(className="fas fa-info-circle me-2"),
                            "AI Analyst is ready! Ask questions about your demo data to get insights."
                        ], color="info")
                    ], style={'height': '400px', 'overflow-y': 'auto', 'border': '1px solid #dee2e6', 'padding': '10px'}),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H5("Sample Questions:"),
                            dbc.ListGroup([
                                dbc.ListGroupItem([
                                    dbc.Button("What's our win rate on T-side?", 
                                             id="sample-q1", color="link", size="sm"),
                                ]),
                                dbc.ListGroupItem([
                                    dbc.Button("Which player has the highest K/D ratio?", 
                                             id="sample-q2", color="link", size="sm"),
                                ]),
                                dbc.ListGroupItem([
                                    dbc.Button("How often do we win when we get first kill?", 
                                             id="sample-q3", color="link", size="sm"),
                                ]),
                                dbc.ListGroupItem([
                                    dbc.Button("What's our most successful strategy on Mirage?", 
                                             id="sample-q4", color="link", size="sm"),
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            html.H5("Knowledge Base Status:"),
                            dbc.Alert([
                                html.I(className="fas fa-exclamation-triangle me-2"),
                                "RAG system not yet configured. This feature will be available in Phase 3."
                            ], color="warning")
                        ], width=6)
                    ])
                ])
            ])
        ])
    ])
])

@callback(
    Output('chat-area', 'children'),
    [Input('ask-btn', 'n_clicks'),
     Input('sample-q1', 'n_clicks'),
     Input('sample-q2', 'n_clicks'),
     Input('sample-q3', 'n_clicks'),
     Input('sample-q4', 'n_clicks')],
    [State('question-input', 'value'),
     State('chat-area', 'children')]
)
def update_chat(ask_clicks, sq1, sq2, sq3, sq4, question_value, current_chat):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_chat
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Determine the question
    if trigger_id == 'ask-btn' and question_value:
        question = question_value
    elif trigger_id == 'sample-q1':
        question = "What's our win rate on T-side?"
    elif trigger_id == 'sample-q2':
        question = "Which player has the highest K/D ratio?"
    elif trigger_id == 'sample-q3':
        question = "How often do we win when we get first kill?"
    elif trigger_id == 'sample-q4':
        question = "What's our most successful strategy on Mirage?"
    else:
        return current_chat
    
    # Add user question to chat
    user_message = dbc.Card([
        dbc.CardBody([
            html.P(question, className="mb-0"),
            html.Small("You", className="text-muted")
        ])
    ], className="mb-2 bg-light")
    
    # Generate AI response (placeholder for now)
    ai_response = dbc.Card([
        dbc.CardBody([
            html.P([
                "I understand you're asking: ",
                html.Em(question),
                ". However, the AI Analyst feature requires the RAG (Retrieval-Augmented Generation) system to be implemented. ",
                "This will allow me to search through your demo data and provide accurate, data-driven answers."
            ], className="mb-2"),
            html.P([
                "This feature will be available in Phase 3 of the project implementation. ",
                "Once configured, I'll be able to analyze your gameplay data and provide insights like win rates, player statistics, and tactical analysis."
            ], className="mb-0"),
            html.Small("AI Analyst", className="text-muted")
        ])
    ], className="mb-2 bg-primary text-white")
    
    # Add messages to chat
    new_chat = current_chat + [user_message, ai_response]
    
    return new_chat

@callback(
    Output('question-input', 'value'),
    [Input('sample-q1', 'n_clicks'),
     Input('sample-q2', 'n_clicks'),
     Input('sample-q3', 'n_clicks'),
     Input('sample-q4', 'n_clicks')]
)
def update_input_from_samples(sq1, sq2, sq3, sq4):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'sample-q1':
        return "What's our win rate on T-side?"
    elif trigger_id == 'sample-q2':
        return "Which player has the highest K/D ratio?"
    elif trigger_id == 'sample-q3':
        return "How often do we win when we get first kill?"
    elif trigger_id == 'sample-q4':
        return "What's our most successful strategy on Mirage?"
    
    return ""
