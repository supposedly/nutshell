"""Facilitates parsing of a nutshell rule into an abstract, compiler.py-readable format."""
import re
from functools import partial
from itertools import chain, cycle, islice, zip_longest

import bidict
import lark

from nutshell.common.classes import TableRange
from nutshell.common.utils import printv, printq
from nutshell.common.errors import *
from . import _napkins as napkins, _utils as utils, _symmetries as symmetries
from ._classes import SpecialVar, VarName
from .lark_assets import NUTSHELL_GRAMMAR, Preprocess, Variable, _classes


class Bidict(bidict.bidict):
    on_dup_kv = bidict.OVERWRITE


class Table:
    CARDINALS = utils.generate_cardinals({
      'oneDimensional': ('W', 'E'),
      'vonNeumann': ('N', 'E', 'S', 'W'),
      'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
      'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'),
      })
    TRLENS = {k: len(v) for k, v in CARDINALS.items()}
    hush = True

    def __init__(self, tbl, start=0, *, dep: ['@NUTSHELL'] = None):
        self._src = tbl
        self._src[:] = [i.split('#')[0].strip() for i in tbl]  # Lark chokes on comments for reasons unknown otherwise :/
        self._start = start
        self._n_states = 0
        self._nbhd = self._trlen = None
        dep, = dep
        
        if self.hush:
            global printv, printq
            printv = printq = lambda *_, **__: None
        
        self.vars = Bidict()  # {VarName(name) | str(name) :: Variable(value)}
        self.directives = {}
        self.transitions = []
        self._constants = {}
        self.sym_types = set()
        
        if dep is not None:
            dep.replace(self._src)
            self._constants = dep.constants
            if self._constants:
                self._n_states = max(self._constants.values())
        
        trans = Preprocess(tbl=self)
        parser = lark.Lark(NUTSHELL_GRAMMAR, parser='lalr', start='table', propagate_positions=True)
        self._data = trans.transform(parser.parse('\n'.join(self._src)))
        if len(self.sym_types) == 1 and not hasattr(next(iter(self.sym_types)), 'fallback'):
            self.final = [t.fix_vars() for t in self._data]
        else:
            min_sym = symmetries.find_min_sym_type(self.sym_types, self.trlen)
            self.directives['symmetries'] = getattr(min_sym, 'name', [min_sym.__name__.lower()])[0]
            self.final = [new_tr for tr in self._data for new_tr in tr.in_symmetry(min_sym)]
            print(self.vars)
        self.directives['n_states'] = self.directives.pop('states')
    
    def __getitem__(self, item):
        return self._src[item]
    
    def __iter__(self):
        yield from self.final
    
    @property
    def neighborhood(self):
        if self._nbhd is None:
            self._nbhd = self.CARDINALS[self.directives['neighborhood']]
        return self._nbhd

    @property
    def trlen(self):
        if self._trlen is None:
            self._trlen = len(self.neighborhood)
        return self._trlen
    
    @property
    def symmetries(self):
        return symmetries.get_sym_type(self.directives['symmetries'])
    
    @property
    def n_states(self):
        return self._n_states
    
    @n_states.setter
    def n_states(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            if value == '?':
                self.vars[VarName('any')] = Variable(range(self.n_states), context=None)
                self.vars[VarName('live')] = Variable(range(1, self.n_states), context=None)
        else:
            self._n_states = value
            self.vars[VarName('any')] = Variable(range(value), context=None)
            self.vars[VarName('live')] = Variable(range(1, value), context=None)

    def add_sym_type(self, name):
        self.sym_types.add(symmetries.get_sym_type(name))
