from collections import defaultdict

from .base import GraphBase, connect, add, resolve
from .. import writer
# from ..stepper import StepperC
from ..packer import argspack



class Graph(GraphBase):
    _stepper_callers = None
    _stepper_args = None
    _stepper_rows = None
    _stepper_class = None

    def get_stepper_class(self):
        if self._stepper_class is None:
            from ..stepper import StepperC
            self._stepper_class = StepperC
        return self._stepper_class

    def add_edge(self, edge):
        # id of the _edge_
        self[edge.id()] += (edge, )
        self[edge.a.id()] += (edge, )

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(edge)

    def get_nodes(self):
        res = set()
        for edges in self.values():
            for edge in edges:
                res.add(edge.a)
                res.add(edge.b)
        return tuple(res)

    def connect(self, *a, **kw):
        return connect(self, *a, **kw)

    def add(self, *a, **kw):
        return add(self, *a, **kw)

    def resolve(self, n, **kw):
        return resolve(n, self, **kw)

    def stepper_prepare(self, n=None, *a, **kw):
        self._stepper_callers = n
        self._stepper_args = argspack(*a, **kw)

    def stepper_prepare_many(self, *rows):
        """Given many rows of `node, primivites`,
        prepare the base rows using the stepper.prepare_many method
        """
        res = ()
        for node, *args in rows:
            print(node, args)
            row = (node, argspack(*args),)
            res += (row,)
        self._stepper_rows = res
        # self._stepper_args = argspack(*a, **kw)

    def stepper(self, n=None, *a, **kw):
        _StepperC = self.get_stepper_class()
        if self._stepper_rows is not None:
            stepper = _StepperC(self, self._stepper_rows)
            return stepper

        stepper = _StepperC(self)
        n = n or self._stepper_callers
        akw = self._stepper_args

        if len(a) + len(kw) > 0:
            akw = argspack(*a, **kw)
        if n is not None:
            stepper.prepare(n, akw=akw)
        return stepper

    def write(self, *a, **kw):
        return writer.write_graphviz(self, *a, **kw)


FORWARD = 1
BACKWARD = -1


class UndirectedGraph(object):

    def __init__(self):
        self.graphs = {
            FORWARD: Graph(tuple),
            BACKWARD: Graph(tuple),
        }

    def add_edge(self, edge):
        # id of the _edge_
        self.graphs[FORWARD][id(edge)] += (edge, )
        self.graphs[BACKWARD][id(edge)] += (edge, )
        # self[id(edge)] += (edge, )

    def __getattr__(self, k):
        if k in self.graphs:
            return self.graphs[k]
        return super().__getattr__(k)

    def connect(self, *nodes, **kw):
        fa = connect(self[FORWARD], *nodes, **kw)
        ba = connect(self[BACKWARD], *reversed(nodes), **kw)
        return fa + ba

    def add(self, *a, **kw):
        return add(self, *a, **kw)


    def resolve(self, n, **kw):
        return resolve(n, self, **kw)
