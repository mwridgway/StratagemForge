import dash
from dash import html, dcc, callback, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import os
import pandas as pd
from datetime import datetime
import base64
import shutil
import sys
sys.path.append('..')
from utils.demo_utils import list_demo_files, validate_demo_file, ensure_demos_directory, get_storage_info

# Register this page
dash.register_page(__name__, path='/matches', name='Match Selection')

def get_demo_files():
    """Get list of demo files from the demos directory"""
    return list_demo_files()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Match Selection", className="mb-4"),
            
            # Upload Modal
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Upload Demo File")),
                dbc.ModalBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Demo Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px',
                            'cursor': 'pointer'
                        },
                        # Allow multiple files to be uploaded
                        multiple=True
                    ),
                    html.Div(id='upload-status', className="mt-3")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id="close-upload-modal", className="ms-auto", n_clicks=0)
                ])
            ],
            id="upload-modal",
            is_open=False,
            size="lg"
            ),
            
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Demo Files", className="mb-0")
                ]),
                dbc.CardBody([
                    # Storage info
                    html.Div(id="storage-info", className="mb-3"),
                    
                    html.P("Select a demo file to analyze:", className="text-muted mb-3"),
                    
                    html.Div(id="demo-files-table"),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Refresh List", id="refresh-btn", color="secondary", className="me-2"),
                            dbc.Button("Upload Demo", id="upload-btn", color="primary"),
                        ])
                    ]),
                    
                    html.Div(id="selected-demo-info", className="mt-3")
                ])
            ])
        ])
    ])
])

@callback(
    [Output('demo-files-table', 'children'),
     Output('storage-info', 'children')],
    Input('refresh-btn', 'n_clicks')
)
def update_demo_table(n_clicks):
    demo_files = get_demo_files()
    storage_info = get_storage_info()
    
    # Storage info display
    storage_display = dbc.Alert([
        html.I(className="fas fa-hdd me-2"),
        f"Storage: {storage_info['total_files']} files, {storage_info['total_size_mb']} MB total"
    ], color="info", className="mb-3")
    
    if not demo_files:
        table_display = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "No demo files found in the demos/ directory. Please add some .dem files to get started."
        ], color="warning")
        return table_display, storage_display
    
    # Convert to DataFrame for table display
    df_data = []
    for demo in demo_files:
        df_data.append({
            'filename': demo['filename'],
            'size_mb': demo['size_mb'],
            'modified': demo['modified_str'],
            'status': demo['status']
        })
    
    df = pd.DataFrame(df_data)
    
    table_display = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {'name': 'Filename', 'id': 'filename'},
            {'name': 'Size (MB)', 'id': 'size_mb'},
            {'name': 'Modified', 'id': 'modified'},
            {'name': 'Status', 'id': 'status'}
        ],
        style_cell={'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        row_selectable='single',
        id='demo-table'
    )
    
    return table_display, storage_display

@callback(
    [Output('selected-demo-info', 'children'),
     Output('selected-demo-store', 'data')],
    Input('demo-table', 'selected_rows'),
    Input('demo-table', 'data')
)
def display_selected_demo(selected_rows, data):
    if not selected_rows or not data:
        return "", None
    
    selected_demo = data[selected_rows[0]]
    
    # Store the selected demo data
    demo_data = {
        'filename': selected_demo['filename'],
        'size_mb': selected_demo['size_mb'],
        'modified': selected_demo['modified'],
        'status': selected_demo['status']
    }
    
    display_content = dbc.Alert([
        html.H5(f"Selected: {selected_demo['filename']}", className="mb-2"),
        html.P(f"Size: {selected_demo['size_mb']} MB | Modified: {selected_demo['modified']}"),
        dbc.Button(
            "Analyze This Demo",
            color="success",
            href="/analysis",
            className="mt-2"
        )
    ], color="info")
    
    return display_content, demo_data

# Modal control callbacks
@callback(
    Output("upload-modal", "is_open"),
    [Input("upload-btn", "n_clicks"), Input("close-upload-modal", "n_clicks")],
    [State("upload-modal", "is_open")],
)
def toggle_upload_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# File upload callback
@callback(
    [Output('upload-status', 'children'),
     Output('demo-files-table', 'children', allow_duplicate=True),
     Output('storage-info', 'children', allow_duplicate=True)],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def handle_upload(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is None:
        return "", dash.no_update, dash.no_update
    
    # Ensure demos directory exists
    demo_dir = ensure_demos_directory()
    
    upload_results = []
    uploaded_files = []
    
    for content, name, date in zip(list_of_contents, list_of_names, list_of_dates):
        if name:
            try:
                # Decode the file content
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                
                # Validate the file
                validation = validate_demo_file(name, decoded)
                
                if not validation['valid'] and name.endswith('.dem'):
                    upload_results.append(f"⚠️ {name} - {validation['message']}")
                    continue
                elif not name.endswith('.dem'):
                    upload_results.append(f"❌ {name} - Invalid file type (must be .dem)")
                    continue
                
                # Save the file
                file_path = os.path.join(demo_dir, name)
                
                # Check if file already exists
                if os.path.exists(file_path):
                    upload_results.append(f"⚠️ {name} - File already exists, skipped")
                else:
                    with open(file_path, 'wb') as f:
                        f.write(decoded)
                    
                    file_size = len(decoded) / (1024 * 1024)  # Size in MB
                    upload_results.append(f"✅ {name} - Uploaded successfully ({file_size:.2f} MB)")
                    uploaded_files.append(name)
                    
            except Exception as e:
                upload_results.append(f"❌ {name} - Upload failed: {str(e)}")
    
    # Create status display
    status_content = [
        html.H5("Upload Results:", className="mb-3"),
        html.Ul([html.Li(result) for result in upload_results])
    ]
    
    if uploaded_files:
        status_content.append(
            dbc.Alert(f"Successfully uploaded {len(uploaded_files)} demo file(s)!", 
                     color="success", className="mt-3")
        )
    
    # Refresh the demo files table and storage info
    updated_table, updated_storage = update_demo_table(None)
    
    return status_content, updated_table, updated_storage
