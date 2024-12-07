from dash import Dash, html, Input, Output, callback, dcc, ctx
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from functions import *

database = 'GEC2017'
node_type = 'Behaviours'
edge_type = 'Frequency'
team = 'All'
meeting = 'All'
colour_type = 'Behaviours'
colour_source = 'Source'
team_compare = 'All'
meeting_compare = 'All'


teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader, node_names, behaviours, node_stats, edge_stats = load_dataset(database, node_type, edge_type, team, meeting, colour_type, colour_source)
legend_nodes = get_legend_nodes(node_names, selector_node_classes, colour_type, behaviours)

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

default_stylesheet = [
    # Group selectors for nodes
    {
        'selector': 'node',
        'style': {
            #'background-color': '#00000',
            'label': 'data(label)',
            'font-size': '20px',
            'text-halign':'center',
            'text-valign':'center'
        },
    },
        {
            'selector': 'label',
            'style': {
                'content': 'data(label)',
                'color': 'white',
            }
        }
]

legend_stylesheet = [
    # Group selectors for nodes
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'font-size': '20px',
            'text-halign': 'right',
            'text-valign': 'center'
        }
    },
    {
        'selector': 'label',
        'style': {
            'content': 'data(label)',
            'color': 'white',
            'text-margin-x': '10px',
        }
    },

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
        style={'width': '200px'},
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'},
)

database_dropdown_compare = html.Div([
    html.P("Database: "),
    dcc.Dropdown(
        id='dropdown-update-database-compare',
        value='GEC2017',
        clearable=False,
        options=[
        {'label': name, 'value': name}
        for name in ['GEC2017', 'GEC2018', 'EYH2017', 'EYH2018', 'IDP2019', 'IDP2020']
        ],
        className='dash-bootstrap',
        style={'width': '200px'},
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
        style={'width': '200px'},
        className='dash-bootstrap'
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'}
)

meeting_dropdown = html.Div([
    html.P("Meeting:"),
    dcc.Dropdown(
        id = 'dropdown-update-meeting',
        value='All',
        clearable=False,
        options=[
            {'label': name, 'value': name}
            for name in meetings
        ],
        style={'width': '200px'},
        className='dash-bootstrap'
    )],
    style = {'display': 'inline-block', 'margin-left': '20px'}
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
        style={'width': '200px'},
        className='dash-bootstrap'
    )
], style = {'display': 'inline-block', 'margin-left': '20px'})

node_type_radio = html.Div([html.P("Node type:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Behaviours', 'Participants'], id='radio-update-nodes', value='Behaviours', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

edge_type_radio = html.Div([html.P("Edge weight:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Frequency', 'Probability'], id='radio-update-edges', value='Frequency', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

colour_type_radio = html.Div([html.P("Colour by:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Behaviours', 'Participants'], id='radio-update-colour_type', value='Behaviours', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

colour_source_radio = html.Div([html.P("Colour by:", style = {'display': 'inline-block'}),
    html.Div(dcc.RadioItems(['Source', 'Target'], id='radio-update-colour-source', value='Source', inline=True, inputStyle={'margin-right': '10px', 'margin-left': '10px'}), style={'display': 'inline-block'})
], style={'margin-left': '20px', 'margin-top': '20px', 'display': 'inline-block'})

update_button = html.Div([
    dbc.Button("Update", id='update-button', color="primary", className="mr-1", style = {'margin-left': '20px'})
], style = {'display': 'inline-block'})

options_div = html.Div([node_type_radio, edge_type_radio, colour_type_radio, colour_source_radio, update_button])

graph = html.Div([cyto.Cytoscape(
        id='BiT',
        layout={'name': 'circle',
                'radius': 200},
        elements = edges+nodes,
        stylesheet = selector_node_classes + selector_edge_classes + default_stylesheet,
        style={'width': '80%', 'height': '780px', 'display': 'inline-block'},
    ),cyto.Cytoscape(id='BiT2',
        layout={'name': 'grid', 'columns': 1},
        elements = legend_nodes,
        stylesheet = selector_node_classes + legend_stylesheet,
        style={'width': '20%', 'height': '780px', 'display': 'inline-block'},)
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

graph_tab = html.Div([database_dropdown, layout_dropdown, team_dropdown, meeting_dropdown, options_div, graph, weight_slider, tooltip])

app.layout = graph_tab

@callback(
        Output('tooltip', 'children'),
        [Input('BiT', 'mouseoverNodeData'),
        Input('BiT', 'mouseoverEdgeData')])
def mouseover_node_data(hover_node_data, hover_edge_data):
    if hover_node_data or hover_edge_data:
        component = list(ctx.triggered_prop_ids.keys())[0]
        text_input = ""
        if 'Node' in component:
            text_input = 'Node'
        if 'Edge' in component:
            text_input = 'Edge'
        if text_input == 'Node':
            return hover_node_data['id'] + ", with frequency: " + str(hover_node_data['freq']) + " " + hover_node_data['stats']
        elif text_input == 'Edge':
            if node_type == 'Behaviours':
                if edge_type == 'Frequency':
                    return hover_edge_data['source'].upper() + " -> " + hover_edge_data['target'].upper() + ": " + str(hover_edge_data['original_weight']) + " " + hover_edge_data['stats']
                else:
                    return hover_edge_data['source'].upper() + " -> " + hover_edge_data['target'].upper() + ": " + str(hover_edge_data['original_weight']) + " (" + str(round(hover_edge_data['weight'], 2)) + "%)" + " " + hover_edge_data['stats']
            else:
                if edge_type == 'Frequency':
                    return hover_edge_data['source'] + " -> " + hover_edge_data['target'] + ", " + hover_edge_data['behaviour'] + ": " + str(hover_edge_data['original_weight']) + " " + hover_edge_data['stats']
                else:
                    return hover_edge_data['source'] + " -> " + hover_edge_data['target'] + ", " + hover_edge_data['behaviour'] + ": " + str(hover_edge_data['original_weight']) + " (" + str(hover_edge_data['weight']) + "%)" + " " + hover_edge_data['stats']


@callback(Output('BiT', 'elements', allow_duplicate=True),
            Input('BiT', 'selectedNodeData'), prevent_initial_call=True)
def select_node(selected_nodes):
    if len(selected_nodes) == 0:
        return get_original_edges(edge_data, node_type, colour_type, colour_source, edge_stats) + get_original_nodes(node_data, node_type, leader, colour_type, node_stats)
    else:
        current_edges = []
        for node in selected_nodes:
            for edge in get_original_edges(edge_data, node_type, colour_type, colour_source, edge_stats):
                if colour_source == 'Source':
                    if edge['data']['source'] == node['id']:
                        current_edges.append(edge)
                else:
                    if edge['data']['target'] == node['id']:
                        current_edges.append(edge)
        return current_edges + get_original_nodes(node_data, node_type, leader, colour_type, node_stats)

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
    global nodes, edges
    if selected_weight == min_weight:
        nodes = get_original_nodes(node_data, node_type, leader, colour_type, node_stats)
        edges = get_original_edges(edge_data, node_type, colour_type, colour_source, edge_stats)
        return edges + nodes, "Weight threshold: " + str(selected_weight)
    else:
        # Remove edges with weight less than selected_weight
        current_edges = []
        for edge in get_original_edges(edge_data, node_type, colour_type, colour_source, edge_stats):
            if edge_type == 'Probability':
                if selected_weight[0] <= edge['data']['weight'] <= selected_weight[1]:
                    current_edges.append(edge)
            else:
                if log2(selected_weight[0]) <= edge['data']['weight'] <= log2(selected_weight[1]):
                    current_edges.append(edge)
        nodes = get_original_nodes(node_data, node_type, leader, colour_type, node_stats)
        edges = current_edges
        # Format selected_weight to display only 2 decimal places
        return edges + nodes, "Weight threshold: " + str(round(selected_weight[0], 2)) + " - " + str(round(selected_weight[1], 2))

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
    Input('dropdown-update-team', 'value'), prevent_initial_call=True)
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
           Output('BiT2', 'elements', allow_duplicate=True),
           Output('BiT2', 'stylesheet'),],
            Input('update-button', 'n_clicks'),
            prevent_initial_call=True)
def update_graph_with_button(n_clicks):
    global teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader, node_names, behaviours, node_stats, edge_stats
    valid = check_valid_options(node_type, colour_type, team)
    if valid:
        teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader, node_names, behaviours, node_stats, edge_stats = load_dataset(
        database, node_type, edge_type, team, meeting, colour_type, colour_source)
        return edges + nodes, selector_node_classes + selector_edge_classes + default_stylesheet, min_weight, max_weight, weight_bins, [min_weight, max_weight], get_legend_nodes(node_names, selector_node_classes, colour_type, behaviours), selector_node_classes + legend_stylesheet
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run(debug=True)
