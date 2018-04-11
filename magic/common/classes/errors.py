class KeyConflict(ValueError):
    pass


class TabelException(Exception):
    def __init__(self, lno, message):
        self.lno = lno
        self.msg = f'Line {lno}: {message}' if lno is not None else message


class TabelNameError(TabelException):
    pass


class TabelSyntaxError(TabelException):
    pass

class TabelValueError(TabelException):
    pass
