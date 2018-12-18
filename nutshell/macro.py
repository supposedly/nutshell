"""Macro-related utilities"""
from .segment_types.table._classes import FinalTransition

def consolidate(transitions):
    lnos = {}
    for tr in transitions:
        lnos.setdefault(tr.lno, []).append(tr)
    return lnos


def consolidate_extra(transitions):
    lnos = {}
    for tr in transitions:
        lnos.setdefault((tr.lno, tr.extra), []).append(tr)
    return lnos
