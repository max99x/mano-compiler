from misc import ManoCollapserError
from objs import *


NAMES_COUNT = 0


def genId():
  global NAMES_COUNT
  NAMES_COUNT += 1
  return 'q%05d' % NAMES_COUNT


def collapse_program(functionset):
  global NAMES_COUNT

  if not (isinstance(functionset, dict)):
    raise ManoCollapserError('Input program is not a dictionary of functions.')

  NAMES_COUNT = 0

  # Construct lookup table.
  global_lookup = {'main': 'main', 'null': 'null'}
  for funcname in functionset:
    if funcname != 'main':
      global_lookup[funcname] = genId()

  for func in functionset.values():
    lookup = {}
    lookup.update(global_lookup)

    varnames = func.vars.keys()
    for varname in varnames:
      lookup[varname] = genId()
      func.vars[lookup[varname]] = func.vars[varname]
      del func.vars[varname]

    for i in range(len(func.params)):
      func.params[i] = lookup[func.params[i]]

    for line in func.code:
      attrs = ['label', 'condition', 'target', 'index']

      for attr in attrs:
        if hasattr(line, attr) and getattr(line, attr):
          name = getattr(line, attr)

          if name not in lookup:
            lookup[name] = genId()

          setattr(line, attr, lookup[name])

      if hasattr(line, 'expression'):
        exp = line.expression
        attrs = ['function', 'name', 'index', 'operand', 'left', 'right']

        for attr in attrs:
          if hasattr(exp, attr) and getattr(exp, attr):
            name = getattr(exp, attr)

            if name not in lookup:
              lookup[name] = genId()

            setattr(exp, attr, lookup[name])

        if hasattr(exp, 'arguments'):
          for i in range(len(exp.arguments)):
            name = exp.arguments[i]

            if name not in lookup:
              lookup[name] = genId()

            exp.arguments[i] = lookup[name]

  # Rename functions.
  funcs = functionset.keys()
  for funcname in funcs:
    if funcname != 'main':
      functionset[lookup[funcname]] = functionset[funcname]
      del functionset[funcname]

  return functionset
