from math import log10, log, log2
import numpy as np
import pandas as pd

events_file = 'Events.csv'
entities_file = 'EntityAttributes.csv'

def load_dataset(dataset_name, node_type):
    events, entities = read_files(dataset_name)
    if node_type == 'Behaviours':
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map = get_behaviour_node_data(events)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map = get_behaviour_edge_data(events)
    else:
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, team, entity_list = get_participant_node_data(events, entities)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map = get_participant_edge_data(events, team, entity_list)
    colors = get_colors(len(node_names))
    selector_node_classes, selector_edge_classes = get_selector_classes(node_names, colors, node_size_map, edge_size_map)
    node_data, nodes = get_nodes(node_names, acronyms, freq, sizes, selector_node_classes)
    if node_type == 'Behaviours':
        edges = get_behaviour_edges(edge_data)
    else:
        edges = get_participant_edges(edge_data)
    return node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins

def read_files(dataset_name):
    events = pd.read_csv(dataset_name + '/' + events_file)
    entities = pd.read_csv(dataset_name + '/' + entities_file)
    # Keep only sequenceId, event and entityId columns in events
    events = events[['sequenceId', 'event', 'entityId']]
    # Keep only entityId, ParameterKey and ParameterValue columns in entities
    entities = entities[['entityId', 'ParameterKey', 'ParameterValue']]
    return events, entities

def get_behaviour_node_data(events):
    # Get node names
    node_names = events['event'].unique()
    node_names = node_names[node_names != 'Break']

    # Get acronyms
    acronyms = [event.replace('_', ' ') for event in node_names]
    acronyms = ["".join([word[0] for word in event.split()]) for event in acronyms]
    acronyms = [name.upper() for name in acronyms]
    acronyms = list(acronyms)

    # Create a dictionary with node names as keys and acronyms as values
    acronyms_dict = dict(zip(node_names, acronyms))

    # Get frequency of events
    freq = events['event'].value_counts()
    # If 'Break' is in freq, remove it
    if 'Break' in freq:
        freq = freq.drop('Break')
    # Sort freq in the same order as node_names
    freq = freq[node_names]
    sizes = freq.values / 2.0
    sizes = [max(250, size) for size in sizes]
    # Size map
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + ",20,80)"
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map

def get_participant_node_data(events, entities):
    # Get unique teams
    teams = events['sequenceId'].unique()
    teams = [team.split('_')[1] for team in teams]
    team = teams[0]

    # Get entityIds of participants in the team.
    # Keep only rows where sequenceId split by '_' is equal to team
    entityIds = events[events['sequenceId'].str.split('_').str[1] == team]['entityId'].unique()

    # Remove -1 from entityIds
    entityIds = entityIds[entityIds != -1]
    # Keep only rows where ParameterKey is 'Name'
    entities = entities[entities['ParameterKey'] == 'name']
    # Keep only rows where entityId is in entityIds
    entities = entities[entities['entityId'].isin(entityIds)]
    # Get names of participants
    participants = entities['ParameterValue'].unique()

    # Get node names
    node_names = participants

    # Get acronyms
    acronyms = participants

    # Create a dictionary with node names as keys and acronyms as values
    acronyms_dict = dict(zip(node_names, acronyms))

    # Get frequency of participants
    # Keep events where entityId is in entityIds
    events = events[events['entityId'].isin(entityIds)]

    freq = events['entityId'].value_counts()

    # Replace entityIds with names
    freq.index = entities[entities['entityId'].isin(freq.index)]['ParameterValue']
    sizes = freq.values / 2.0
    sizes = [max(250, size) for size in sizes]
    # Size map
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + ",20,80)"
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map, team, entities

def get_behaviour_edge_data(events):
    # Get edges
    # From events, count the number of transitions between events. Save in a dictionary
    edges = {}
    for i in range(1, len(events)):
        if events['event'][i] != 'Break' and events['event'][i - 1] != 'Break':
            if (events['event'][i - 1], events['event'][i]) in edges:
                edges[(events['event'][i - 1], events['event'][i])] += 1
            else:
                edges[(events['event'][i - 1], events['event'][i])] = 1
    weights = list(edges.values())
    min_weight = min(weights)
    max_weight = max(weights)

    # Create 10 bins in the range of min_weight and max_weight
    weight_bins = np.linspace(min_weight, max_weight, 20)
    # Create a dictionary with the bins as keys and the bins as values
    weight_bins = {str(int(bin)): str(int(bin)) for bin in weight_bins}

    # Divide weights by max_weight
    #weights = [weight / max_weight for weight in weights]
    # Convert dictionary to a list of 4-tuples
    edge_data = [(key[0], key[1], log2(value), value) for key, value in edges.items()]
    edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + ",1,20)"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map

def get_participant_edge_data(events, team, entity_list):
    # Get unique teams
    teams = events['sequenceId'].unique()
    teams = [team.split('_')[1] for team in teams]
    team = teams[0]

    # Get events rows where sequenceId contains team
    events = events[events['sequenceId'].str.split('_').str[1] == team]
    # Remove rows with entityId -1
    events = events[events['entityId'] != -1]
    # Regenerate index
    events = events.reset_index(drop=True)
    # Replace each entityId with the name of the participant
    events['entityId'] = events['entityId'].replace(entity_list.set_index('entityId')['ParameterValue'])

    # Get edges
    # From events, count the number of transitions between entityIds, including the event transition. Save in a dictionary (entityId1, entityId2, event): count
    edges = {}
    for i in range(1, len(events)):
        if (events['entityId'][i - 1], events['entityId'][i], events['event'][i]) in edges:
            edges[(events['entityId'][i - 1], events['entityId'][i], events['event'][i])] += 1
        else:
            edges[(events['entityId'][i - 1], events['entityId'][i], events['event'][i])] = 1


    weights = list(edges.values())
    min_weight = min(weights)
    max_weight = max(weights)

    # Create 10 bins in the range of min_weight and max_weight
    weight_bins = np.linspace(min_weight, max_weight, 20)
    # Create a dictionary with the bins as keys and the bins as values
    weight_bins = {str(int(bin)): str(int(bin)) for bin in weight_bins}

    # Divide weights by max_weight
    #weights = [weight / max_weight for weight in weights]
    # Convert dictionary to a list of 4-tuples
    edge_data = [(key[0], key[1], key[2], log2(value), value) for key, value in edges.items()]
    edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + ",1,20)"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map

def get_colors(length):
    # List of colors in rgb format
    colors = [(0.0, 1.0, 0.0), (0.9943259034408901, 0.0012842177138555622, 0.9174329074599924),
              (0.0, 0.5, 1.0), (1.0, 0.5, 0.0), (0.5, 0.75, 0.5),
              (0.38539888501730646, 0.13504094033721226, 0.6030566783362241),
              (0.2274309309202145, 0.9916143649051387, 0.9940075760357668), (1.0, 0.0, 0.0),
              (0.19635097896407006, 0.5009447066269282, 0.02520413500628782), (1.0, 1.0, 0.0), (1.0, 0.5, 1.0),
              (0.0, 0.0, 1.0), (0.0, 0.5, 0.5),
              (0.9080663741715954, 0.24507985021755374, 0.45946418737627126),
              (0.5419953696803366, 0.17214943372398184, 0.041558678566627205),
              (0.9851725449490569, 0.7473699550058078, 0.4530441265365358),
              (0.5307859786313746, 0.9399885275455782, 0.05504161834032317)]

    # Change color array to format accepted by pyvis
    colors = ['#%02x%02x%02x' % (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)) for color in colors]
    # Grab only colors for the number of acronyms
    colors = colors[:length]
    return colors

def get_selector_classes(node_names, colors, node_size_map, edge_size_map):
    # Create a list of dictionaries with 'selector' and 'style' keys. 'selector' has a value of 'node' and 'style' has a dictionary
    selector_node_classes = []
    selector_edge_classes = []
    for i, color in enumerate(colors):
        selector_node_classes.append(
            {
                'selector': '.node' + node_names[i],
                'style': {
                    'background-color': color,
                    'line-color': color,
                    'width': node_size_map,
                    'height': node_size_map
                }
            }
        )
        selector_edge_classes.append(
            {
                'selector': '.edge' + node_names[i],
                'style': {
                    'line-color': color,
                    'target-arrow-color': color,
                    'target-arrow-shape': 'vee',
                    'curve-style': 'bezier',
                    'control-point-step-size': 100,
                    'width': edge_size_map
                }
            }
        )
    return selector_node_classes, selector_edge_classes

def get_nodes(node_names, acronyms, freq, sizes, selector_node_classes):
    # Create a list of random longitudes and latitudes with the size of the number of acronyms
    longitudes = np.random.uniform(-180, 180, len(acronyms))
    latitudes = np.random.uniform(-90, 90, len(acronyms))
    # Create list of tuples with short name, label, long and lat
    freq_values = freq.tolist()
    node_data = list(zip(node_names, acronyms, freq_values, longitudes, latitudes, sizes, selector_node_classes))
    nodes = [
        {
            'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
            'position': {'x': 20 * lat, 'y': -20 * long},
            'classes': selector_class['selector'][1:]
        }
        for short, label, freq, long, lat, size, selector_class in node_data
    ]
    return node_data, nodes

def get_behaviour_edges(edge_data):
    edges = [
        {
            'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight},
            'classes': "edge" + source
        }
        for source, target, weight, original_weight in edge_data
    ]
    return edges

def get_participant_edges(edge_data):
    edges = [
        {
            'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
            'classes': "edge" + source
        }
        for source, target, behaviour, weight, original_weight in edge_data
    ]
    return edges

def get_original_nodes(node_data):
    original_nodes = [
        {
            'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
            'position': {'x': 20 * lat, 'y': -20 * long},
            'classes': selector_class['selector'][1:]
        }
        for short, label, freq, long, lat, size, selector_class in node_data
    ]
    return original_nodes

def get_original_edges(edge_data, node_type):
    if node_type == 'Behaviours':
        original_edges = [
            {
                'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight},
                'classes': "edge" + source
            }
            for source, target, weight, original_weight in edge_data
        ]
    else:
        original_edges = [
            {
                'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                'classes': "edge" + source
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    return original_edges