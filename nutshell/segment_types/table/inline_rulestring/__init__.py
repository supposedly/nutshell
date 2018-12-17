from . import default_rs

funcs = {
  'hensel': default_rs.standard,
  'hensel-r4r': default_rs.r4r_only,
  '!hensel': default_rs.inverted,
  }