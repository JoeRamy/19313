import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
import plotly.graph_objs as go

# Function to convert Fahrenheit to Celsius
def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) / 1.8

# Function to return the air quality threshold
def air_quality_threshold():
    return 50

# Define thresholds for each sensor
THRESHOLDS = {
    'temperature': fahrenheit_to_celsius(100),
    'humidity': 80,
    'co_level': 200,
    'heat_index': 45,
    'air_quality_index': air_quality_threshold()
}

# Connect to the SQLite database and fetch the latest data
def fetch_data(limit=50):
    conn = sqlite3.connect('D:/Joee/T3/SensorsReadings.db')  # Adjusted database path
    query = f"SELECT * FROM sensor_readings ORDER BY real_time DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Sort by timestamp for correct plotting
    df = df.rename(columns={'real_time': 'timestamp'})
    df = df.sort_values(by='timestamp')
    return df

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Sensor Data Dashboard"),
    
    # Tabs for different graphs
    dcc.Tabs([
        dcc.Tab(label='Line Graphs', children=[
            html.H2("Line Graphs for Individual Sensors"),
            html.P("Select a sensor to view live data as a line graph, with real-time updates every 10 seconds."),
            html.Label("Choose Sensor:"),
            dcc.Dropdown(
                id='sensor-dropdown',
                options=[{'label': sensor.capitalize(), 'value': sensor} for sensor in THRESHOLDS.keys()],
                value='temperature'  # Default sensor
            ),
            dcc.Graph(id='line-graphs'),
            dcc.Interval(
                id='interval-line-graphs',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            ),
            html.Div(id='line-real-time', style={'fontSize': 20, 'fontWeight': 'bold'}),  # Real-time label
            html.Div(id='line-heat-index-danger-label', style={'fontSize': 18, 'fontWeight': 'bold'})  # Danger level label
        ]),
        dcc.Tab(label='Instantaneous Readings', children=[
            html.H2("Instantaneous Readings with Thresholds"),
            html.P("Displays bar graphs of current sensor readings with thresholds, updated every 10 seconds."),
            dcc.Graph(id='instantaneous-readings'),
            dcc.Interval(
                id='interval-instantaneous-readings',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            ),
            html.Div(id='instantaneous-real-time', style={'fontSize': 20, 'fontWeight': 'bold'}),  # Real-time label
            html.Div(id='instantaneous-heat-index-danger-label', style={'fontSize': 18, 'fontWeight': 'bold'})  # Danger level label
        ]),
        dcc.Tab(label='All Data Collected', children=[
            html.H2("All Data Collected Over Time"),
            html.P("Displays all collected sensor data in a multi-line graph, showing historical trends for each sensor."),
            dcc.Graph(id='all-data-graphs'),
            dcc.Interval(
                id='interval-all-data-graphs',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            ),
            html.Div(id='all-real-time', style={'fontSize': 20, 'fontWeight': 'bold'}),  # Real-time label
            html.Div(id='all-heat-index-danger-label', style={'fontSize': 18, 'fontWeight': 'bold'})  # Danger level label
        ]),
        dcc.Tab(label='Radial Progress Indicators', children=[
            html.H2("Radial Progress Indicators"),
            html.P("Displays the latest reading of each sensor as a radial progress indicator, showing the value relative to the defined threshold."),
            dcc.Graph(id='radial-progress'),
            dcc.Interval(
                id='interval-radial-progress',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            ),
            html.Div(id='radial-real-time', style={'fontSize': 20, 'fontWeight': 'bold'}),  # Real-time label
            html.Div(id='radial-heat-index-danger-label', style={'fontSize': 18, 'fontWeight': 'bold'})  # Danger level label
        ])
    ])
])

# Callback to update the line graph based on the selected sensor
@app.callback(
    [Output('line-graphs', 'figure'),
     Output('line-real-time', 'children'),
     Output('line-heat-index-danger-label', 'children')],
    [Input('interval-line-graphs', 'n_intervals'),
     Input('sensor-dropdown', 'value')]
)
def update_line_graphs(n, sensor):
    df = fetch_data()
    if df.empty:
        return go.Figure(), "Real-Time: N/A", "Danger Level: N/A"  # Return empty figure and labels if no data

    # Update the real-time label with the current timestamp
    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    # Separate data based on threshold
    threshold = THRESHOLDS.get(sensor, None)
    df_normal = df[df[sensor] <= threshold]
    df_exceeded = df[df[sensor] > threshold]

    # Create the line graph for the selected sensor
    figure = {
        'data': [
            go.Scatter(
                x=df_normal['timestamp'],
                y=df_normal[sensor],
                mode='lines+markers',
                name=f"{sensor.capitalize()} (Normal)",
                line=dict(color='blue')
            ),
            go.Scatter(
                x=df_exceeded['timestamp'],
                y=df_exceeded[sensor],
                mode='lines+markers',
                name=f"{sensor.capitalize()} (Exceeded)",
                line=dict(color='red')
            )
        ],
        'layout': go.Layout(
            title=f'Live {sensor.capitalize()} Data',
            xaxis=dict(title='Timestamp'),
            yaxis=dict(title=sensor.capitalize()),
            hovermode='closest',
            shapes=[dict(
                type='line',
                x0=df['timestamp'].min(),
                x1=df['timestamp'].max(),
                y0=threshold,
                y1=threshold,
                line=dict(color='green', width=2, dash='dash'),
                name=f'{sensor.capitalize()} Threshold'
            )]
        )
    }

    # Determine the heat index danger level for the current reading
    heat_index_value = df['heat_index'].values[-1]
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger (Alarm)"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger (Alarm) "
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution "
    elif heat_index_value >= 80:
        danger_level = "Heat Index Danger Level: Caution"
    else:
        danger_level = "Heat Index Danger Level: Normal"

    return figure, real_time_label, danger_level

# Callback to update the instantaneous readings graph with thresholds
@app.callback(
    [Output('instantaneous-readings', 'figure'),
     Output('instantaneous-real-time', 'children'),
     Output('instantaneous-heat-index-danger-label', 'children')],
    Input('interval-instantaneous-readings', 'n_intervals')
)
def update_instantaneous_readings(n):
    df = fetch_data()
    if df.empty:
        return go.Figure(), "Real-Time: N/A", "Danger Level: N/A"  # Return empty figure and labels if no data

    # Update the real-time label with the current timestamp
    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    fig = go.Figure()
    heat_index_value = df['heat_index'].values[-1]  # Get the latest heat index value
    danger_level = ""
    
    # Determine the danger level based on the heat index value
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger"
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution"
    elif heat_index_value >= 80:
        danger_level = "Heat Index Danger Level: Caution"
    else:
        danger_level = "Heat Index Danger Level: Normal"

    for sensor, threshold in THRESHOLDS.items():
        current_value = df[sensor].values[-1]  # Get the latest reading for each sensor
        fig.add_trace(
            go.Bar(
                x=[sensor.capitalize()],
                y=[current_value],
                name=sensor.capitalize(),
                text=f"{current_value}",
                textposition='auto',
            )
        )
        fig.add_shape(
            type='line',
            x0=sensor.capitalize(),
            y0=threshold,
            x1=sensor.capitalize(),
            y1=threshold,
            line=dict(color='red', width=2, dash='dash'),
        )
    
    fig.update_layout(
        title='Current Sensor Readings with Thresholds',
        yaxis=dict(title='Value'),
        xaxis=dict(title='Sensor'),
        showlegend=False
    )
    
    return fig, real_time_label, danger_level

# Callback to update the all data collected graph
@app.callback(
    [Output('all-data-graphs', 'figure'),
     Output('all-real-time', 'children'),
     Output('all-heat-index-danger-label', 'children')],
    Input('interval-all-data-graphs', 'n_intervals')
)
def update_all_data_graphs(n):
    df = fetch_data()
    if df.empty:
        return go.Figure(), "Real-Time: N/A", "Danger Level: N/A"  # Return empty figure and labels if no data

    # Update the real-time label with the current timestamp
    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    # Create a multi-line graph for all sensors
    figure = {
        'data': [],
        'layout': go.Layout(
            title='All Sensor Data Over Time',
            xaxis=dict(title='Timestamp'),
            yaxis=dict(title='Value'),
            hovermode='closest'
        )
    }

    # Add traces for each sensor
    for sensor in THRESHOLDS.keys():
        figure['data'].append(go.Scatter(
            x=df['timestamp'],
            y=df[sensor],
            mode='lines+markers',
            name=sensor.capitalize()
        ))

    # Determine the heat index danger level for the current reading
    heat_index_value = df['heat_index'].values[-1]
    danger_level = ""
    
    # Determine the danger level based on the heat index value
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger"
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution"
    elif heat_index_value >= 80:
        danger_level = "Heat Index Danger Level: Caution"
    else:
        danger_level = "Heat Index Danger Level: Normal"

    return figure, real_time_label, danger_level

# Callback to update the radial progress indicators
@app.callback(
    [Output('radial-progress', 'figure'),
     Output('radial-real-time', 'children'),
     Output('radial-heat-index-danger-label', 'children')],
    Input('interval-radial-progress', 'n_intervals')
)
def update_radial_progress(n):
    df = fetch_data()
    if df.empty:
        return go.Figure(), "Real-Time: N/A", "Danger Level: N/A"  # Return empty figure and labels if no data

    # Update the real-time label with the current timestamp
    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    fig = go.Figure()
    heat_index_value = df['heat_index'].values[-1]  # Get the latest heat index value
    danger_level = ""
    
    # Determine the danger level based on the heat index value
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger"
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution"
    elif heat_index_value >= 80:
        danger_level = "Heat Index Danger Level: Caution"
    else:
        danger_level = "Heat Index Danger Level: Normal"

    for sensor, threshold in THRESHOLDS.items():
        current_value = df[sensor].values[-1]  # Get the latest reading for each sensor
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_value,
                title={'text': f"{sensor.capitalize()}"},
                gauge={
                    'axis': {'range': [None, threshold]},
                    'bar': {'color': 'blue'},
                    'steps': [
                        {'range': [0, threshold * 0.7], 'color': "lightgreen"},
                        {'range': [threshold * 0.7, threshold], 'color': "orange"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': threshold
                    }
                },
                domain={'x': [0.2 * (list(THRESHOLDS.keys()).index(sensor)), 0.2 * (list(THRESHOLDS.keys()).index(sensor) + 1)], 'y': [0, 1]}
            )
        )
    
    fig.update_layout(
        title='Radial Progress Indicators',
        grid={'rows': 1, 'columns': len(THRESHOLDS)}
    )
    
    return fig, real_time_label, danger_level  # Return both the figure and the updated label

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)