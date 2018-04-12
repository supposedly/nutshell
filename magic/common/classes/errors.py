class KeyConflict(ValueError):
    pass


class TabelException(SystemExit):
    def __init__(self, lno, tbl, msg=None):
        if msg is None:
            msg, tbl = tbl, None
        self.code = msg if lno is None else f'{type(self).__name__} (line {lno}): {msg}'
        if isinstance(tbl, (list, tuple)):
            self.code = f'  {type(self).__name__} (line {lno}):\n    {tbl[lno]}\n  {msg}'


class TabelNameError(TabelException):
    pass


class TabelSyntaxError(TabelException):
    pass


class TabelValueError(TabelException):
    pass


class TabelFeatureUnsupported(TabelException):
    pass
