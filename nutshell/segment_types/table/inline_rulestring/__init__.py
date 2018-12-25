from . import default_rs

funcs = {
  'hensel': default_rs.standard,
  '!hensel': default_rs.inverted,
  'b0-odd': default_rs.odd_invert
  }
