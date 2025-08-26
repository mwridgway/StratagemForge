# VS Code Debugging Setup for StratagemForge

## Quick Start

1. **Open the project in VS Code**
2. **Select the Python interpreter**: 
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter" 
   - Choose `.venv/Scripts/python.exe`

3. **Start debugging**:
   - Press `F5` or go to Run and Debug panel
   - Select "Debug Dash App"
   - The app will start with debugger attached

## Debug Configurations Available

### 1. Debug Dash App
- **Purpose**: Debug the main Dash web application
- **Breakpoint locations**:
  - `app.py` line 35+ (main app startup)
  - `pages/analysis.py` callbacks (e.g., `update_map_visualization`)
  - `pages/matches.py` callbacks (e.g., `handle_upload`)
  - `utils/demo_utils.py` functions

### 2. Debug Parse Demo Script
- **Purpose**: Debug the demo parsing logic
- **Breakpoint locations**:
  - `parse_demo.py` line 8+ (demo loading)
  - Distance calculation loops
  - Position tracking logic

## Useful Debugging Features

### Setting Breakpoints
1. Click in the gutter (left of line numbers) to set breakpoints
2. Red dots indicate active breakpoints
3. Breakpoints will pause execution and show variable values

### Debug Console
- Access variables: type variable names in Debug Console
- Execute code: run Python expressions during debugging
- Inspect objects: examine complex data structures

### Variable Inspection
- **Variables panel**: Shows all local/global variables
- **Watch panel**: Add expressions to monitor continuously
- **Call Stack**: See function call hierarchy

## Common Debug Scenarios

### Debugging Dash Callbacks
```python
@callback(
    Output('map-graph', 'figure'),
    [Input('round-selector', 'value')]
)
def update_map_visualization(selected_round):
    # Set breakpoint here to debug callback execution
    print(f"Debug: selected_round = {selected_round}")  # Add debug prints
    # ... rest of function
```

### Debugging Demo Parsing
```python
# In parse_demo.py
for tick in dem.ticks["tick"].unique().to_list()[:2000]:
    # Set breakpoint here to debug tick processing
    frame_df = dem.ticks.filter(pl.col("tick") == tick)
    # ... rest of loop
```

## Hot Reload
- Changes to Python files will automatically restart the Dash app
- CSS/styling changes appear immediately
- Callback changes require app restart

## Environment Variables
- `FLASK_DEBUG=1`: Enables debug mode
- `FLASK_ENV=development`: Development environment

## Tips
1. Use `print()` statements for quick debugging
2. Check the integrated terminal for error messages
3. Use the Debug Console for interactive debugging
4. Set conditional breakpoints for specific conditions
5. Use the Call Stack to trace function calls

## Troubleshooting
- If debugger doesn't start: Check Python interpreter path
- If breakpoints don't work: Ensure `justMyCode` is true in launch.json
- If modules not found: Check `python.analysis.extraPaths` in settings.json
