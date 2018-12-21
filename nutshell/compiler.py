from contextlib import suppress

from nutshell.cli import cli


def _handle_rule(rulefile, include_header, seg):
    """
    rulefile: stream to write to
    include_header: whether to include the compiled-by header or not
    seg: @RULE-segment data as a list of lines

    Writes @RULE segment to output stream
    """
    if seg is None:
        return
    name = seg.pop(0)
    rulefile.append(f'@RULE {name}')
    if include_header:
        rulefile.append(cli.result.transpile.header)
    rulefile.extend(seg)


def compile(parsed):
    """
    parsed: dict of operated-upon segments from Nutshell file
    return: text of Golly table compiled from the above
    """
    rulefile = []
    with suppress(KeyError):
        _handle_rule(rulefile, '@NUTSHELL' in parsed, parsed.pop('@NUTSHELL', parsed.pop('@RULE', None)))
    for label, segment in parsed.items():
        rulefile.extend(('', label, *segment))
    return '\n'.join(rulefile) + '\n'
