HEADER = '''\
*********************************
**** COMPILED FROM RUELTABEL ****
*********************************
'''


def _handle_rule(rulefile, seg):
    name = seg.pop(0)
    rulefile.extend((f'@RULE {name}', HEADER, *seg))


def _handle_table(rulefile, tbl):
    rulefile.append('@TABLE')
    rulefile.append(f"neighborhood: {tbl.directives.pop('neighborhood')}")
    for directive, value in tbl.directives.items():
        rulefile.append(f'{directive}: {value}')
    rulefile.append('')
    
    for suf in range(1+tbl.var_all_rep):
        rulefile.append(f"var __all__{suf} = {'__all__0' if suf else set(tbl.var_all)}")
    for var, value in tbl.vars.items():
        rulefile.append('')
        value = set(value)  # Removes duplicates and gives braces
        rulefile.append(f'var {var.name}_0 = {value}')
        for suf in range(1, 1+var.rep):
            rulefile.append(f'var {var.name}_{suf} = {var.name}_0')
    rulefile.append('')
    rulefile.extend(', '.join(map(str, tr)) for _lno, tr in tbl.transitions)


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
    return '\n'.join(rulefile)
