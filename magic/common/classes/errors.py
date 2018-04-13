"""Errors to be raised during rueltabel parsing."""

class KeyConflict(ValueError):
    pass


class TabelException(SystemExit):
    def __init__(self, lno: int, msg: str, seg: list = None, shift: int = 0):
        """
        lno: line number error occurred on
        msg: error message
        seg: segment of ruelfile error occurred in
        shift: line number seg starts on
        """
        self.lno, self.msg = lno, msg
        exc_name = self.__class__.__name__
        self.code = f'  {exc_name}: {msg}\n' if lno is None else f'  {exc_name} (line {2+shift+lno}): {msg}\n'
        if isinstance(seg, (list, tuple)):
            # add 1 because 'lno' is zero-indexed
            self.code = f'  {exc_name} (line {1+shift+lno}):\n      {seg[lno]}\n  {msg}\n'


class TabelNameError(TabelException):
    pass


class TabelSyntaxError(TabelException):
    pass


class TabelValueError(TabelException):
    pass


class TabelFeatureUnsupported(TabelException):
    pass
