import streamlit as st
import pandas as pd
import networkx as nx
import pickle
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Facebook Network Analysis",
    page_icon="🔗",
    layout="wide"
)

SEED = 42

st.title("Facebook Network Analysis")
st.caption("Interactive exploration of connections, communities, and structural importance among public-figure pages.")
st.write(
    "This dashboard explores a 2017 Facebook public-figures network where nodes represent "
    "public-figure pages and edges represent mutual page likes. The goal is to understand "
    "network connectivity, structural importance, and community structure."
)

@st.cache_resource(show_spinner=False)
def load_network_data():
    node_df = pd.read_csv("processed_nodes.csv")
    with open("graph.pkl", "rb") as f:
        G = pickle.load(f)

    with open("summary_stats.pkl", "rb") as f:
        summary_stats = pickle.load(f)

    return G, node_df, summary_stats


def build_network_figure(G, node_df, selected_nodes, title):
    subG = G.subgraph(selected_nodes).copy()

    if subG.number_of_nodes() == 0:
        return go.Figure()

    pos = nx.spring_layout(subG, seed=SEED)

    plot_nodes = node_df[node_df["node"].isin(subG.nodes())].copy()
    plot_nodes["x"] = plot_nodes["node"].map(lambda n: pos[n][0])
    plot_nodes["y"] = plot_nodes["node"].map(lambda n: pos[n][1])

    edge_x, edge_y = [], []

    for source, target in subG.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        hoverinfo="none",
        line=dict(width=0.7, color="lightgray")
    )

    node_trace = go.Scatter(
        x=plot_nodes["x"],
        y=plot_nodes["y"],
        mode="markers",
        customdata=plot_nodes[["node", "name", "community", "degree", "betweenness"]].values,
        hovertemplate=(
            "Node ID: %{customdata[0]}<br>"
            "Name: %{customdata[1]}<br>"
            "Community: %{customdata[2]}<br>"
            "Degree: %{customdata[3]}<br>"
            "Betweenness: %{customdata[4]:.4f}<extra></extra>"
        ),
        marker=dict(
            size=8 + plot_nodes["degree"] / plot_nodes["degree"].max() * 30,
            color=plot_nodes["community"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Community"),
            line=dict(width=1, color="black")
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=title,
        showlegend=False,
        height=650,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )

    return fig


def build_ego_figure(G, node_df, selected_node):
    ego_G = nx.ego_graph(G, selected_node)
    pos = nx.spring_layout(ego_G, seed=SEED)

    ego_nodes = list(ego_G.nodes())
    ego_node_df = node_df[node_df["node"].isin(ego_nodes)].copy()
    ego_node_df["x"] = ego_node_df["node"].map(lambda n: pos[n][0])
    ego_node_df["y"] = ego_node_df["node"].map(lambda n: pos[n][1])

    edge_x, edge_y = [], []

    for source, target in ego_G.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        hoverinfo="none",
        line=dict(width=1, color="lightgray")
    )

    node_trace = go.Scatter(
        x=ego_node_df["x"],
        y=ego_node_df["y"],
        mode="markers",
        customdata=ego_node_df[["node", "name", "community", "degree"]].values,
        hovertemplate=(
            "Node ID: %{customdata[0]}<br>"
            "Name: %{customdata[1]}<br>"
            "Community: %{customdata[2]}<br>"
            "Degree: %{customdata[3]}<extra></extra>"
        ),
        marker=dict(
            size=[35 if n == selected_node else 18 for n in ego_node_df["node"]],
            color=ego_node_df["community"],
            colorscale="Viridis",
            line=dict(width=1, color="black")
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"Ego Network for {selected_node}",
        showlegend=False,
        height=550,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )

    return fig


with st.spinner("Loading network data..."):
    G, node_df, summary_stats = load_network_data()

with st.sidebar:
    st.header("About this project")
    st.caption("A network-analysis portfolio project built with Python, NetworkX, Streamlit, and Plotly.")
    st.metric("Pages", f"{summary_stats['nodes']:,}")
    st.metric("Connections", f"{summary_stats['edges']:,}")
    st.metric("Communities", summary_stats["communities"])
    st.divider()
    st.caption("Dataset: 2017 Facebook Public Figures")
    st.caption("Edges represent mutual page likes and do not necessarily indicate friendship, endorsement, or influence.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Structural Importance",
    "Communities",
    "Node Explorer",
    "Findings & Limitations"
])

with tab1:
    st.header("Overview")

    st.markdown("""
    ## Research Questions

    **Community Structure:**  
    What do communities look like in the network? Do public figures form clusters based on shared interests?

    **Structural Importance:**  
    Which public figures occupy the most connected or strategically important positions?

    **Network Connectivity:**  
    Is the network highly connected, or does it break into smaller sub-networks?
    """)

    st.markdown("""
    ## What this network represents

    - **Nodes:** Facebook public figure pages  
    - **Edges:** Mutual likes between pages  
    - **Network type:** Undirected and unweighted  
    - **Time period:** 2017 snapshot  
    """)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", f"{summary_stats['nodes']:,}")
    c2.metric("Edges", f"{summary_stats['edges']:,}")
    c3.metric("Components", summary_stats["components"])
    c4.metric("Communities", summary_stats["communities"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Largest Component", f"{summary_stats['gcc_size']:,}")
    c6.metric("Average Degree", round(summary_stats["avg_degree"], 2))
    c7.metric("Density", round(summary_stats["density"], 5))
    c8.metric("Avg. Clustering", round(summary_stats["avg_clustering"], 3))

    st.markdown("## Key Findings")

    st.markdown("""
    - The network is **globally connected**, with most nodes located in one giant component.  
    - The network is **sparse**, meaning most public figures have only a few direct ties.  
    - A small number of nodes act as **major hubs** with unusually high degree.  
    - Some nodes act as **bridges** between different parts of the network.  
    - The network contains many detected communities, but a few large communities dominate.  
    """)

    with st.expander("Show full node metrics table"):
        st.dataframe(
            node_df[["node", "name", "degree", "degree_centrality", "betweenness", "community"]],
            use_container_width=True
        )

with tab2:
    st.header("Structural Importance")

    st.markdown("""
    Centrality measures describe different kinds of structural importance.  
    They identify highly connected nodes and bridges, but do not prove real-world influence.
    """)

    metric = st.selectbox(
        "Choose centrality measure",
        ["degree", "degree_centrality", "betweenness"]
    )

    explanations = {
        "degree": "Degree counts the number of direct connections a node has.",
        "degree_centrality": "Degree centrality rescales degree based on total network size.",
        "betweenness": "Betweenness identifies nodes that act as bridges between different parts of the network."
    }

    st.info(explanations[metric])

    top_k = st.slider("Number of top nodes to show", 5, 20, 10)

    top_nodes = node_df.sort_values(metric, ascending=False).head(top_k)

    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("Top-ranked nodes")
        st.dataframe(
            top_nodes[["node", "name", "community", "degree", "degree_centrality", "betweenness"]],
            use_container_width=True
        )

    with right:
        fig = px.bar(
            top_nodes,
            x="name",
            y=metric,
            color="community",
            hover_data=["node", "degree", "betweenness"],
            title=f"Top {top_k} Nodes by {metric}"
        )
        fig.update_layout(xaxis_title="Public Figure", yaxis_title=metric)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Key Insight")
    st.markdown("""
    Degree-based measures identify highly connected hubs, while betweenness identifies bridge nodes.
    This shows that structural importance is not just about having many connections. A node can also be important
    because it connects otherwise separate parts of the network.
    """)

with tab3:
    st.header("Community Structure")

    st.markdown("""
    Community detection identifies groups of nodes that are more connected to each other than to the rest of the network.
    This helps reveal whether public figures form smaller clusters within the larger network.
    """)

    community_sizes = (
        node_df.groupby("community")
        .size()
        .reset_index(name="num_nodes")
        .sort_values("num_nodes", ascending=False)
    )

    top_n = st.slider("Number of top communities to display", 5, 25, 10)

    fig_comm = px.bar(
        community_sizes.head(top_n),
        x="community",
        y="num_nodes",
        title=f"Top {top_n} Community Sizes"
    )
    fig_comm.update_layout(xaxis_title="Community", yaxis_title="Number of Nodes")
    st.plotly_chart(fig_comm, use_container_width=True)

    st.markdown("### Key Insight")
    st.markdown("""
    The community size distribution is uneven. A few communities contain thousands of nodes,
    while many others are much smaller. This suggests a core-periphery structure, where large
    clusters dominate but smaller niche groups still exist.
    """)

    selected_community = st.selectbox(
        "Select a community to inspect",
        sorted(community_sizes["community"].tolist())
    )

    community_nodes_df = node_df[node_df["community"] == selected_community].copy()

    st.subheader(f"Community {selected_community} Summary")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nodes", len(community_nodes_df))
    c2.metric("Average Degree", round(community_nodes_df["degree"].mean(), 2))
    c3.metric("Average Betweenness", round(community_nodes_df["betweenness"].mean(), 4))

    st.dataframe(
        community_nodes_df.sort_values("degree", ascending=False)
        [["node", "name", "degree", "betweenness", "community"]]
        .head(25),
        use_container_width=True
    )

    max_nodes = st.slider("Nodes to show in community network", 25, 200, 75)

    selected_nodes = (
        community_nodes_df.sort_values("degree", ascending=False)
        .head(max_nodes)["node"]
        .tolist()
    )

    fig_network = build_network_figure(
        G,
        node_df,
        selected_nodes,
        title=f"Community {selected_community} Network View"
    )

    st.plotly_chart(fig_network, use_container_width=True)

with tab4:
    st.header("Node Explorer")

    st.markdown("""
    This section allows users to inspect a specific public figure and view their local ego network.
    """)

    search_name = st.text_input("Search by public figure name")

    if search_name:
        search_results = node_df[
            node_df["name"].str.contains(search_name, case=False, na=False)
        ].sort_values("degree", ascending=False)

        st.write(f"Search results for: **{search_name}**")
        st.dataframe(
            search_results[["node", "name", "degree", "betweenness", "community"]].head(20),
            use_container_width=True
        )

    node_names = node_df.set_index("node")["name"].to_dict()
    node_options = sorted(node_names, key=lambda n: str(node_names[n]).lower())
    selected_node = st.selectbox(
        "Choose a node to inspect",
        node_options,
        format_func=lambda n: f"{node_names[n]} (ID: {n})"
    )

    node_row = node_df[node_df["node"] == selected_node].iloc[0]
    neighbors = list(G.neighbors(selected_node))
    neighbor_df = node_df[node_df["node"].isin(neighbors)].sort_values("degree", ascending=False)

    a, b, c, d = st.columns(4)
    a.metric("Degree", int(node_row["degree"]))
    b.metric("Community", int(node_row["community"]))
    c.metric("Betweenness", round(node_row["betweenness"], 4))
    d.metric("Neighbors", len(neighbors))

    st.markdown(
        f"""
        **Selected node:** {selected_node}  
        **Name:** {node_row["name"]}  
        **Community:** {int(node_row["community"])}  
        **Direct ties:** {int(node_row["degree"])}
        """
    )

    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("Immediate Neighbors")
        st.dataframe(
            neighbor_df[["node", "name", "degree", "betweenness", "community"]],
            use_container_width=True
        )

    with right:
        st.subheader("Local Ego Network")
        fig_ego = build_ego_figure(G, node_df, selected_node)
        st.plotly_chart(fig_ego, use_container_width=True)

    st.markdown("### Key Insight")
    st.markdown("""
    Ego networks help connect the global network structure to individual cases.
    Instead of only seeing the full graph, users can inspect how one public figure is locally positioned.
    """)

with tab5:
    st.header("Interpretation and Limitations")

    st.markdown("""
    ## Interpretation

    Overall, the Facebook public figures network is globally connected but locally sparse.
    Most nodes belong to one large connected component, meaning public figures are broadly linked
    through chains of mutual likes. However, the low density and low average degree show that most
    pages only have a small number of direct connections.

    The centrality results show that structural prominence is unevenly distributed. A small number of public figures
    act as hubs with many direct connections, while others may serve as bridges between different
    communities. This means that importance in the network is not only about popularity, but also about
    structural position.

    Community detection shows that the network is divided into many groups. A few communities are very
    large, while many others are smaller. This suggests that public figures may cluster around shared
    audiences, industries, or interests.

    ## Limitations

    - Edges represent mutual likes, not necessarily friendship, endorsement, collaboration, or real influence.
    - The dataset only captures one type of interaction and does not include comments, shares, followers, or content similarity.
    - The dataset is a 2017 snapshot, so the results may not reflect current Facebook relationships.
    - Community detection is algorithmic and should not be treated as perfect evidence of real-world groups.
    - Large network visualizations can be difficult to interpret, so the dashboard uses filtered views and ego networks.

    ## Next Steps

    - Refine community interpretation by examining the names and possible categories of top nodes in each group.
    - Add more polished labels and captions for dashboard visuals.
    - Improve the network visualization layout for clearer community separation.
    - Add additional centrality comparisons if computation time allows.
    - Prepare the final dashboard narrative so users can clearly understand the main findings.
    """)
