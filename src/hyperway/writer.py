

try:
    import graphviz
    HAS_GRAPHVIZ = True
    print('Successfully imported graphviz for writing graphviz files.')
except ImportError:
    import sys
    _error_string = 'No graphviz installed, cannot write graphviz files.\n'
    sys.stderr.write(_error_string)
    print(_error_string)
    HAS_GRAPHVIZ = False

from .reader import get_nodes_edges


import os
from pathlib import Path


def set_graphviz(path):
    graphviz_bin = Path(path)
    os.environ["PATH"] += os.pathsep + str(graphviz_bin)


def write_graphviz(graph, title, **opts):
    """
    styles:
        name               default
        ---------------------------
        node_shape         'box'
        node_style         "rounded"
        node_arrowsize     "0.8"
        node_fontname      "Arial"
        node_color         #2299FF'
        node_fontcolor     #DDD'
        direction          'TB' 'LR'
    """
    if HAS_GRAPHVIZ is False:
        print('graphviz is not installed.')
        return False

    styles = opts.pop('styles', {})
    direction = opts.pop('direction', 'TB')
    show_view = opts.pop('view', False)
    t_format = opts.pop('format', None)
    print(f'{direction=}')
    defaults = {
        # 'format':'svg',
        'format':'png',
        # filename='traffic_lights.svg',
        # filename='traffic_lights.gv',
        # node_attr={'class': 'darkmode'},
         # 'engine':'neato',
        'engine':'dot',
        'graph_attr':{
            'rankdir': direction
        }
    }

    defaults.update(opts)

    t = graphviz.Digraph(title, **defaults)
    t.graph_attr['rankdir'] = direction

    nodes, edges = get_nodes_edges(graph)

    # t.attr('node', shape='circle', fixedsize='true', width='0.9')
    t.attr('node',
            shape=styles.get('node_shape', 'box'),
            style=styles.get('node_style', "rounded"),
            arrowsize=styles.get('node_arrowsize', "0.8"),
            fontname=styles.get('node_fontname', "Arial"),
            color=styles.get('node_color', '#2299FF'),
            fontcolor=styles.get('node_fontcolor', '#DDD'),
        )

    for node, label in nodes:
        t.node(node, label)

    for edge in edges:
        t.edge(*edge)

    t.attr(overlap=styles.get('overlap', 'false'))
    # t.attr(label=r'PetriNet Model Diagram\n')
                 # r'Extracted from ConceptBase and layed out by Graphviz'))
    t.attr(fontsize=styles.get('fontsize', '12'))
    t.attr(bgcolor=styles.get('bgcolor', "#00000000"))

    if show_view:
        t.view()
    if t_format is not None:
        t.format = t_format
    r_opts = {}
    directory = opts.get('directory', None)
    if directory is not None:
        r_opts = {'directory':directory}

    t.render(**r_opts).replace('\\', '/')

    return t