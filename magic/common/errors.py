"""Errors to be raised during rueltabel parsing."""
class TabelException(SystemExit):
    def __init__(self, lno: int, msg: str, seg_name: str = None, segment: list = None, shift: int = 0):
        """
        lno: line number error occurred on
        msg: error message
        seg: segment of ruelfile error occurred in
        shift: line number seg starts on
        """
        self.lno, self.msg = lno, msg
        start = f'\n  {self.__class__.__name__} in {seg_name}'
        self.code = f'{start}:\n      {msg}\n' if lno is None else f'{start} (line {1+shift+lno}):\n      {msg}\n'
        if isinstance(segment, list):
            # add 1 because 'lno' is zero-indexed
            self.code = f'{start} (line {1+shift+lno}):\n      {segment[lno]}\n  {msg}\n'


class TabelReferenceError(TabelException):
    pass


class TabelSyntaxError(TabelException):
    pass


class TabelValueError(TabelException):
    pass


class TabelFeatureUnsupported(TabelException):
    pass
