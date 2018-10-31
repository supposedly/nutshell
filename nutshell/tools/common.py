import traceback

class StreamProxy:
    """
    Proxies a filestream, with the option to use an "alternate" stream
    if a certain condition is met
    
    (Used in Nutshell to operate on either a file-stream OR
    sys.stdout/.stdin depending on whether `-` was passed)
    """
    
    def __init__(self, path, mode='r', *, alternate=None, use_alternate=False):
        """
        path: path to file
        mode: mode to open path in
        alternate: Alternate stream to use if not use_alternate
        use_alternate: Whether to use `alternate` or file at `path`
        """
        self.path = path
        self.mode = mode
        self._opened = alternate if use_alternate else None
        self._using_alternate = use_alternate
    
    def __enter__(self):
        if self._opened is None:
            self._opened = open(self.path, self.mode)
        return self._opened
    
    def __exit__(self, etype, value, tb):
        if not self._using_alternate:
            self._opened.close()
            self._opened = None
        if etype is not None:
            traceback.print_tb(tb)
            raise etype(value)  # from None