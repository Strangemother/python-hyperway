


from hyperway import edges
from hyperway.edges import PartialConnection, get_connections
from hyperway.graph import Graph
from hyperway.nodes import as_unit

graph = Graph()

pc = PartialConnection(
    parent_connection=edges.make_edge('A', 'B')
)

res = get_connections(graph, pc)
# assert pc.get_connections was called. 

