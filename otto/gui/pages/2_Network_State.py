import PIL.Image
import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder

if st.session_state.user_token is None:
    st.info('Please Login from the Home page and try again.')
    st.stop()


def create_network_graph(network_state: dict):
    """
    Function to create a network graph from current network state
    Creates a diagram with switches, hosts and links
    Credit to: https://networkx.org/documentation/stable/auto_examples/drawing/plot_custom_node_icons.html
    Args:
        network_state: dict - current network state retrieved from otto_network_state_db
    """

    if not network_state:
        return None

    icons = {
        "switch": "otto/gui/pages/switch.png",
        "host": "otto/gui/pages/host.png",
    }

    network_graph = nx.Graph()

    images = {k: PIL.Image.open(fname) for k, fname in icons.items()}

    for switch, switch_data in network_state.items():
        switch_decimal = f"switch-{format(int(switch), 'd')}"
        if switch_decimal not in network_graph.nodes():
            network_graph.add_node(switch_decimal, image=images["switch"])
        for switch_port, remote_port in switch_data.get('portMappings', {}).items():
            remote_switch = f"switch-{int(remote_port.split('-')[0][1])}"
            if remote_switch not in network_graph.nodes():
                print(f"{remote_switch} not in graph. adding..")
                network_graph.add_node(remote_switch, image=images["switch"])

            network_graph.add_edge(switch_decimal, remote_switch, port_info=(switch_port, remote_port))

        for switch_port, remote_host in switch_data.get('connectedHosts', {}).items():
            host_id = remote_host['id']
            network_graph.add_node(host_id, image=images["host"])
            network_graph.add_edge(switch_decimal, host_id)

    pos = nx.spring_layout(network_graph, k=0.5, iterations=50, seed=1734289230)
    fig, ax = plt.subplots()

    nx.draw_networkx_edges(
        network_graph,
        pos=pos,
        ax=ax,
        edge_color="gray",
        width=2, alpha=0.7,
        connectionstyle="arc3,rad=0.1",
        arrows=True,
        arrowstyle="-",
        min_source_margin=15,
        min_target_margin=15,
    )

    label_offset = 0.05
    label_pos = {node: (x, y + label_offset) for node, (x, y) in pos.items()}
    nx.draw_networkx_labels(
        network_graph,
        pos=label_pos,
        labels={n: n for n in network_graph.nodes()},
        font_size=8,
        font_color="black",
        font_weight="bold",
        verticalalignment="bottom",
        horizontalalignment="center",
        ax=ax,
    )
    tr_figure = ax.transData.transform
    tr_axes = fig.transFigure.inverted().transform

    icon_size = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02  # Fixed extra parenthesis
    icon_center = icon_size / 2.0

    for n in network_graph.nodes:
        xf, yf = tr_figure(pos[n])
        xa, ya = tr_axes((xf, yf))
        a = plt.axes([xa - icon_center, ya - icon_center, icon_size, icon_size])
        a.imshow(network_graph.nodes[n]["image"])
        a.axis("off")

    return fig


if st.session_state.user_token is not None:
    network_state_finder = NetworkStateFinder()

    network_state = network_state_finder.get_network_state()

    if state_id := next(iter(network_state), None) is not None:
        network_graph_complete = create_network_graph(network_state[state_id])
    else:
        network_graph_complete = None

    st.header("Current Network State")

    if network_graph_complete is not None:
        st.pyplot(network_graph_complete)
    else:
        st.write("No network state available")

    if network_state:
        for switch, switch_data in network_state.items():
            with st.expander(f"Flows for switch-{format(int(switch), 'd')}:"):
                st.write(f"Switch datapath ID: {switch}")
                st.write(f"Switch ID: {format(int(switch), 'd')}")
                st.write("Installed Flows:")
                st.write(switch_data.get("installedFlows", {}))
