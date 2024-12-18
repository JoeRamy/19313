import os
import io
import dash
from dash import dcc, html, Output, Input, callback, ctx
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
import plotly.graph_objs as go
from dash import Dash, html, dcc, Input, Output

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
    conn = sqlite3.connect(os.path.expanduser('~/SensorsReadings.db'))
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
app.layout = html.Div(
    style={'backgroundColor': 'black', 'padding': '20px', 'fontFamily': 'Arial, sans-serif'},
    children=[ 
        # Title
        html.Div(
            html.H1(
                "Sensor Data Dashboard",
                style={'textAlign': 'center', 'color': 'cyan', 'marginBottom': '20px'}
            ),
            style={'padding': '10px', 'borderBottom': '1px solid cyan'}
        ),

        # Tabs for different sections
        dcc.Tabs(
            style={
                'backgroundColor': '#202123',
                'color': 'white',
                'borderRadius': '8px',
                'overflow': 'hidden'
            },
            parent_style={'border': '1px solid cyan', 'borderRadius': '8px'},
            children=[

                # Line Graphs Tab
                dcc.Tab(
                    label='Line Graphs',
                    children=[ 
                        html.Div(
                            [
                                html.H2(
                                    "Line Graphs for Individual Sensors",
                                    style={'color': 'white', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.P(
                                    "Select a sensor to view live data as a line graph, with real-time updates every 10 seconds.",
                                    style={'color': 'grey', 'textAlign': 'center'}
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            "Choose Sensor:",
                                            style={'color': 'white', 'display': 'inline-block', 'width': '150px'}
                                        ),
                                        dcc.Dropdown(
                                            id='sensor-dropdown',
                                            options=[{'label': sensor.capitalize(), 'value': sensor} for sensor in THRESHOLDS.keys()],
                                            value='temperature',
                                            style={
                                                'backgroundColor': '#505357',  # Dropdown background
                                                'color': 'black',
                                                'border': '1px solid cyan',
                                                'borderRadius': '5px',
                                                'width': '300px',
                                                'display': 'inline-block'
                                            }
                                        )
                                    ],
                                    style={'textAlign': 'center', 'marginBottom': '20px'}
                                ),
                                dcc.Graph(
                                    id='line-graphs',
                                    style={
                                        'backgroundColor': '#202123',
                                        'padding': '10px',
                                        'borderRadius': '10px'
                                    }
                                ),
                                dcc.Interval(
                                    id='interval-line-graphs',
                                    interval=10 * 1000,
                                    n_intervals=0
                                ),
                                html.Div(
                                    id='line-real-time',
                                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': 'cyan', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.Div(
                                    id='line-heat-index-danger-label',
                                    style={'fontSize': '16px', 'fontWeight': 'bold', 'color': 'red', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                # Download button for Line Graphs tab
                                html.Div(
                                    [
                                        html.Button(
                                            "Download CSV",
                                            id='download-button-line-graphs',
                                            style={
                                                'color': 'black',
                                                'backgroundColor': 'cyan',
                                                'borderRadius': '5px',
                                                'padding': '10px',
                                                'border': 'none',
                                                'cursor': 'pointer'
                                            }
                                        ),
                                        dcc.Download(id='download-dataframe-csv-line-graphs')
                                    ],
                                    style={'position': 'absolute', 'top': '20px', 'right': '20px'}
                                )
                            ],
                            style={'padding': '20px'}
                        )
                    ],
                    style={'backgroundColor': 'black', 'color': 'white'}
                ),

                # Instantaneous Readings Tab
                dcc.Tab(
                    label='Instantaneous Readings',
                    children=[ 
                        html.Div(
                            [
                                html.H2(
                                    "Instantaneous Readings with Thresholds",
                                    style={'color': 'white', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.P(
                                    "Displays bar graphs of current sensor readings with thresholds, updated every 10 seconds.",
                                    style={'color': 'grey', 'textAlign': 'center'}
                                ),
                                dcc.Graph(
                                    id='instantaneous-readings',
                                    style={
                                        'backgroundColor': '#202123',
                                        'padding': '10px',
                                        'borderRadius': '10px'
                                    }
                                ),
                                dcc.Interval(
                                    id='interval-instantaneous-readings',
                                    interval=10 * 1000,
                                    n_intervals=0
                                ),
                                html.Div(
                                    id='instantaneous-real-time',
                                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': 'cyan', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.Div(
                                    id='instantaneous-heat-index-danger-label',
                                    style={'fontSize': '16px', 'fontWeight': 'bold', 'color': 'red', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                # Download button for Instantaneous Readings tab
                                html.Div(
                                    [
                                        html.Button(
                                            "Download CSV",
                                            id='download-button-instantaneous-readings',
                                            style={
                                                'color': 'black',
                                                'backgroundColor': 'cyan',
                                                'borderRadius': '5px',
                                                'padding': '10px',
                                                'border': 'none',
                                                'cursor': 'pointer'
                                            }
                                        ),
                                        dcc.Download(id='download-dataframe-csv-instantaneous-readings')
                                    ],
                                    style={'position': 'absolute', 'top': '20px', 'right': '20px'}
                                )
                            ],
                            style={'padding': '20px'}
                        )
                    ],
                    style={'backgroundColor': 'black', 'color': 'white'}
                ),

                # All Data Collected Tab
                dcc.Tab(
                    label='All Data Collected',
                    children=[ 
                        html.Div(
                            [
                                html.H2(
                                    "All Data Collected Over Time",
                                    style={'color': 'white', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.P(
                                    "Displays all collected sensor data in a multi-line graph, showing historical trends for each sensor.",
                                    style={'color': 'grey', 'textAlign': 'center'}
                                ),
                                dcc.Graph(
                                    id='all-data-graphs',
                                    style={
                                        'backgroundColor': '#202123',
                                        'padding': '10px',
                                        'borderRadius': '10px'
                                    }
                                ),
                                dcc.Interval(
                                    id='interval-all-data-graphs',
                                    interval=10 * 1000,
                                    n_intervals=0
                                ),
                                html.Div(
                                    id='all-real-time',
                                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': 'cyan', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.Div(
                                    id='all-heat-index-danger-label',
                                    style={'fontSize': '16px', 'fontWeight': 'bold', 'color': 'red', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                # Download button for All Data Collected tab
                                html.Div(
                                    [
                                        html.Button(
                                            "Download CSV",
                                            id='download-button-all-data-collected',
                                            style={
                                                'color': 'black',
                                                'backgroundColor': 'cyan',
                                                'borderRadius': '5px',
                                                'padding': '10px',
                                                'border': 'none',
                                                'cursor': 'pointer'
                                            }
                                        ),
                                        dcc.Download(id='download-dataframe-csv-all-data-collected')
                                    ],
                                    style={'position': 'absolute', 'top': '20px', 'right': '20px'}
                                )
                            ],
                            style={'padding': '20px'}
                        )
                    ],
                    style={'backgroundColor': 'black', 'color': 'white'}
                ),

                # Radial Progress Tab
                dcc.Tab(
                    label='Radial Progress Indicators',
                    children=[ 
                        html.Div(
                            [
                                html.H2(
                                    "Radial Progress Indicators",
                                    style={'color': 'white', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.P(
                                    "Displays the latest reading of each sensor as a radial progress indicator, showing the value relative to the defined threshold.",
                                    style={'color': 'grey', 'textAlign': 'center'}
                                ),
                                dcc.Graph(
                                    id='radial-progress',
                                    style={
                                        'backgroundColor': '#202123',
                                        'padding': '10px',
                                        'borderRadius': '10px'
                                    }
                                ),
                                 dcc.Interval(
                                    id='interval-radial-progress',
                                    interval=5 * 1000,  # Reduced interval to 5 seconds for faster updates
                                    n_intervals=0
                                ),
                                html.Div(
                                    id='radial-real-time',
                                    style={'fontSize': '20px', 'fontWeight': 'bold', 'color': 'lime', 'textAlign': 'center', 'marginTop': '10px'}
                                ),
                                html.Div(
                                    id='radial-heat-index-danger-label',
                                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': 'orange', 'textAlign': 'center', 'marginTop': '10px'}
                                ),

                                # Download button for Radial Progress Indicators tab
                                html.Div(
                                    [
                                        html.Button(
                                            "Download CSV",
                                            id='download-button',
                                            style={
                                                'color': 'black',
                                                'backgroundColor': 'cyan',
                                                'borderRadius': '5px',
                                                'padding': '10px',
                                                'border': 'none',
                                                'cursor': 'pointer'
                                            }
                                        ),
                                        dcc.Download(id='download-dataframe-csv')
                                    ],
                                    style={'position': 'absolute', 'top': '20px', 'right': '20px'}
                                )                   
                            ],
                            style={'backgroundColor': '#121212', 'color': '#FFFFFF'}
                        )
                    ],
                    style={'backgroundColor': '#121212', 'color': '#FFFFFF'} 
                ),
            ]
        )
    ]
)

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
        return go.Figure(), "Real-Time: N/A", "Danger Level: N/A"

    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    threshold = THRESHOLDS.get(sensor, None)
    df_normal = df[df[sensor] <= threshold]
    df_exceeded = df[df[sensor] > threshold]

    figure = {
        'data': [
            go.Scatter(
                x=df_normal['timestamp'],
                y=df_normal[sensor],
                mode='lines+markers',
                name=f"{sensor.capitalize()} (Normal)",
                line=dict(color='cyan'),
                marker=dict(symbol='circle', size=6, color='cyan')
            ),
            go.Scatter(
                x=df_exceeded['timestamp'],
                y=df_exceeded[sensor],
                mode='lines+markers',
                name=f"{sensor.capitalize()} (Exceeded)",
                line=dict(color='red'),
                marker=dict(symbol='diamond', size=8, color='red')
            )
        ],
        'layout': go.Layout(
            title=dict(text=f'Live {sensor.capitalize()} Data', font=dict(color='white')),
            xaxis=dict(title='Timestamp', titlefont=dict(color='white'), tickfont=dict(color='white')),
            yaxis=dict(title=sensor.capitalize(), titlefont=dict(color='white'), tickfont=dict(color='white')),
            hovermode='closest',
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='lightgray'),
            shapes=[dict(
                type='line',
                x0=df['timestamp'].min(),
                x1=df['timestamp'].max(),
                y0=threshold,
                y1=threshold,
                line=dict(color='green', width=2, dash='dash'),
                name=f'{sensor.capitalize()} Threshold'
            )],
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',  # Semi-transparent legend
                font=dict(color='white')
            )
        )
    }

    heat_index_value = df['heat_index'].values[-1]
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger (Alarm)"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger (Alarm)"
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution"
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

    sensor_colors = {
        'temperature': 'lightblue',
        'humidity': 'orange',
        'heat_index': 'red',
        'air_quality': 'green'
    }

    for sensor, threshold in THRESHOLDS.items():
        current_value = df[sensor].values[-1]  # Get the latest reading for each sensor
        fig.add_trace(
            go.Bar(
                x=[sensor.capitalize()],
                y=[current_value],
                name=sensor.capitalize(),
                text=f"{current_value}",
                textposition='auto',
                marker=dict(color=sensor_colors.get(sensor, 'lightgray'))  # Match column color to line graph color
            )
        )
        fig.add_shape(
            type='line',
            x0=sensor.capitalize(),
            y0=threshold,
            x1=sensor.capitalize(),
            y1=threshold,
            line=dict(color='green', width=2, dash='dash'),  # Updated threshold line color
        )
    
    fig.update_layout(
        title=dict(text='Current Sensor Readings with Thresholds', font=dict(color='white')),
        yaxis=dict(title='Value', titlefont=dict(color='white'), tickfont=dict(color='white')),
        xaxis=dict(title='Sensor', titlefont=dict(color='white'), tickfont=dict(color='white')),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='lightgray'),
        showlegend=False
    )
    
    return fig, real_time_label, danger_level


# Callback to update the all-data collected graph
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
    figure = go.Figure()
    for i, sensor in enumerate(THRESHOLDS.keys()):
        figure.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[sensor],
            mode='lines+markers',
            name=sensor.capitalize(),
            line=dict(color=f"rgb({100 + i * 40}, {100 + i * 30}, {200 - i * 20})"),
            marker=dict(size=6)
        ))

    # Customize layout
    figure.update_layout(
        title=dict(
            text='All Sensor Data Over Time',
            font=dict(color='white', size=18)
        ),
        xaxis=dict(
            title='Timestamp',
            titlefont=dict(color='white'),
            tickfont=dict(color='white'),
            gridcolor='gray'
        ),
        yaxis=dict(
            title='Value',
            titlefont=dict(color='white'),
            tickfont=dict(color='white'),
            gridcolor='gray'
        ),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        legend=dict(
            title='Sensors',
            font=dict(color='white'),
            bgcolor='rgba(0, 0, 0, 0.5)'
        )
    )

    # Determine the heat index danger level for the current reading
    heat_index_value = df['heat_index'].values[-1]
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

# Callback for radial graphs
@app.callback(
    [Output('radial-progress', 'figure'),
     Output('radial-progress', 'style'),
     Output('radial-real-time', 'children'),
     Output('radial-heat-index-danger-label', 'children')],
    Input('interval-radial-progress', 'n_intervals')
)
def update_radial_progress(n):
    df = fetch_data()
    if df.empty:
        return (
            go.Figure(),
            {'backgroundColor': '#202123', 'padding': '10px', 'borderRadius': '10px'},
            "Real-Time: N/A",
            "Danger Level: N/A"
        )

    current_time = df['timestamp'].values[-1]
    real_time_label = f"Real-Time: {current_time}"

    fig = go.Figure()
    heat_index_value = df['heat_index'].values[-1]
    danger_level = ""

    # Determine danger level
    if heat_index_value >= 125:
        danger_level = "Heat Index Danger Level: Extreme Danger"
    elif heat_index_value >= 103:
        danger_level = "Heat Index Danger Level: Danger"
        radial_style = {
            'backgroundColor': 'red',
            'padding': '10px',
            'borderRadius': '10px'
        }
    elif heat_index_value >= 90:
        danger_level = "Heat Index Danger Level: Extreme Caution"
    elif heat_index_value >= 80:
        danger_level = "Heat Index Danger Level: Caution"
    else:
        danger_level = "Heat Index Danger Level: Normal"
        radial_style = {
            'backgroundColor': '#202123',
            'padding': '10px',
            'borderRadius': '10px'
        }

    # Create the radial progress figure
    for sensor, threshold in THRESHOLDS.items():
        current_value = df[sensor].values[-1]
        max_range = max(threshold * 1.2, current_value * 1.2)

        if sensor == 'temperature':
            red_start = 40
            orange_start = 30
        elif sensor == 'humidity':
            red_start = 80
            orange_start = 70
        elif sensor == 'heat_index':
            red_start = 90
            orange_start = 80
        elif sensor == 'air_quality':
            red_start = 80
            orange_start = 70
        else:
            red_start = threshold
            orange_start = threshold * 0.8

        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_value,
                title={'text': f"{sensor.capitalize()}", 'font': {'color': 'gray'}},
                gauge={
                    'axis': {'range': [0, max_range], 'tickcolor': 'gray'},
                    'bar': {'color': 'grey'},
                    'steps': [
                        {'range': [0, orange_start], 'color': "lightgray"},
                        {'range': [orange_start, red_start], 'color': "orange"},
                        {'range': [red_start, max_range], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': threshold
                    }
                },
                domain={
                    'x': [
                        0.2 * list(THRESHOLDS.keys()).index(sensor),
                        0.2 * (list(THRESHOLDS.keys()).index(sensor) + 1)
                    ],
                    'y': [0, 1]
                }
            )
        )

    fig.update_layout(
        title=dict(
            text='Radial Progress Indicators',
            font=dict(color='white', size=18)
        ),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
    )

    return fig, radial_style, real_time_label, danger_level

@app.callback(
    Output('download-dataframe-csv', 'data'),
    Input('download-button', 'n_clicks'),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    if "download-button" in ctx.triggered_id:
        # Fetch data from the database
        df = fetch_data(limit=50)

        # Convert dataframe to CSV format
        csv_string = io.StringIO()
        df.to_csv(csv_string, index=False)
        csv_string.seek(0)

        # Return CSV as download
        return dict(
            content=csv_string.getvalue(),
            filename="sensor_data.csv"
        )

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
