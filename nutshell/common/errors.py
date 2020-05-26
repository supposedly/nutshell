"""Errors to be raised during nutshell parsing."""


class NutshellException(Exception):
    def __init__(self, lno: int, msg: str, seg_name: str = None, segment: list = None, *, shift: int = 0):
        """
        lno: line number error occurred on
        msg: error message
        seg: segment of rulefile error occurred in
        shift: line number seg starts on
        """
        self.pre = f'\n  {self.__class__.__name__}' if seg_name is None else f'\n  {self.__class__.__name__} in {seg_name}'
        self.lno, self.span, self.msg = lno, None, msg
        self.shift = shift
        if isinstance(lno, tuple):
            self.lno, *self.span = lno
        self.lno += 1
        if isinstance(segment, list):
            code = [
              f'{self.pre}, line {shift+self.lno}:',
              f'      {segment[self.lno-1]}'
              ]
            if self.span is not None:
                begin, end = self.span
                code.append(f"      {' ' * (begin - 1)}{'^' * (end - begin)}")
                self.msg = msg = msg.format(span=segment[self.lno-1][begin-1:end-1])
            code.append(f'  {msg}')
        else:
            code = [
              f'{self.pre}:' if self.lno is None else f'{self.pre}, line {shift+self.lno}:',
              f'      {msg}\n'
              ]
        self.lno = lno
        self.code = '\n'.join(code) + '\n'


class Error(NutshellException):
    pass


class UndefinedErr(NutshellException):
    pass


class SyntaxErr(NutshellException):
    pass


class ArithmeticErr(NutshellException):
    pass


class UnsupportedFeature(NutshellException):
    pass


class CoordOutOfBounds(NutshellException):
    pass
