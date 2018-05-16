HEADER = '''\
*********************************
**** COMPILED FROM RUELTABEL ****
*********************************
'''
COMMENT_SRC = True


def _handle_rule(rulefile, seg):
    name = seg.pop(0)
    rulefile.extend((f'@RULE {name}', HEADER, *seg))


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
    if COMMENT_SRC:
        def new():
            done = set()
            for lno, tr in tbl.transitions:
                if lno not in done:
                    yield f"# {tbl[lno].split('#')[0]}"
                    done.add(lno)
                yield ', '.join(map(str, tr))
    else:
        new = lambda: (', '.join(map(str, tr)) for _lno, tr in tbl.transitions)
    rulefile.extend(new())


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
    for segment_name, seg in parsed.items():
        rulefile.extend(('', '', segment_name, *seg))
    return '\n'.join(rulefile) + '\n'
