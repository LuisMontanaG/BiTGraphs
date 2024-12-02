from dash import Dash, html, Input, Output, callback, dcc, ctx
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from data_handler import *

database = 'GEC2017'
node_type = 'Behaviours'
edge_type = 'Frequency'
team = 'All'
meeting = 'All'
colour_type = 'Behaviours'
colour_source = 'Source'

teams, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader = load_dataset(database, node_type, edge_type, team, meeting, colour_type, colour_source)

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

default_stylesheet = [
    # Group selectors for nodes
    {
        'selector': 'node',
        'style': {
            'background-color': '#00000',
            'label': 'data(label)',
            'font-size': '20px',
            'text-halign':'center',
            'text-valign':'center'
        }
    }
]

database_dropdown = html.Div([
    html.P("Database: "),
    dcc.Dropdown(
        id='dropdown-update-database',
        value='GEC2017',
        clearable=False,
        options=[
        {'label': name, 'value': name}
        for name in ['GEC2017', 'GEC2018', 'EYH2017', 'EYH2018', 'IDP2019', 'IDP2020']
        ],
        className='dash-bootstrap',
        style={'width': '300px'},
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'},
)

team_dropdown = html.Div([
    html.P("Team:"),
    dcc.Dropdown(
        id = 'dropdown-update-team',
        value='All',
        clearable=False,
        options=[
            {'label': name, 'value': name}
            for name in teams
        ],
        style={'width': '300px'},
        className='dash-bootstrap'
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'},
    id='div-update-team'
)

meeting_dropdown = html.Div([
    html.P("Meeting:"),
    dcc.Dropdown(
        id = 'dropdown-update-meeting',
        #value='All',
        clearable=False,
        # options=[
        #     {'label': name, 'value': name}
        #     for name in (['All'],)
        # ],
        options=[],
        style={'width': '300px'},
        className='dash-bootstrap'
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'},
    id='div-update-meeting'
)

layout_dropdown = html.Div([
    html.P("Layout:"),
    dcc.Dropdown(
        id='dropdown-update-layout',
        value='grid',
        clearable=False,
        options=[
            {'label': name.capitalize(), 'value': name}
            for name in ['grid', 'random', 'circle', 'cose', 'concentric']
        ],
        style={'width': '300px'},
        className='dash-bootstrap'
    )
], style={'margin-left': '20px', 'margin-top': '10px'})

node_type_radio = html.Div([html.P("Node type:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Behaviours', 'Participants'], id='radio-update-nodes', value='Behaviours', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

edge_type_radio = html.Div([html.P("Edge weight:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Frequency', 'Probability'], id='radio-update-edges', value='Frequency', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

colour_type_radio = html.Div([html.P("Colours:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Behaviours', 'Participants'], id='radio-update-colour_type', value='Behaviours', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

colour_source_radio = html.Div([html.P("Colours:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Source', 'Target'], id='radio-update-colour-source', value='Source', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

update_button = html.Div([
    dbc.Button("Update", id='update-button', color="primary", className="mr-1", style = {'margin-left': '20px'})
], style = {'display': 'inline-block'})

options_div = html.Div([node_type_radio, edge_type_radio, colour_type_radio, colour_source_radio, update_button])

graph = html.Div([
    cyto.Cytoscape(
        id='BiT',
        layout={'name': 'circle',
                'radius': 200},
        elements = edges+nodes,
        stylesheet = selector_node_classes + selector_edge_classes + default_stylesheet,
        style={'width': '100%', 'height': '950px'},
    )
])

weight_slider = html.Div([
    html.P("Weight threshold", id='weight-slider-output', style={'margin-left': '20px'}),
    dcc.RangeSlider(
        min = min_weight,
        max = max_weight,
        step = 1,
        value = [min_weight, max_weight],
        marks = weight_bins,
        allowCross = False,
        id = 'weight-slider'
    )
])

tooltip = html.Div([
    html.P(id='tooltip')
], style={'margin-left': '10px'})

leader = html.Div([
    html.P(id='leader')], style={'margin-left': '10px', 'display': 'inline-block'})

app.layout = html.Div([database_dropdown, team_dropdown, meeting_dropdown, leader, options_div, layout_dropdown, graph, weight_slider, tooltip])

@callback(
        Output('tooltip', 'children'),
        [Input('BiT', 'mouseoverNodeData'),
        Input('BiT', 'mouseoverEdgeData')])
def mouseoverNodeData(node_data, edge_data):
    if node_data or edge_data:
        component = list(ctx.triggered_prop_ids.keys())[0]
        input = ""
        if 'Node' in component:
            input = 'Node'
        if 'Edge' in component:
            input = 'Edge'
        if input == 'Node':
            return node_data['id'] + ", with frequency: " + str(node_data['freq'])
        elif input == 'Edge':
            if node_type == 'Behaviours':
                return edge_data['source'].upper() + " -> " + edge_data['target'].upper() + ": " + str(edge_data['original_weight'])
            else:
                return edge_data['source'] + " -> " + edge_data['target'] + ", " + edge_data['behaviour'] + ": " + str(edge_data['original_weight'])

@callback(Output('BiT', 'elements', allow_duplicate=True),
            Input('BiT', 'selectedNodeData'), prevent_initial_call=True)
def select_node(selected_nodes):
    if len(selected_nodes) == 0:
        return get_original_edges(edge_data, node_type, colour_type, colour_source) + get_original_nodes(node_data)
    else:
        current_edges = []
        for node in selected_nodes:
            for edge in get_original_edges(edge_data, node_type, colour_type, colour_source):
                if colour_source == 'Source':
                    if edge['data']['source'] == node['id']:
                        current_edges.append(edge)
                else:
                    if edge['data']['target'] == node['id']:
                        current_edges.append(edge)
        return current_edges + get_original_nodes(node_data)

@callback(Output('BiT', 'layout'),
              Input('dropdown-update-layout', 'value'))
def update_layout(layout):
    return {
        'name': layout,
        #'animate': True
    }

@callback(Input('dropdown-update-database', 'value'),prevent_initial_call=True)
def update_database(value):
    global database
    database = value

@callback(
    [Output('BiT', 'elements'),
    Output('weight-slider-output', 'children')],
    Input('weight-slider', 'value'))
def update_graph(selected_weight):
    if selected_weight == min_weight:
        return get_original_edges(edge_data, node_type, colour_type, colour_source) + get_original_nodes(node_data), "Weight threshold: " + str(selected_weight)
    else:
        # Remove edges with weight less than selected_weight
        current_edges = []
        for edge in get_original_edges(edge_data, node_type, colour_type, colour_source):
            if edge_type == 'Probability':
                if selected_weight[0] <= edge['data']['weight'] <= selected_weight[1]:
                    current_edges.append(edge)
            else:
                if log2(selected_weight[0]) <= edge['data']['weight'] <= log2(selected_weight[1]):
                    current_edges.append(edge)
        return current_edges + get_original_nodes(node_data), "Weight threshold: " + str(selected_weight[0]) + " - " + str(selected_weight[1])

@callback(Input('radio-update-nodes', 'value'),
    prevent_initial_call=True)
def update_team(value):
    global node_type
    node_type = value

@callback(Input('radio-update-edges', 'value'),
    prevent_initial_call=True)
def update_edge_weight(value):
    global edge_type
    edge_type = value

@callback(Input('radio-update-colour_type', 'value'),
    prevent_initial_call=True)
def update_colour_type(value):
    global colour_type
    colour_type = value

@callback(Input('radio-update-colour-source', 'value'),
    prevent_initial_call=True)
def update_colour_source(value):
    global colour_source
    colour_source = value

@callback(
    [Output('dropdown-update-meeting', 'options')],
    Input('dropdown-update-team', 'value'))
def update_meeting_display(value):
    if value != '':
        global team
        team = value
        return [get_meetings_for_team(database, value)]
    else:
        return [[]]

@callback(Input('dropdown-update-meeting', 'value'), prevent_initial_call=True)
def update_graph_with_meeting(value):
    global meeting
    if value is not None:
        meeting = value

@callback([Output('BiT', 'elements', allow_duplicate=True),
             Output('BiT', 'stylesheet'),
             Output('weight-slider', 'min'),
             Output('weight-slider', 'max'),
             Output('weight-slider', 'marks'),
             Output('weight-slider', 'value'),
             Output('leader', 'children')],
            Input('update-button', 'n_clicks'),
            prevent_initial_call=True)
def update_graph_with_button(n_clicks):
    global teams, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader
    valid = check_valid_options(node_type, colour_type, team)
    if valid:
        teams, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader = load_dataset(
        database, node_type, edge_type, team, meeting, colour_type, colour_source)
        return edges + nodes, selector_node_classes + selector_edge_classes + default_stylesheet, min_weight, max_weight, weight_bins, [min_weight, max_weight], leader
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run(debug=True)
