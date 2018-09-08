from .icons import icon_dev_rulegen
from .icons import icon_encoder

DISPATCH = {
  'convert': icon_encoder,
  'genrule': icon_dev_rulegen
  }

def dispatch(args):
    cmd = next(iter(args))
    return DISPATCH[cmd].main(args[cmd]) or ()
