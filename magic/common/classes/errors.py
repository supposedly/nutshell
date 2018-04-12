class ExceptionMeta(type):
    def __new__(cls, name, bases, attrs):
        # Hide module name (don't need user seeing `magic.common.classes.errors` on every error output)
        attrs['__module__'] = ''
        # Hide 'inheritance dot' that the default Python interpreter keeps in spite of empty __module__
        return super().__new__(cls, '\N{BACKSPACE}'+name, bases, attrs)


class TabelException(Exception, metaclass=ExceptionMeta):
    def __init__(self, lno, message):
        self.lno = lno
        # Overwrite colon and opening space of error printing. ('\x08' == '\N{BACKSPACE}')
        self.msg = message if lno is None else f'\x08\x08 (line {lno}): {message}'
    
    def __str__(self):
        return str(self.msg)


class TabelNameError(TabelException):
    pass


class TabelSyntaxError(TabelException):
    pass


class TabelValueError(TabelException):
    pass


class TabelFeatureUnsupported(TabelException):
    pass


class KeyConflict(ValueError):
    pass
