from collections import defaultdict

from .base import GraphBase, connect, add, resolve
from .. import writer
from ..stepper import StepperC
from ..packer import argspack



class Graph(GraphBase):
    _stepper_callers = None
    _stepper_args = None

    def add_edge(self, edge):
        # id of the _edge_
        self[edge.id()] += (edge, )
        self[edge.a.id()] += (edge, )

    def connect(self, *a, **kw):
        return connect(self, *a, **kw)

    def add(self, *a, **kw):
        return add(self, *a, **kw)

    def resolve(self, n, **kw):
        return resolve(n, self, **kw)

    def stepper_prepare(self, n=None, *a, **kw):
        self._stepper_callers = n
        self._stepper_args = argspack(*a, **kw)

    def stepper(self, n=None, *a, **kw):
        stepper = StepperC(self)
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
