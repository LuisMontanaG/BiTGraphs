from math import log2
import numpy as np
import pandas as pd

NODE_MAP_MIN_SIZE = 40
NODE_MAP_MAX_SIZE = 150
EDGE_MAP_MIN_SIZE = 1
EDGE_MAP_MAX_SIZE = 20

events_file = 'Events.csv'
entities_file = 'EntityAttributes.csv'
participants_file = 'Participants.sav'

def load_dataset(dataset_name, node_type, edge_type, team, meeting, colour_type, colour_source, graph_type):
    events, entities, teams, behaviours, participants, meetings = read_files(dataset_name)
    if node_type == 'Behaviours':
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, leader, node_stats = get_behaviour_node_data(events, teams, team, meeting, participants, graph_type)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_behaviour_edge_data(edge_type, teams, events, team, meeting, graph_type)
    else:
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, entity_list, leader, node_stats = get_participant_node_data(events, entities, team, meeting, participants)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_participant_edge_data(edge_type, events, team, meeting, entity_list)
    colors = get_colors(node_names, behaviours, colour_type)
    selector_node_classes, selector_edge_classes = get_selector_classes(node_names, behaviours, colors, node_size_map, edge_size_map, colour_type)
    node_data, nodes = get_nodes(node_names, acronyms, freq, sizes, node_type, leader, colour_type, node_stats)
    if node_type == 'Behaviours':
        edges = get_behaviour_edges(edge_data, colour_source, edge_stats)
    else:
        edges = get_participant_edges(edge_data, colour_type, colour_source)
    return teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader, node_names, behaviours, node_stats, edge_stats

def load_dataset_comparison(database, node_type, edge_type, team, meeting, team_compare, meeting_compare, colour_type, colour_source, graph_type):
    events, entities, teams, behaviours, participants, meetings = read_files(database)
    node_data_list = []
    edge_data_list = []
    if node_type == 'Behaviours':
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, leader, node_stats = get_behaviour_node_data(events, teams, team, meeting, participants, graph_type)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_behaviour_edge_data(edge_type, teams, events, team, meeting, graph_type)
        node_data_list.append((node_names, freq))
        edge_data_list.append(edge_data)
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, leader, node_stats = get_behaviour_node_data(events, teams, team_compare, meeting_compare, participants, graph_type)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_behaviour_edge_data(edge_type, teams, events, team_compare, meeting_compare, graph_type)
        node_data_list.append((node_names, freq))
        edge_data_list.append(edge_data)
    else:
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, entity_list, leader, node_stats = get_participant_node_data(events, entities, team, meeting, participants)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_participant_edge_data(edge_type, events, team, meeting, entity_list)
        node_data_list.append((node_names, freq))
        edge_data_list.append(edge_data)
        node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, entity_list, leader, node_stats = get_participant_node_data(events, entities, team_compare, meeting_compare, participants)
        edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_stats = get_participant_edge_data(edge_type, events, team_compare, meeting_compare, entity_list)
        node_data_list.append((node_names, freq))
        edge_data_list.append(edge_data)
    node_names, acronyms, acronyms_dict, freq, sizes, node_size_map, node_signs, node_stats = get_node_data_diff(node_data_list, node_type)
    edge_data, min_weight, max_weight, weight_bins, edge_size_map, edge_signs, edge_stats = get_edge_data_diff(edge_data_list, edge_type)
    colors = get_colors(node_names, behaviours, colour_type)
    selector_node_classes, selector_edge_classes = get_selector_classes_comparison(node_names, behaviours, colors, node_size_map, edge_size_map, colour_type)
    node_data, nodes = get_nodes_comparison(node_names, acronyms, freq, sizes, node_type, node_signs, leader, colour_type)
    if node_type == 'Behaviours':
        edges = get_behaviour_edges_comparison(edge_data, colour_source, edge_signs)
    else:
        edges = get_participant_edges_comparison(edge_data, colour_type, colour_source, edge_signs)
    return teams, meetings, node_data, edge_data, nodes, edges, selector_node_classes, selector_edge_classes, min_weight, max_weight, weight_bins, leader, node_signs, edge_signs, node_names, behaviours, node_stats, edge_stats

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
    teams = list(set(teams))
    teams.sort()
    # Add 'All' to teams at the beginning
    teams.insert(0, 'All')

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

def get_behaviour_node_data(events, team_list, team, meeting, participants, graph_type):
    # Remove All from teams (if present)
    teams = team_list.copy()
    if 'All' in teams:
        teams.remove('All')
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

    # Get additional stats for each node if team and/or meeting = 'All'
    stats = {}
    for name in node_names:
        stats[name] = ''
    if graph_type != 'Comparison':
        if team == 'All':
            team_freqs = {}
            for t in teams:
                team_events = events[events['sequenceId'].str.split('_').str[1] == t]
                team_freq = team_events['event'].value_counts()
                # If one node_name is not present in team_freq, add it with value 0
                for name in node_names:
                    if name not in team_freq:
                        team_freq[name] = 0
                team_freq = team_freq[node_names]
                team_freqs[t] = team_freq
            # Get the team with the highest frequency of each behaviour
            for name in node_names:
                max_freq = 0
                max_team = ''
                min_freq = 1000000
                min_team = ''
                sum = 0
                for t in teams:
                    if team_freqs[t][name] > max_freq:
                        max_freq = team_freqs[t][name]
                        max_team = t
                    if team_freqs[t][name] < min_freq:
                        min_freq = team_freqs[t][name]
                        min_team = t
                    sum += team_freqs[t][name]
                stats[name] += 'Most frequent team: ' + max_team + ' (' + str(max_freq) + ')'
                stats[name] += ' Least frequent team: ' + min_team + ' (' + str(min_freq) + ')'
                # Get average frequency
                stats[name] += ' Average frequency: ' + str(round(sum / len(teams),2))
        if meeting == 'All':
            # Get unique sequenceIds
            sequenceIds = events['sequenceId'].unique()
            # Get frequency of each behaviour in each meeting
            meeting_freqs = {}
            for s in sequenceIds:
                meeting_events = events[events['sequenceId'] == s]
                meeting_freq = meeting_events['event'].value_counts()
                # If one node_name is not present in meeting_freq, add it with value 0
                for name in node_names:
                    if name not in meeting_freq:
                        meeting_freq[name] = 0
                meeting_freq = meeting_freq[node_names]
                meeting_freqs[s] = meeting_freq
            # Get the meeting with the highest frequency of each behaviour
            for name in node_names:
                max_freq = 0
                max_meeting = ''
                min_freq = 1000000
                min_meeting = ''
                sum = 0
                for m in sequenceIds:
                    if meeting_freqs[m][name] > max_freq:
                        max_freq = meeting_freqs[m][name]
                        max_meeting = m
                    if meeting_freqs[m][name] < min_freq:
                        min_freq = meeting_freqs[m][name]
                        min_meeting = m
                    sum += meeting_freqs[m][name]
                stats[name] += ' Most frequent meeting: ' + max_meeting + ' (' + str(max_freq) + ')'
                stats[name] += ' Least frequent meeting: ' + min_meeting + ' (' + str(min_freq) + ')'

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
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + "," + str(NODE_MAP_MIN_SIZE) + "," + str(NODE_MAP_MAX_SIZE) + ")"
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map, leader, stats

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

    # Get additional stats for each node if team and/or meeting = 'All'
    stats = {}
    for name in node_names:
        stats[name] = ''

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
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + "," + str(NODE_MAP_MIN_SIZE) + "," + str(NODE_MAP_MAX_SIZE) + ")"
    return node_names, acronyms, acronyms_dict, freq, sizes, size_map, entities, leader, stats

def get_node_data_diff(node_data_list, node_type):
    node_names = []
    freq = []
    for node_data in node_data_list:
        node_names.append(node_data[0])
        freq.append(node_data[1])

    # Get the union of all node names
    node_names_diff = list(set().union(*node_names))

    stats = {}
    for name in node_names_diff:
        stats[name] = ''

    # Get acronyms
    if node_type == 'Behaviours':
        acronyms = [event.replace('_', ' ') for event in node_names_diff]
        acronyms = ["".join([word[0] for word in event.split()]) for event in acronyms]
        acronyms = [name.upper() for name in acronyms]
        acronyms = list(acronyms)
    else:
        acronyms = node_names_diff
    # Get acronyms dictionary
    acronyms_dict = dict(zip(node_names_diff, acronyms))

    # Ensure that freqs have all the node names (Add 0 if not present)
    for i in range(len(freq)):
        for node in node_names_diff:
            if node not in freq[i].index:
                freq[i][node] = 0
    # Calculate the difference in frequency between the two datasets
    freq_diff = freq[1] - freq[0]

    # Sort freq in the same order as node_names
    freq_diff = freq_diff[node_names_diff]

    # Get size
    sizes = freq_diff.values / 2.0
    # Get an array of 1 and -1 to depending on the size value
    signs = [size / abs(size) for size in sizes]
    # Change -1 for "negative" and 1 for "positive" and 0 for "neutral" in signs
    signs = ["negative" if sign == -1 else "positive" if sign == 1 else "" for sign in signs]


    # Change the sign of the sizes to positive
    sizes = [abs(size) for size in sizes]
    sizes = [max(250, size) for size in sizes]

    # Change the sign of freq_diff to positive
    freq_diff = freq_diff.abs()

    # Size map
    size_map = "mapData(size," + str(min(sizes)) + "," + str(max(sizes)) + "," + str(NODE_MAP_MIN_SIZE) + "," + str(NODE_MAP_MAX_SIZE) + ")"

    return node_names_diff, acronyms, acronyms_dict, freq_diff, sizes, size_map, signs, stats

def get_behaviour_edge_data(edge_type, team_list, events, team, meeting, graph_type):
    # Remove All from teams (if present)
    teams = team_list.copy()
    if 'All' in teams:
        teams.remove('All')
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

    # Get additional stats for each node if team and/or meeting = 'All'
    stats = {}
    for source,target in list(edges.keys()):
        stats[source,target] = ''
    if graph_type != 'Comparison':
        if team == 'All':
            team_freqs = {}
            for t in teams:
                team_freq = {}
                team_events = events[events['sequenceId'].str.split('_').str[1] == t]
                # Regenerate index
                team_events = team_events.reset_index(drop=True)
                for i in range(1, len(team_events)):
                    if (team_events['event'][i - 1], team_events['event'][i]) in team_freq:
                        team_freq[(team_events['event'][i - 1], team_events['event'][i])] += 1
                    else:
                        team_freq[(team_events['event'][i - 1], team_events['event'][i])] = 1
                # If one source, target pair is not present in team_freq, add it with value 0
                for name in list(edges.keys()):
                    if name not in team_freq:
                        team_freq[name] = 0
                team_freqs[t] = team_freq
            # Get the team with the highest frequency of each behaviour
            for source,target in list(edges.keys()):
                max_freq = 0
                max_team = ''
                min_freq = 1000000
                min_team = ''
                sum = 0
                for t in teams:
                    if team_freqs[t][source,target] > max_freq:
                        max_freq = team_freqs[t][source,target]
                        max_team = t
                    if team_freqs[t][source,target] < min_freq:
                        min_freq = team_freqs[t][source,target]
                        min_team = t
                    sum += team_freqs[t][source,target]
                stats[source,target] += 'Most frequent team: ' + max_team + ' (' + str(max_freq) + ')'
                stats[source,target] += ' Least frequent team: ' + min_team + ' (' + str(min_freq) + ')'
                # Get average frequency
                stats[source,target] += ' Average frequency: ' + str(round(sum / len(teams),2))
        if meeting == 'All':
            # Get unique sequenceIds
            sequenceIds = events['sequenceId'].unique()
            # Get frequency of each behaviour in each meeting
            meeting_freqs = {}
            for s in sequenceIds:
                meeting_freq = {}
                meeting_events = events[events['sequenceId'] == s]
                # Regenerate index
                meeting_events = meeting_events.reset_index(drop=True)
                for i in range(1, len(meeting_events)):
                    if (meeting_events['event'][i - 1], meeting_events['event'][i]) in meeting_freq:
                        meeting_freq[(meeting_events['event'][i - 1], meeting_events['event'][i])] += 1
                    else:
                        meeting_freq[(meeting_events['event'][i - 1], meeting_events['event'][i])] = 1
                # If one node_name is not present in meeting_freq, add it with value 0
                for name in list(edges.keys()):
                    if name not in meeting_freq:
                        meeting_freq[name] = 0
                meeting_freqs[s] = meeting_freq
            # Get the meeting with the highest frequency of each behaviour
            for source,target in list(edges.keys()):
                max_freq = 0
                max_meeting = ''
                min_freq = 1000000
                min_meeting = ''
                sum = 0
                for m in sequenceIds:
                    if meeting_freqs[m][source,target] > max_freq:
                        max_freq = meeting_freqs[m][source,target]
                        max_meeting = m
                    if meeting_freqs[m][source,target] < min_freq:
                        min_freq = meeting_freqs[m][source,target]
                        min_meeting = m
                    sum += meeting_freqs[m][source,target]
                stats[source,target] += ' Most frequent meeting: ' + max_meeting + ' (' + str(max_freq) + ')'
                stats[source,target] += ' Least frequent meeting: ' + min_meeting + ' (' + str(min_freq) + ')'

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
        edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    else:
        edge_data = [(key[0], key[1], "", value, int(round((value / 100) * source_sum[key[0]]))) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(min_weight) + "," + str(max_weight) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map, stats

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


    # Get additional stats for each node if team and/or meeting = 'All'
    stats = {}
    for name in list(edges.keys()):
        stats[name] = ''
    # Remove third element from the key
    stats = {(key[0], key[1]): value for key, value in stats.items()}

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
        edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    else:
        edge_data = [(key[0], key[1], key[2], value, int(round((value / 100) * source_sum[key[0]]))) for key, value in edges.items()]
        edge_size_map = "mapData(weight," + str(min_weight) + "," + str(max_weight) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    return edge_data, min_weight, max_weight, weight_bins, edge_size_map, stats

def get_edge_data_diff(edge_data_list, edge_type):
    edge_data = []
    # Append all the edge data to a list

    for edge in edge_data_list:
        # Add each tuple individually
        edge_dat = []
        for i in range(len(edge)):
            edge_dat.append(edge[i])
        edge_data.append(edge_dat)

    # Get the unique combinations of source, target and behaviour in the edge data
    edge_data_diff = []
    for i in range(len(edge_data)):
        for j in range(len(edge_data[i])):
            # Append if not present
            if (edge_data[i][j][0], edge_data[i][j][1], edge_data[i][j][2], 0.0, 0.0) not in edge_data_diff:
                edge_data_diff.append((edge_data[i][j][0], edge_data[i][j][1], edge_data[i][j][2], 0, 0))

    # Convert data each list in edge_data to a dictionary (key: (source, target, behaviour), value: (weight, original_weight))
    for i in range(len(edge_data)):
        edge_data[i] = dict(zip([(edge[0], edge[1], edge[2]) for edge in edge_data[i]],
                                [(edge[3], edge[4]) for edge in edge_data[i]]))
    # Convert edge_data_diff to a dictionary (key: (source, target, behaviour), value: (weight, original_weight))
    edge_data_diff = dict(zip([(edge[0], edge[1], edge[2]) for edge in edge_data_diff], [(edge[3], edge[4]) for edge in edge_data_diff]))

    # Ensure that both edge data dictionaries have the same keys in edge_data_diff
    for i in range(len(edge_data)):
        for key in edge_data_diff:
            if key not in edge_data[i]:
                edge_data[i][key] = (0.0, 0.0)

    # Calculate the difference in weights between the two dictionaries
    for key in edge_data_diff:
        edge_data_diff[key] = (edge_data[1][key][0] - edge_data[0][key][0], edge_data[1][key][1] - edge_data[0][key][1])

    # Remove edges with weight 0
    edge_data_diff = {key: value for key, value in edge_data_diff.items() if value[1] != 0}

    # Get additional stats for each node if team and/or meeting = 'All'
    stats = {}
    for name in list(edge_data_diff.keys()):
        stats[name] = ''
    # Remove third element from the key
    stats = {(key[0], key[1]): value for key, value in stats.items()}

    # Dictionary of signs (positive or negative) for each weight
    signs = {key: value[1] / abs(value[1]) for key, value in edge_data_diff.items()}
    # Change -1 for "negative" and 1 for "positive" and 0 for "" in signs
    signs = {key: "negative" if sign == -1 else "positive" if sign == 1 else "" for key, sign in signs.items()}
    # Change the sign of the weights to positive
    edge_data_diff = {key: (abs(value[0]), abs(value[1])) for key, value in edge_data_diff.items()}
    # Keep the original weights
    edge_data_diff = {key: value[1] for key, value in edge_data_diff.items()}

    if edge_type == 'Probability':
        source_sum = {}
        for key, value in edge_data_diff.items():
            source = key[0]
            if source in source_sum:
                source_sum[source] += value
            else:
                source_sum[source] = value

        for key, value in edge_data_diff.items():
            source = key[0]
            edge_data_diff[key] = (value / source_sum[source] * 100)

    weights = list(edge_data_diff.values())
    min_weight = min(weights)
    max_weight = max(weights)

    # Create 10 bins in the range of min_weight and max_weight
    weight_bins = np.linspace(min_weight, max_weight, 20)
    # Create a dictionary with the bins as keys and the bins as values
    weight_bins = {str(int(bin)): str(int(bin)) for bin in weight_bins}

    # Convert dictionary to a list of 4-tuples
    if edge_type == 'Frequency':
        edge_data_diff = [(key[0], key[1], key[2], log2(value), value) for key, value in edge_data_diff.items()]
        edge_size_map = "mapData(weight," + str(log2(min_weight)) + "," + str(log2(max_weight)) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    else:
        edge_data_diff = [(key[0], key[1], key[2], value, int(round((value / 100) * source_sum[key[0]]))) for key, value in edge_data_diff.items()]
        edge_size_map = "mapData(weight," + str(min_weight) + "," + str(max_weight) + "," + str(EDGE_MAP_MIN_SIZE) + "," + str(EDGE_MAP_MAX_SIZE) + ")"
    return edge_data_diff, min_weight, max_weight, weight_bins, edge_size_map, signs, stats

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
                'background-color': "#44444",
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
                'background-color': "#444444",
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

def get_selector_classes_comparison(node_names, behaviours, colors, node_size_map, edge_size_map, colour_type):
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
                    'height': node_size_map,
                }
            }
        )
        selector_node_classes.append(
            {
                'selector': '.node' + name + 'positive',
                'style': {
                    'background-color': colors[name],
                    'line-color': colors[name],
                    'width': node_size_map,
                    'height': node_size_map,
                    'shape': 'triangle'
                }
            }
        )
        selector_node_classes.append(
            {
                'selector': '.node' + name + 'negative',
                'style': {
                    'background-color': colors[name],
                    'line-color': colors[name],
                    'width': node_size_map,
                    'height': node_size_map,
                    'shape': 'vee'
                }
            }
        )
        selector_edge_classes.append(
            {
                'selector': '.edge' + name + 'positive',
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
        selector_edge_classes.append(
            {
                'selector': '.edge' + name + 'negative',
                'style': {
                    'line-color': colors[name],
                    'target-arrow-color': colors[name],
                    'target-arrow-shape': 'vee',
                    'curve-style': 'bezier',
                    'control-point-step-size': 100,
                    'width': edge_size_map,
                    'line-style': 'dashed',
                    'line-dash-pattern': [6, 10]
                }
            }
        )
    return selector_node_classes, selector_edge_classes

def get_nodes(node_names, acronyms, freq, sizes, node_type, leader, colour_type, stats):
    # Create a list of random longitudes and latitudes with the size of the number of acronyms
    longitudes = np.random.uniform(-180, 180, len(acronyms))
    latitudes = np.random.uniform(-90, 90, len(acronyms))
    # Create list of tuples with short name, label, long and lat
    freq_values = freq.tolist()
    node_data = list(zip(node_names, acronyms, freq_values, longitudes, latitudes, sizes))
    if node_type == 'Behaviours':
        nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "node" + short
            }
            for short, label, freq, long, lat, size in node_data
        ]
    else:
        if colour_type == 'Behaviours':
            nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "nodeParticipant"
                }
                for short, label, freq, long, lat, size in node_data
            ]
        else:
            nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "node" + short
                }
                for short, label, freq, long, lat, size in node_data
            ]
        # Change leader node class
        if leader != '':
            for node in nodes:
                if node['data']['id'] in leader:
                    node['classes'] = "nodeLeader"
    return node_data, nodes

def get_nodes_comparison(node_names, acronyms, freq, sizes, node_type, node_signs, leader, colour_type):
    # Create a list of random longitudes and latitudes with the size of the number of acronyms
    longitudes = np.random.uniform(-180, 180, len(acronyms))
    latitudes = np.random.uniform(-90, 90, len(acronyms))
    # Create list of tuples with short name, label, long and lat
    freq_values = freq.tolist()
    node_data = list(zip(node_names, acronyms, freq_values, longitudes, latitudes, sizes))
    if node_type == 'Behaviours':
        nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': ''},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "node" + short
            }
            for short, label, freq, long, lat, size in node_data
        ]
    else:
        if colour_type == 'Behaviours':
            nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': ''},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "nodeParticipant"
                }
                for short, label, freq, long, lat, size in node_data
            ]
        else:
            nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': ''},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "node" + short
                }
                for short, label, freq, long, lat, size in node_data
            ]
        # Change leader node class
        if leader != '':
            for node in nodes:
                if node['data']['id'] in leader:
                    node['classes'] = "nodeLeader"

    # Change the class of each node depending on the sign of the size (add word positive or negative)
    for i, node in enumerate(nodes):
        node['classes'] += node_signs[i]
    return node_data, nodes

def get_behaviour_edges(edge_data, colour_source, stats):
    if colour_source == "Source":
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': stats[source, target]},
                'classes': "edge" + source
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': stats[source, target]},
                'classes': "edge" + target
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    return edges

def get_behaviour_edges_comparison(edge_data, colour_source, signs):
    if colour_source == "Source":
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': ''},
                'classes': "edge" + source
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        edges = [
            {
                'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': ''},
                'classes': "edge" + target
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    # Change the class of each edge depending on the sign of the weight (add word positive or negative)
    for i, edge in enumerate(edges):
        edge['classes'] += signs[edge['data']['source'], edge['data']['target'], edge['data']['behaviour']]

    return edges

def get_participant_edges(edge_data, colour_type, colour_source):
    if colour_type == 'Behaviours':
        edges = [
            {
                'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                'classes': "edge" + behaviour
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        if colour_source == "Source":
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                    'classes': "edge" + source
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                    'classes': "edge" + target
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
    return edges

def get_participant_edges_comparison(edge_data, colour_type, colour_source, signs):
    if colour_type == 'Behaviours':
        edges = [
            {
                'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                'classes': "edge" + behaviour
            }
            for source, target, behaviour, weight, original_weight in edge_data
        ]
    else:
        if colour_source == "Source":
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                    'classes': "edge" + source
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': ''},
                    'classes': "edge" + target
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
    # Change the class of each edge depending on the sign of the weight (add word positive or negative)
    for i, edge in enumerate(edges):
        edge['classes'] += signs[edge['data']['source'], edge['data']['target'], edge['data']['behaviour']]
    return edges

def get_original_nodes(node_data, node_type, leader, graph_type, node_signs, colour_type, stats):
    if node_type == 'Behaviours':
        original_nodes = [
            {
                'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                'position': {'x': 20 * lat, 'y': -20 * long},
                'classes': "node" + short
            }
            for short, label, freq, long, lat, size in node_data
        ]
    else:
        if colour_type == 'Behaviours':
            original_nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "nodeParticipant"
                }
                for short, label, freq, long, lat, size in node_data
            ]
        else:
            original_nodes = [
                {
                    'data': {'id': short, 'label': label, 'freq': str(freq), 'size': size, 'stats': stats[short]},
                    'position': {'x': 20 * lat, 'y': -20 * long},
                    'classes': "node" + short
                }
                for short, label, freq, long, lat, size in node_data
            ]
        # Change leader node class
        if leader != '':
            for node in original_nodes:
                if node['data']['id'] in leader:
                    node['classes'] = "nodeLeader"
    if graph_type == 'Comparison':
        # Change the class of each node depending on the sign of the size (add word positive or negative)
        for i, node in enumerate(original_nodes):
            node['classes'] += node_signs[i]
    return original_nodes

def get_original_edges(edge_data, node_type, colour_type, colour_source, graph_type, edge_signs, stats):
    if node_type == 'Behaviours':
        if colour_source == "Source":
            original_edges = [
                {
                    'data': {'source': source, 'target': target, 'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': stats[source, target]},
                    'classes': "edge" + source
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            original_edges = [
                {
                    'data': {'source': source, 'target': target,'behaviour':behaviour, 'weight': weight, 'original_weight': original_weight, 'stats': stats[source, target]},
                    'classes': "edge" + target
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
    else:
        if colour_type == 'Behaviours':
            original_edges = [
                {
                    'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': stats[source, target]},
                    'classes': "edge" + behaviour
                }
                for source, target, behaviour, weight, original_weight in edge_data
            ]
        else:
            if colour_source == "Source":
                original_edges = [
                    {
                        'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': stats[source, target]},
                        'classes': "edge" + source
                    }
                    for source, target, behaviour, weight, original_weight in edge_data
                ]
            else:
                original_edges = [
                    {
                        'data': {'source': source, 'target': target, 'weight': weight, 'original_weight': original_weight, 'behaviour': behaviour, 'stats': stats[source, target]},
                        'classes': "edge" + target
                    }
                    for source, target, behaviour, weight, original_weight in edge_data
            ]
    if graph_type == 'Comparison':
        for i, edge in enumerate(original_edges):
            edge['classes'] += edge_signs[edge['data']['source'], edge['data']['target'], edge['data']['behaviour']]
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

def get_legend_nodes(node_names, selector_node_classes, colour_type, behaviours):
    if colour_type == 'Behaviours':
        node_names = behaviours
    # Create a list of random longitudes and latitudes with the size of the number of acronyms
    longitudes = np.random.uniform(10, 700, len(node_names))
    latitudes = np.random.uniform(0, 0, len(node_names))
    # Create an array of size len(node_names) with the value 20
    sizes = [20] * len(node_names)
    node_data = list(zip(node_names,longitudes, latitudes, sizes, selector_node_classes))
    nodes = [
        {
            'data': {'label': short, 'size': size},
            'position': {'x': 20, 'y': -1},
            'classes': "node" + short
        }
        for short, long, lat, size, selector_class in node_data
    ]
    return nodes