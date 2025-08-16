import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                use_pages=True,
                suppress_callback_exceptions=True)

# Define the layout with navigation
app.layout = dbc.Container([
    # Store components for sharing data between pages
    dcc.Store(id='selected-demo-store', storage_type='session'),
    
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
            dbc.NavItem(dbc.NavLink("Match Selection", href="/matches", active="exact")),
            dbc.NavItem(dbc.NavLink("Round Analysis", href="/analysis", active="exact")),
            dbc.NavItem(dbc.NavLink("AI Analyst", href="/ai-analyst", active="exact")),
        ],
        brand="StrategemForge - CS2 Analytics",
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    
    # Page content will be injected here
    dash.page_container
    
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
