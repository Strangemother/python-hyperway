
import graphviz
from .graph import Graph
from .tools import factory as f
from .nodes import as_unit
from .reader import get_nodes_edges

g = Graph(tuple)

ad30 = as_unit(f.add_30)
ad30_2 = as_unit(f.add_30)
# Connect
first_connection = g.add(f.add_10, f.add_20)
many_connections = g.connect(ad30, f.add_1, f.add_2, f.add_4)
compound_connection = g.add(many_connections[1].b, f.add_3)

g.connect(ad30_2, f.mul_1, f.add_6)
g.connect(f.mul_3, f.mul_1, ad30)

from writer import write_graphviz

write_graphviz(g, 'Diagram', directory='doctest-output')
