from math import log2
import numpy as np
import pandas as pd

events_file = 'Events.csv'
entities_file = 'EntityAttributes.csv'
participants_file = 'Participants.sav'

def load_dataset(dataset_name, node_type, edge_type, team, meeting, colour_type, colour_source):
    events, entities, teams, behaviours, participants, meetings = read_files(dataset_name)
    if node_type == 'Behaviours':
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, leader = get_behaviour_node_data(events, team, meeting, participants)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map = get_behaviour_edge_data(edge_type, events, team, meeting)
    else:
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, entity_list, leader = get_participant_node_data(events, entities, team, meeting, participants)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map = get_participant_edge_data(edge_type, events, team, meeting, entity_list)
    colors = get_colors(node_names, behaviours, colour_type)
    selector_node_classes, selector_edge_classes = get_selector_classes(node_names, behaviours, colors, node_size_map, edge_size_map, colour_type)
    node_data, nodes = get_nodes(node_names, acronyms, freq, sizes, selector_node_classes, node_type, leader)
    if node_type == 'Behaviours':
        edges = get_behaviour_edges(edge_data, colour_source)
    else:
        edges = get_participant_edges(edge_data, colour_type, colour_source)
    return teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader

def read_files(dataset_name):
    events = pd.read_csv(dataset_name + '/' + events_file)
    entities = pd.read_csv(dataset_name + '/' + entities_file)
    # Keep only sequenceId, event and entityId columns in events
    events = events[['sequenceId', 'event', 'entityId']]
    # Keep only entityId, ParameterKey and ParameterValue columns in entities
    entities = entities[['entityId', 'ParameterKey', 'ParameterValue']]

    # Get unique teams
    teams = events['sequenceId'].unique()
    teams = [team.split('_')[1] for team in teams]
    teams.append('All')

    # Get unique behaviours
    behaviours = events['event'].unique()
    behaviours = behaviours[behaviours != 'Break']

    # Participants
    if '2017' in dataset_name:
        participants = pd.read_spss(dataset_name + '/' + participants_file)
        participants = participants[['teamid', 'nameinfile', 'leader_meeting']]
    else:
        participants = []

    # Get meetings
    meetings = events['sequenceId'].unique()
    meetings = [meeting.split('_')[0] for meeting in meetings]
    meetings = list(set(meetings))
    meetings.sort()
    meetings.append('All')

    return events, entities, teams, behaviours, participants, meetings

def get_behaviour_node_data(events, team, meeting, participants):
    leader = ''
    if team != 'All':
        # Keep only rows where sequenceId contains team
        events = events[events['sequenceId'].str.split('_').str[1] == team]
        # Keep only rows where meeting is equal to the selected meeting
        if meeting != 'All':
            events = events[events['sequenceId'].str.split('_').str[0] == meeting]
            # Get participants in the selected team
            leader = participants[(participants['teamid'] == team) & (participants['leader_meeting'] == int(meeting))]['nameinfile']
            if len(leader) > 0:
                leader = "Leader: " + ",".join(leader)

    elif meeting != 'All':
        # Keep only rows where meeting is equal to the selected meeting
        events = events[events['sequenceId'].str.split('_').str[0] == meeting]

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
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map, leader

def get_participant_node_data(events, entities, team, meeting, participants_attributes):
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
    # Keep meeting only
    leader = ''
    if meeting != 'All':
        events = events[events['sequenceId'].str.split('_').str[0] == meeting]
        # Get participants in the selected team
        leader = participants_attributes[(participants_attributes['teamid'] == team) & (participants_attributes['leader_meeting'] == int(meeting))][
            'nameinfile']
        if len(leader) > 0:
            leader = "Leader: " + ",".join(leader)

    freq = events['entityId'].value_counts()

    # Replace entityIds with names
    freq.index = entities[entities['entityId'].isin(freq.index)]['ParameterValue']
    sizes = freq.values / 2.0
    sizes = [max(250, size) for size in sizes]
    # Size map
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + ",20,80)"
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map, entities, leader

def get_behaviour_edge_data(edge_type, events, team, meeting):
    if team != 'All':
        # Keep only rows where sequenceId contains team
        events = events[events['sequenceId'].str.split('_').str[1] == team]
        # Keep only rows where meeting is equal to the selected meeting
        if meeting != 'All':
            events = events[events['sequenceId'].str.split('_').str[0] == meeting]
    elif meeting != 'All':
        # Keep only rows where meeting is equal to the selected meeting
        events = events[events['sequenceId'].str.split('_').str[0] == meeting]
    # Get edges
    # From events, count the number of transitions between events. Save in a dictionary
    edges = {}
    # Remove rows with event 'Break'
    events = events[events['event'] != 'Break']
    # Regenerate index
    events = events.reset_index(drop=True)
    for i in range(1, len(events)):
        if (events['event'][i - 1], events['event'][i]) in edges:
            edges[(events['event'][i - 1], events['event'][i])] += 1
        else:
            edges[(events['event'][i - 1], events['event'][i])] = 1
    if edge_type == 'Probability':
        source_sum = {}
        for key, value in edges.items():
            source = key[0]
            if source in source_sum:
                source_sum[source] += value
            else:
                source_sum[source] = value

        for key, value in edges.items():
            source = key[0]
            edges[key] = (value / source_sum[source] * 100)

    weights = list(edges.values())
    min_weight = min(weights)
    max_weight = max(weights)

    # Create 10 bins in the range of min_weight and max_weight
    weight_bins = np.linspace(min_weight, max_weight, 20)
    # Create a dictionary with the bins as keys and the bins as values
    weight_bins = {str(int(bin)): str(int(bin)) for bin in weight_bins}

    # Convert dictionary to a list of 4-tuples
    if edge_type == 'Frequency':
        edge_data = [(key[0], key[1], "", log2(value), value) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + ",1,20)"
    else:
        edge_data = [(key[0], key[1], "", value, int(round((value / 100) * source_sum[key[0]]))) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(min_weight) + "," + str(max_weight) + ",1,20)"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map

def get_participant_edge_data(edge_type, events, team, meeting, entity_list):

    # Get events rows where sequenceId contains team
    events = events[events['sequenceId'].str.split('_').str[1] == team]
    # Remove rows with entityId -1
    events = events[events['entityId'] != -1]
    # Keep meeting only
    if meeting != 'All':
        events = events[events['sequenceId'].str.split('_').str[0] == meeting]
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

    if edge_type == 'Probability':
        source_sum = {}
        for key, value in edges.items():
            source = key[0]
            if source in source_sum:
                source_sum[source] += value
            else:
                source_sum[source] = value

        for key, value in edges.items():
            source = key[0]
            edges[key] = (value / source_sum[source] * 100)

    weights = list(edges.values())
    min_weight = min(weights)
    max_weight = max(weights)

    # Create 10 bins in the range of min_weight and max_weight
    weight_bins = np.linspace(min_weight, max_weight, 20)
    # Create a dictionary with the bins as keys and the bins as values
    weight_bins = {str(int(bin)): str(int(bin)) for bin in weight_bins}

    # Divide weights by max_weight
    #weights = [weight / max_weight for weight in weights]
    # Convert dictionary to a list of 5-tuples
    if edge_type == 'Frequency':
        edge_data = [(key[0], key[1], key[2], log2(value), value) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + ",1,20)"
    else:
        edge_data = [(key[0], key[1], key[2], value, int(round((value / 100) * source_sum[key[0]]))) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(min_weight) + "," + str(max_weight) + ",1,20)"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map

def get_colors(keys, behaviours, colour_type):
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

    # Create a dictionary with keys as node names and values as colors
    if colour_type == "Behaviours":
        colors = dict(zip(behaviours, colors))
    else:
        colors = dict(zip(keys, colors))
    return colors

def get_selector_classes(node_names, behaviours, colors, node_size_map, edge_size_map, colour_type):
    # Create a list of dictionaries with 'selector' and 'style' keys. 'selector' has a value of 'node' and 'style' has a dictionary
    selector_node_classes = []
    selector_edge_classes = []
    names = node_names

    if colour_type == "Behaviours":
        names = behaviours

    selector_node_classes.append(
        {
            'selector': '.nodeParticipant',
            'style': {
                'background-color': "white",
                'line-color': "white",
                'width': node_size_map,
                'height': node_size_map
            }
        }
    )
    selector_node_classes.append(
        {
            'selector': '.nodeLeader',
            'style': {
                'background-color': "white",
                'line-color': "FFFFFF",
                'shape': "star",
                'width': 100,
                'height': 100
            }
        }
    )
    # Iterate over node names
    for i, name in enumerate(names):
        selector_node_classes.append(
            {
                'selector': '.node' + name,
                'style': {
                    'background-color': colors[name],
                    'line-color': colors[name],
                    'width': node_size_map,
                    'height': node_size_map
                }
            }
        )
        selector_edge_classes.append(
            {
                'selector': '.edge' + name,
                'style': {
                    'line-color': colors[name],
                    'target-arrow-color': colors[name],
                    'target-arrow-shape': 'vee',
                    'curve-style': 'bezier',
                    'control-point-step-size': 100,
                    'width': edge_size_map
                }
            }
        )
    return selector_node_classes, selector_edge_classes

def get_nodes(node_names, acronyms, freq, sizes, selector_node_classes, node_type, leader):
    # Create a list of random longitudes and latitudes with the size of the number of acronyms
    longitudes = np.random.uniform(-180, 180, len(acronyms))
    latitudes = np.random.uniform(-90, 90, len(acronyms))
    # Create list of tuples with short name, label, long and lat
    freq_values = freq.tolist()
    node_data = list(zip(node_names, acronyms, freq_values, longitudes, latitudes, sizes, selector_node_classes))
    if node_type == 'Behaviours':
        nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "node" + short
            }
            for short, label, freq, long, lat, size, selector_class in node_data
        ]
    else:
        nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "nodeParticipant"
            }
            for short, label, freq, long, lat, size, selector_class in node_data
        ]
        # Change leader node class
        if leader != '':
            for node in nodes:
                if node['data']['id'] in leader:
                    node['classes'] = "nodeLeader"
    return node_data, nodes

def get_behaviour_edges(edge_data, colour_source):
    if colour_source == "Source":
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight},
                'classes': "edge" + source
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight},
                'classes': "edge" + target
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    return edges

def get_participant_edges(edge_data, colour_type, colour_source):
    if colour_type == 'Behaviours':
        edges = [
            {
                'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                'classes': "edge" + behaviour
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        if colour_source == "Source":
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                    'classes': "edge" + source
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                    'classes': "edge" + target
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
    return edges

def get_original_nodes(node_data, node_type, leader):
    if node_type == 'Behaviours':
        original_nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "node" + short
            }
            for short, label, freq, long, lat, size, selector_class in node_data
        ]
    else:
        original_nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "nodeParticipant"
            }
            for short, label, freq, long, lat, size, selector_class in node_data
        ]
        # Change leader node class
        if leader != '':
            for node in original_nodes:
                if node['data']['id'] in leader:
                    node['classes'] = "nodeLeader"
    return original_nodes

def get_original_edges(edge_data, node_type, colour_type, colour_source):
    if node_type == 'Behaviours':
        if colour_source == "Source":
            original_edges = [
                {
                    'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight},
                    'classes': "edge" + source
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            original_edges = [
                {
                    'data': {'source': source, 'target': target,'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight},
                    'classes': "edge" + target
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
    else:
        if colour_type == 'Behaviours':
            original_edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                    'classes': "edge" + behaviour
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            if colour_source == "Source":
                original_edges = [
                    {
                        'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                        'classes': "edge" + source
                    }
                    for source, target, behaviour, weight, original_weight in edge_data
                ]
            else:
                original_edges = [
                    {
                        'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour},
                        'classes': "edge" + target
                    }
                    for source, target, behaviour, weight, original_weight in edge_data
            ]
    return original_edges

def get_meetings_for_team(database, team):
    events, entities, teams, behaviours, leader, meetings = read_files(database)
    meetings = ['All']

    if team != 'All':
        # Iterate through events
        for index, event in events.iterrows():
            if event['sequenceId'].split('_')[1] == team:
                meetings.append(event['sequenceId'].split('_')[0])
        meetings = list(set(meetings))
        meetings.sort()

    else:
        meetings = events['sequenceId'].unique()
        meetings = [meeting.split('_')[0] for meeting in meetings]
        meetings = list(set(meetings))
        meetings.sort()
        meetings.append('All')

    options = [
        {'label': name.capitalize(), 'value': name}
        for name in meetings
    ]
    return options

def check_valid_options(node_type, colour_type, team):
    if node_type == 'Behaviours':
        if colour_type == 'Behaviours':
            return True
    else:
        if team == 'All':
            return False
        return True