from inspect import cleandoc


def _handle_rule(comp, seg):
    name = seg.pop(0)
    comp.append(f'@RULE {name}')
    comp.append(cleandoc('''
    *********************************
    **** COMPILED FROM RUELTABLE ****
    *********************************
    '''))
    comp.extend(seg)


def _handle_table(comp, tbl):
    comp.append('@TABLE')
    for directive, value in tbl.directives.items():
        comp.append(f'{directive}: {value}')
    comp.append('')
    
    for suf in range(1+tbl.var_all_rep):
        comp.append(f"var __all__{suf} = {'__all__0' if suf else set(tbl.var_all)}")
    for var, value in tbl.vars.items():
        comp.append('')
        value = set(value)  # Removes duplicates and also gives it braces
        comp.append(f'var {var.name}_0 = {value}')
        for suf in range(1, 1+var.rep):
            comp.append(f'var {var.name}_{suf} = {var.name}_0')
    comp.append('')
    comp.extend(', '.join(map(str, tr)) for tr in tbl.transitions)


def compile(parsed):
    comp = []
    _handle_rule(comp, parsed.pop('@RUEL'))
    _handle_table(comp, parsed.pop('@TABLE'))
    for segment_name, seg in parsed.items():
        comp.extend(['', '', segment_name, *seg])
    return '\n'.join(comp)
