import numpy as np
from dash import Dash, html, Input, Output, callback, dcc, ctx
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc

from data_handler import *

database = 'GEC2017'
node_type = 'Behaviours'

node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins = load_dataset(database, node_type)


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
    # Group selectors for edges
    # {
    #     'selector': 'edge',
    #     'style': {
    #         'line-color': '#000000'
    #     }
    # }

]

app.layout = html.Div(
    children = [
        html.P("Database: "),
        dcc.Dropdown(
            id='dropdown-update-database',
            value='GEC2017',
            clearable=False,
            options=[
                {'label': name, 'value': name}
                for name in ['GEC2017', 'GEC2018', 'EYH2017', 'EYH2018', 'IDP2019', 'IDP2020']
            ],
            style={'width': '300px'},
            className='dash-bootstrap'
        ),
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
        ),
        #dcc.RadioItems(['Behaviours', ' Participants'], id='radio-update-nodes', value='Behaviours', inline=True),
        cyto.Cytoscape(
            id='BiT',
            layout={'name': 'circle',
                    'radius': 200},
            elements = edges+nodes,
            stylesheet = selector_node_classes + selector_edge_classes + default_stylesheet,
            style={'width': '100%', 'height': '750px'},
        ),
        html.P("Weight threshold", id='weight-slider-output'),
        dcc.RangeSlider(
            min = min_weight,
            max = max_weight,
            step = 1,
            value = [min_weight, max_weight],
            marks = weight_bins,
            allowCross = False,
            id = 'weight-slider'
        ),
        html.P(id='tooltip')
    ]
)

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

@callback(Output('BiT', 'layout'),
              Input('dropdown-update-layout', 'value'))
def update_layout(layout):
    return {
        'name': layout,
        #'animate': True
    }

@callback([Output('BiT', 'elements', allow_duplicate=True),
            Output('BiT', 'stylesheet'),
            Output('weight-slider', 'min'),
            Output('weight-slider', 'max'),
            Output('weight-slider', 'marks'),
            Output('weight-slider', 'value')],
                Input('dropdown-update-database', 'value'),
          prevent_initial_call=True)
def update_database(database):
    global node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins
    node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins = load_dataset(database, node_type)
    return edges + nodes, selector_node_classes + selector_edge_classes + default_stylesheet, min_weight, max_weight, weight_bins, [min_weight, max_weight]

@callback(
    [Output('BiT', 'elements'),
    Output('weight-slider-output', 'children')],
    Input('weight-slider', 'value'))
def update_graph(selected_weight):
    if selected_weight == min_weight:
        return get_original_edges(edge_data, node_type) + get_original_nodes(node_data), "Weight threshold: " + str(selected_weight)
    else:
        # Remove edges with weight less than selected_weight
        current_edges = []
        for edge in get_original_edges(edge_data, node_type):
            if log2(selected_weight[0]) <= edge['data']['weight'] <= log2(selected_weight[1]):
                current_edges.append(edge)
        return current_edges + get_original_nodes(node_data), "Weight threshold: " + str(selected_weight[0]) + " - " + str(selected_weight[1])

if __name__ == '__main__':
    app.run(debug=True)
