HEADER = '''\
*********************************
**** COMPILED FROM RUELTABEL ****
*********************************
'''
COMMENT_SRC = False


def _handle_rule(rulefile, seg):
    name = seg.pop(0)
    rulefile.extend((f'@RULE {name}', HEADER, *seg))


def _iter_transitions(transitions):
    done = set()
    for lno, tr in transitions:
        if COMMENT_SRC and lno not in done:
            yield f"# {tbl[lno].split('#')[0]}"
            done.add(lno)
        yield ', '.join(map(str, tr))


def _handle_table(rulefile, tbl):
    rulefile.append('@TABLE')
    rulefile.append(f"neighborhood: {tbl.directives.pop('neighborhood')}")
    for directive, value in tbl.directives.items():
        rulefile.append(f'{directive}: {value}')
    rulefile.append('')
    
    for var, value in tbl.vars.items():
        rulefile.append('')
        value = set(value)  # Removes duplicates and gives braces
        rulefile.append(f'var {var.name}_0 = {value}')
        for suf in range(1, 1+var.rep):
            rulefile.append(f'var {var.name}_{suf} = {var.name}_0')
    rulefile.append('')
    rulefile.extend(_iter_transitions(tbl.transitions))


def compile(parsed):
    rulefile = []
    try:
        _handle_rule(rulefile, parsed.pop('@RUEL'))
    except KeyError:
        pass
    try:
        _handle_table(rulefile, parsed.pop('@TABEL'))
    except KeyError:
        pass
    for label, segment in parsed.items():
        rulefile.extend(('', '', label, *segment))
    return '\n'.join(rulefile) + '\n'
