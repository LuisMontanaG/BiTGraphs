from pyvis.network import Network
import networkx as nx
import pandas as pd

net = Network(height='1200', width='100%', bgcolor='#222222', font_color='white', directed=True, filter_menu=True)

# set the physics layout of the network
net.barnes_hut(overlap=1)

# Read csv file
database = 'dbGEC2017'
events = pd.read_csv(database + '/Events.csv')
entities = pd.read_csv(database + '/EntityAttributes.csv')

# Keep only event and entityId columns in events
events = events[['event', 'entityId']]
# Keep only entityId, ParameterKey and ParameterValue columns in entities
entities = entities[['entityId', 'ParameterKey', 'ParameterValue']]

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
freq = freq.drop('Break')
# Sort freq in the same order as node_names
freq = freq[node_names]
sizes = freq.values / 2.0
sizes = [max(250, size) for size in sizes]


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
colors = colors[:len(node_names)]

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
max_weight = max(weights) #* .01

# Divide weights by max_weight
weights = [weight / max_weight for weight in weights]
# Convert dictionary to a list of 3-tuples
edges = [(key[0], key[1], value) for key, value in edges.items()]

# Node attributes
node_attributes = {}
for i in range(len(acronyms)):
    node_attributes[acronyms[i]] = {'name': node_names[i], 'freq': int(freq[node_names[i]])}

# Edge attributes
edge_attributes = {}
for i in range(len(edges)):
    edge_attributes[(edges[i][0], edges[i][1])] = {'weight': edges[i][2]}

DG = nx.DiGraph()
DG.add_nodes_from(node_names)
DG.add_weighted_edges_from(edges)
pos = nx.circular_layout(DG, scale= 400)

# Create nodes
for node in DG.nodes:
    net.add_node(node, node, title=node, color=colors[node_names.tolist().index(node)], x = pos[node][0],y = pos[node][1])

for edge in edges:
    net.add_edge(edge[0], edge[1], value=edge[2], title=str(edge[0]) + " -> " + str(edge[1]) + ": " + str(edge[2]))

neighbor_map = net.get_adj_list()
edges = net.get_edges()
nodes = net.get_nodes()

N_nodes = len(nodes)
N_edges = len(edges)

weights = [[] for i in range(N_nodes)]

# Associating weights to neighbors
for i in range(N_nodes):  # Loop through nodes
    for neighbor in neighbor_map[nodes[i]]:  # and neighbors
        for j in range(N_edges):  # associate weights to the edge between node and neighbor
            if (edges[j]['from'] == nodes[i] and edges[j]['to'] == neighbor) or \
                    (edges[j]['from'] == neighbor and edges[j]['to'] == nodes[i]):
                weights[i].append(edges[j]['value'])

for node, i in zip(net.nodes, range(N_nodes)):
    node['value'] = len(neighbor_map[node['id']])
    node['weight'] = [str(weights[i][k]) for k in range(len(weights[i]))]
    list_neighbor = list(neighbor_map[node['id']])
    # Concatenating neighbors and weights
    hover_str = [list_neighbor[k] + ' ' + node['weight'][k] for k in range(node['value'])]
    # Setting up node title for hovering
    node['title'] += ': ' + str(freq[node['id']])

for node in net.get_nodes():
  net.get_node(node)['physics']=False
  net.get_node(node)['label']=acronyms_dict[node]

#net.show_buttons(filter_=["physics"])
net.toggle_physics(False)
net.save_graph('network.html')