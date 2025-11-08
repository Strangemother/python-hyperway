"""
Example demonstrating get_outbound_connections and get_inbound_connections methods.

This example shows how to:
1. Build a graph with multiple nodes and connections
2. Query outbound connections from a specific node
3. Query inbound connections to a specific node
4. Inspect the graph topology programmatically
"""

from hyperway.graph import Graph
from hyperway.nodes import as_unit
from hyperway.tools import factory as f


def print_section(title):
    """Helper to print section headers"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def inspect_node_connections(node, graph, label="Node"):
    """Print detailed connection information for a node"""
    print(f"\n{label}: {node.get_name()}")
    print(f"  ID: {node.id()}")
    
    # Get outbound connections
    outbound = node.get_outbound_connections(graph)
    print(f"\n  Outbound connections: {len(outbound) if outbound else 0}")
    if outbound:
        for i, edge in enumerate(outbound, 1):
            print(f"    {i}. {edge.a.get_name()} → {edge.b.get_name()}")
            if edge.through:
                print(f"       (via wire: {edge.through})")
    
    # Get inbound connections
    inbound = node.get_inbound_connections(graph)
    print(f"\n  Inbound connections: {len(inbound)}")
    if inbound:
        for i, edge in enumerate(inbound, 1):
            print(f"    {i}. {edge.a.get_name()} → {edge.b.get_name()}")
            if edge.through:
                print(f"       (via wire: {edge.through})")


def example_linear_chain():
    """Example 1: Simple linear chain A → B → C → D"""
    print_section("Example 1: Linear Chain")
    
    g = Graph(tuple)
    
    # Create a linear chain
    chain = g.connect(f.add_10, f.add_20, f.add_30, f.add_40)
    
    # Get the individual nodes
    start_node = chain[0].a
    middle_node = chain[1].a
    end_node = chain[-1].b
    
    print("\nGraph structure: add_10 → add_20 → add_30 → add_40")
    
    # Inspect each node
    inspect_node_connections(start_node, g, "START Node")
    inspect_node_connections(middle_node, g, "MIDDLE Node")
    inspect_node_connections(end_node, g, "END Node")


def example_branching_graph():
    """Example 2: Graph with branches (one node connects to multiple)"""
    print_section("Example 2: Branching Graph")
    
    g = Graph(tuple)
    
    # Create a branching structure:
    #        → add_20 →
    # add_10            add_40
    #        → add_30 →
    
    start = as_unit(f.add_10)
    branch_a = as_unit(f.add_20)
    branch_b = as_unit(f.add_30)
    end = as_unit(f.add_40)
    
    # Connect start to both branches
    g.add(start, branch_a)
    g.add(start, branch_b)
    
    # Connect both branches to end
    g.add(branch_a, end)
    g.add(branch_b, end)
    
    print("\nGraph structure:")
    print("        → add_20 →")
    print("add_10            add_40")
    print("        → add_30 →")
    
    inspect_node_connections(start, g, "START Node (splits)")
    inspect_node_connections(branch_a, g, "BRANCH A")
    inspect_node_connections(branch_b, g, "BRANCH B")
    inspect_node_connections(end, g, "END Node (merges)")


def example_complex_topology():
    """Example 3: More complex topology with multiple connection types"""
    print_section("Example 3: Complex Topology")
    
    g = Graph(tuple)
    
    # Create nodes
    n1 = as_unit(f.add_1, name="n1")
    n2 = as_unit(f.add_2, name="n2")
    n3 = as_unit(f.add_3, name="n3")
    n4 = as_unit(f.add_4, name="n4")
    n5 = as_unit(f.add_5, name="n5")
    
    # Create a more complex graph:
    # n1 → n2 → n4
    #  ↓    ↓     ↑
    # n3 → n5 ----+
    
    g.add(n1, n2)
    g.add(n1, n3)
    g.add(n2, n4)
    g.add(n2, n5)
    g.add(n3, n5)
    g.add(n5, n4)
    
    print("\nGraph structure:")
    print("n1 → n2 → n4")
    print(" ↓    ↓     ↑")
    print("n3 → n5 ----+")
    
    # Inspect a node with multiple inbound and outbound connections
    inspect_node_connections(n5, g, "Node n5 (central hub)")
    
    # Show all nodes for comparison
    for node in [n1, n2, n3, n4, n5]:
        inspect_node_connections(node, g, f"Node {node.get_name()}")


def example_using_connections_for_analysis():
    """Example 4: Using connection methods for graph analysis"""
    print_section("Example 4: Graph Analysis")
    
    g = Graph(tuple)
    
    # Build a graph
    nodes = [as_unit(func, name=f"node_{i}") 
             for i, func in enumerate([f.add_1, f.add_2, f.add_3, f.add_4, f.add_5])]
    
    n1, n2, n3, n4, n5 = nodes
    
    # Create connections
    g.connect(n1, n2, n3)
    g.add(n2, n4)
    g.add(n3, n4)
    g.add(n4, n5)
    
    print("\nGraph structure: n1 → n2 → n3")
    print("                      ↓    ↓")
    print("                      n4 → n5")
    
    # Analysis functions using the connection methods
    def find_leaf_nodes(graph):
        """Find nodes with no outbound connections"""
        all_nodes = graph.get_nodes()
        leaves = []
        for node in all_nodes:
            outbound = node.get_outbound_connections(graph)
            if not outbound or len(outbound) == 0:
                leaves.append(node)
        return leaves
    
    def find_root_nodes(graph):
        """Find nodes with no inbound connections"""
        all_nodes = graph.get_nodes()
        roots = []
        for node in all_nodes:
            inbound = node.get_inbound_connections(graph)
            if len(inbound) == 0:
                roots.append(node)
        return roots
    
    def find_hub_nodes(graph, threshold=2):
        """Find nodes with many connections (in or out)"""
        all_nodes = graph.get_nodes()
        hubs = []
        for node in all_nodes:
            outbound = node.get_outbound_connections(graph)
            inbound = node.get_inbound_connections(graph)
            total = len(outbound or []) + len(inbound)
            if total >= threshold:
                hubs.append((node, total))
        return sorted(hubs, key=lambda x: x[1], reverse=True)
    
    # Run analysis
    print("\n--- Graph Analysis ---")
    
    roots = find_root_nodes(g)
    print(f"\nRoot nodes (no inbound): {len(roots)}")
    for node in roots:
        print(f"  - {node.get_name()}")
    
    leaves = find_leaf_nodes(g)
    print(f"\nLeaf nodes (no outbound): {len(leaves)}")
    for node in leaves:
        print(f"  - {node.get_name()}")
    
    hubs = find_hub_nodes(g, threshold=3)
    print(f"\nHub nodes (3+ connections): {len(hubs)}")
    for node, count in hubs:
        print(f"  - {node.get_name()}: {count} total connections")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("  NODE CONNECTION INTROSPECTION EXAMPLES")
    print("=" * 60)
    
    example_linear_chain()
    example_branching_graph()
    example_complex_topology()
    example_using_connections_for_analysis()
    
    print("\n" + "=" * 60)
    print("  Examples Complete")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
