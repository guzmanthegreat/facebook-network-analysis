import pandas as pd
import networkx as nx
import pickle

# Load the raw dataset.
df_edges = pd.read_csv("fb-pages-public-figure.edges", header=None, names=["source", "target"])
df_nodes = pd.read_csv("fb-pages-public-figure.nodes")

# Build the undirected graph.
G = nx.Graph()

for _, row in df_nodes.iterrows():
    G.add_node(row["new_id"], name=row["name"])

valid_nodes = set(df_nodes["new_id"])

for _, row in df_edges.iterrows():
    if row["source"] in valid_nodes and row["target"] in valid_nodes:
        G.add_edge(row["source"], row["target"])

# Identify the giant connected component.
largest_cc = max(nx.connected_components(G), key=len)
G_gcc = G.subgraph(largest_cc).copy()

# Calculate node-level metrics.
degree_dict = dict(G.degree())
degree_centrality = nx.degree_centrality(G)
clustering_dict = nx.clustering(G)

betweenness = nx.betweenness_centrality(G)

# Detect communities using greedy modularity optimization.
communities = list(nx.community.greedy_modularity_communities(G))

community_map = {}
for i, community in enumerate(communities):
    for node in community:
        community_map[node] = i

# Generate a reproducible layout for visualizations.
positions = nx.spring_layout(G, seed=42)

# Assemble the processed node table.
node_df = pd.DataFrame({
    "node": list(G.nodes()),
    "degree": [degree_dict[n] for n in G.nodes()],
    "degree_centrality": [degree_centrality[n] for n in G.nodes()],
    "betweenness": [betweenness[n] for n in G.nodes()],
    "clustering": [clustering_dict[n] for n in G.nodes()],
    "community": [community_map[n] for n in G.nodes()],
    "x": [positions[n][0] for n in G.nodes()],
    "y": [positions[n][1] for n in G.nodes()],
    "name": [G.nodes[n].get("name", f"Node {n}") for n in G.nodes()],
})

# Calculate network-level summary statistics.
summary_stats = {
    "nodes": G.number_of_nodes(),
    "edges": G.number_of_edges(),
    "density": nx.density(G),
    "components": nx.number_connected_components(G),
    "gcc_size": G_gcc.number_of_nodes(),
    "avg_degree": sum(degree_dict.values()) / G.number_of_nodes(),
    "avg_clustering": sum(clustering_dict.values()) / G.number_of_nodes(),
    "communities": len(communities)
}

# Save artifacts used by the dashboard.
node_df.to_csv("processed_nodes.csv", index=False)

with open("graph.pkl", "wb") as f:
    pickle.dump(G, f)

with open("summary_stats.pkl", "wb") as f:
    pickle.dump(summary_stats, f)
