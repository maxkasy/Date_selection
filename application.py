import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd
from google.cloud import storage

# Instantiate a Google Cloud Storage client
client = storage.Client.create_anonymous_client()
# The name of our bucket
bucket_name = 'date_selection_data'
# Get the bucket
bucket = client.bucket(bucket_name)
# The name of our spreadsheet
file_name = 'date_time_test.csv'

def load_data():    
    # Reading DataFrame from the bucket
    df = pd.read_csv(f'gs://{bucket_name}/{file_name}')
    # Filter for rows where name is missing, but date is not missing
    df = df[df['Name'].isna() & df['Date'].notna()]

    return df['Date']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = "Seminar date selection, Oxford econometrics seminar"
server = app.server

app.layout = html.Div([
    html.H1('Select a seminar date', className='text-center mb-4'),
    html.Hr(className='mb-4'),
    html.Div([
        dcc.Input(id='name-input', type='text', placeholder='Enter your name', className='mb-4'),
        html.Br(),
        html.Label('Available dates:', className='mb-2', id='dates-label'),
        html.Br(),
        dcc.RadioItems(id='date-radioitems', className='mb-4'),
    ], id='input-group'),
    html.Div(id='thank-you-message', className='mb-4'),  # New Div for the thank you message
    html.Hr(className='mb-4'),
    html.Button('Submit', id='submit-button', n_clicks=0),
], style={'margin': '20%', 'textAlign': 'center'}, id='app-layout')

@app.callback(
    Output('date-radioitems', 'options'),
    Output('date-radioitems', 'value'),
    Input('app-layout', 'children')
)
def update_options(n):
    df = load_data()
    options = [{'label': " " + i, 'value': i} for i in df]
    value = df.iloc[0] if len(df) > 0 else None
    return options, value

@app.callback(
    [Output('submit-button', 'style'),
     Output('input-group', 'style'),
     Output('thank-you-message', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('date-radioitems', 'value'),
     State('name-input', 'value')]
)
def update_sheet(n_clicks, selected_date, entered_name):
    if n_clicks > 0:
        # Reading DataFrame from the bucket
        df = pd.read_csv(f'gs://{bucket_name}/{file_name}')
        # Find the row to update
        row_index = df[df['Date'] == selected_date].index[0]
        # Update the 'Name' column in the found row
        df.loc[row_index, 'Name'] = entered_name
        # Write csv to bucket
        df.to_csv(f'gs://{bucket_name}/{file_name}', index=False)
        # Hide the input, radio items, and submit button, and show the thank you message
        return {'display': 'none'}, {'display': 'none'}, 'Thank you for your selection!'
    else:
        # If the submit button has not been clicked, show the input, radio items, and submit button, and hide the thank you message
        return {}, {}, ''

if __name__ == '__main__':
    app.run_server(debug=True)