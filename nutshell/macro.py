"""Macro-related utilities"""
from .segment_types.table._classes import FinalTransition

def consolidate(transitions):
    lnos = {}
    for tr in transitions:
        lnos.setdefault(tr.lno, []).append(tr)
    return lnos
