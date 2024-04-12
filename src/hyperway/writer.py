

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    print('No Graphviz -')
    HAS_GRAPHVIZ = False

from .reader import get_nodes_edges


def write_graphviz(graph, title, **opts):
    if HAS_GRAPHVIZ is False:
        print('graphviz is not installed.')
        return False

    defaults = {
        # 'format':'svg',
        'format':'png',
        # filename='traffic_lights.svg',
        # filename='traffic_lights.gv',
        # node_attr={'class': 'darkmode'},
         'engine':'neato'
    }

    defaults.update(opts)

    t = graphviz.Digraph(title, **defaults)

    nodes, edges = get_nodes_edges(graph)

    # t.attr('node', shape='circle', fixedsize='true', width='0.9')
    t.attr('node', shape='box', style="rounded", # fontsize='12',
        fontname="Arial", color='#2299FF', fontcolor='#DDD')


    for node, label in nodes:
        t.node(node, label)

    for edge in edges:
        t.edge(*edge)

    t.attr(overlap='false')
    # t.attr(label=r'PetriNet Model Diagram\n')
                 # r'Extracted from ConceptBase and layed out by Graphviz'))
    t.attr(fontsize='12')
    # t.attr(bgcolor="#000000")
    t.attr(bgcolor="#00000000")

    # t.view()
    # t.format = 'svg'
    r_opts = {}
    directory = opts.get('directory', None)
    if directory is not None:
        r_opts = dict(directory=directory)

    t.render(**r_opts).replace('\\', '/')

    return t