from contextlib import suppress

from nutshell.cli import cli


def _handle_rule(rulefile, include_header, seg):
    if seg is None:
        return
    name = seg.pop(0)
    rulefile.append(f'@RULE {name}')
    if include_header:
        rulefile.append(cli.result.transpile.header)
    rulefile.extend(seg)


def _iter_transitions(tbl):
    if not cli.result.transpile.comment_src:
        yield from (', '.join(map(str, tr)) for tr in tbl)
        return
    seen = set()
    for tr in tbl:
        if tr.ctx not in seen:
            seen.add(tr.ctx)
            lno, start, end = tr.ctx
            yield f"# {lno}: {tbl[lno-1][start-1:end-1]}"
        yield ', '.join(map(str, tr))


def _handle_table(rulefile, tbl):
    rulefile.append('@TABLE')
    if tbl[0] is None:  # sentinel from segmentor.py indicating not to touch
        rulefile.extend(tbl[1:])
        return
    rulefile.append(f"neighborhood: {tbl.directives.pop('neighborhood')}")
    for directive, value in tbl.directives.items():
        rulefile.append(f'{directive}: {value}')
    rulefile.append('')
    for var, value in tbl.vars.items():
        if var.rep == -1:
            continue
        # set() removes duplicates and gives braces
        # XXX: Golly gives up reading variables past a certain length; maybe not a good idea to keep spaces...?
        rulefile.append(f'var {var.name}.0 = {set(value)}')
        rulefile.extend(f'var {var.name}.{suf} = {var.name}.0' for suf in range(1, 1 + var.rep))
    rulefile.append('')
    rulefile.extend(_iter_transitions(tbl))


def compile(parsed):
    rulefile = []
    with suppress(KeyError):
        _handle_rule(rulefile, '@NUTSHELL' in parsed, parsed.pop('@NUTSHELL', parsed.pop('@RULE', None)))
    with suppress(KeyError):
        _handle_table(rulefile, parsed.pop('@TABLE'))
    for label, segment in parsed.items():
        rulefile.extend(('', label, *segment))
    return '\n'.join(rulefile) + '\n'
