import traceback

class StreamProxy:
    def __init__(self, path, *, alternate=None, use_alternate=False):
        self.path = path
        self._opened = alternate if use_alternate else None
        self._using_alternate = use_alternate
    
    def __enter__(self):
        if self._opened is None:
            self._opened = open(self.path)
        return self._opened
    
    def __exit__(self, etype, value, tb):
        if not self._using_alternate:
            self._opened.close()
            self._opened = None
        if etype is not None:
            traceback.print_tb(tb)
            raise etype(value)  # from None