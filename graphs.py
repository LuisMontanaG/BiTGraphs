import math
import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import pandas as pd

def remake_graph(w, node_names, acronyms_dict, edges):
    DG.clear()
    DG.add_nodes_from(node_names)
    # Remove edges with weight less than w
    edges = [(i[0], i[1], i[2]) for i in edges if i[2] >= w]
    #print(edges)
    DG.add_weighted_edges_from(edges)
    nx.relabel_nodes(DG, acronyms_dict, copy=False)
    nx.set_node_attributes(DG, node_attributes)
    nx.set_edge_attributes(DG, edge_attributes)


def update(val, node_names, acronyms_dict, freq, edges, colors):
    global annot
    r = val
    remake_graph(r, node_names, acronyms_dict, edges)
    ax.clear()
    nx.draw_networkx_edges(DG, pos, ax=ax, node_size=sizes)#, width=weights)
    nx.draw_networkx_labels(DG, pos, ax=ax)
    #nx.draw_networkx_edge_labels(DG, pos, ax=ax)
    nx.draw_networkx_nodes(DG, pos, ax=ax, node_size=sizes, node_color=colors)
    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)
    fig.canvas.draw_idle()
    pass

def update_annot_nodes(ind):
    node = ind["ind"][0]
    node = acronyms[node]
    xy = pos[node]
    annot.xy = xy
    node_attr = DG.nodes[node]
    text = '\n'.join(f'{k}: {v}' for k, v in node_attr.items())
    annot.set_text(text)

def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = nodes.contains(event)
        if cont:
            update_annot_nodes(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        elif vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()


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
    node_attributes[acronyms[i]] = {'name': node_names[i], 'freq': freq[node_names[i]]}

# Edge attributes
edge_attributes = {}
for i in range(len(edges)):
    edge_attributes[(edges[i][0], edges[i][1])] = {'weight': edges[i][2]}

r = 0.0
DG = nx.DiGraph()
DG.add_nodes_from(node_names)
DG.add_weighted_edges_from(edges)
nx.relabel_nodes(DG, acronyms_dict, copy=False)
nx.set_node_attributes(DG, node_attributes)
nx.set_edge_attributes(DG, edge_attributes)
#remake_graph(r)

fig, ax = plt.subplots()
pos = nx.spring_layout(DG, seed=42, k = 120/math.sqrt(DG.order()))
#nx.draw_networkx(DG, pos, arrows=True, with_labels=True, node_size=freq.values / 1.0, node_color=colors)
nx.draw_networkx_edges(DG, pos, ax=ax, node_size=sizes)# width=weights, arrowsize=20)
#nx.draw_networkx_edge_labels(DG, pos, ax=ax)
nx.draw_networkx_labels(DG, pos, ax=ax)
nodes = nx.draw_networkx_nodes(DG, pos, ax=ax, node_size=sizes, node_color=colors)
annot = ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->"))
annot.set_visible(False)
plt.subplots_adjust(bottom=0.25)


# Make a horizontal slider to control the frequency.
axcolor = 'lightgoldenrodyellow'
axfreq = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)
freq_slider = Slider(
    ax=axfreq,
    label='Weight treshold',
    valmin=0.0,
    valmax=max_weight,
    valinit=r,
)
freq_slider.on_changed(lambda new_val: update(new_val, node_names, acronyms_dict, freq, edges, colors))
fig.canvas.mpl_connect("motion_notify_event", hover)
plt.show()