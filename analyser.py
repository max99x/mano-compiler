from misc import ManoAnalyserError
from objs import *


lookup = {}


def analyse_program(functionset):
  global lookup

  if not isinstance(functionset, dict):
    raise ManoAnalyserError('Input program is not a dictionary of functions.')

  # Construct function lookup table.
  global_lookup = {}
  for funcname in functionset:
    global_lookup[funcname] = ('function', functionset[funcname].return_type)

  for funcname in functionset:
    func = functionset[funcname]

    # Construct var lookup table.
    lookup = {}
    lookup.update(global_lookup)

    varnames = func.vars.keys()
    for varname in varnames:
      lookup[varname] = ('var', func.vars[varname][0])

    # Construct label lookup table.
    for line in func.code:
      if line.label:
        lookup[line.label] = ('label', 'any')

    # Analyse code.
    for line in func.code:
      if isinstance(line, GotoLine):
        assertType(line.target, ('label', 'any'), line, funcname, func)
      elif isinstance(line, PrintLine):
        assertType(line.target, ('var', 'any'), line, funcname, func)
      elif isinstance(line, ReadLine):
        assertType(line.target, ('var', 'any'), line, funcname, func)
      elif isinstance(line, ReturnLine):
        if line.target != 'null':
          assertType(
              line.target, ('var', lookup[funcname][1]), line, funcname, func)
      elif isinstance(line, AssignLine):
        type = getType(line.expression, functionset, line, funcname, func)
        if line.index:
          if type != ('var', Type('WORD')):
            throwError(line, funcname, func)
        elif line.target:
          assertType(line.target, type, line, funcname, func)
      else:
        raise ManoAnalyserError, 'Unrecognize statement type encountered.'


def assertType(identifier, typ, line, funcname, func):
  if identifier is None: return
  try:
    if typ[1] == 'any':
      if lookup[identifier][0] != typ[0]:
        throwError(line, funcname, func)
    else:
      if lookup[identifier] != typ:
        throwError(line, funcname, func)
  except:
    throwError(line, funcname, func)


def throwError(line, funcname, func):
  details = (func.code.index(line)+1, funcname, line)
  raise ManoAnalyserError('Error in statement %d of function %s: %s.' % details)


def getType(exp, functionset, line, funcname, func):
  if isinstance(exp, Identifier):
    if exp.index is not None:
      return ('var', Type('WORD'))
    else:
      return lookup[exp.name]
  elif isinstance(exp, UnaryOperation):
    assertType(exp.operand, ('var', Type('WORD')), line, funcname, func)
    return ('var', Type('WORD'))
  elif isinstance(exp, BinaryOperation):
    assertType(exp.left, ('var', Type('WORD')), line, funcname, func)
    assertType(exp.right, ('var', Type('WORD')), line, funcname, func)
    return ('var', Type('WORD'))
  elif isinstance(exp, Call):
    target_func = functionset[exp.function]

    for i in range(len(exp.arguments)):
      typ = ('var', target_func.vars[target_func.params[i]][0])
      assertType(exp.arguments[i], typ, line, funcname, func)

    return ('var', lookup[exp.function][1])
  else:
    raise ManoAnalyserError('Unrecognize expression type encountered.')
