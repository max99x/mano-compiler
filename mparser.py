from objs import *
from misc import ManoParserError, isValidIdentifier, isValueOfType, tokenizer, UNARY_OPS, BINARY_OPS

def parse_program(text):
  functions = {}
  tokenlist = tokenizer(text)

  try:
    while tokenlist:
      func = Function()

      funcname = parse_func_head(tokenlist, func)
      parse_vars(tokenlist, func)
      parse_code(tokenlist, func)

      func.addCodeLine(ReturnLine())

      key = tokenlist.read()
      if key != ['END']:
        raise ManoParserError('No END found after function header.')

      functions[funcname] = func
  except:
    raise

  return functions


def parse_func_head(tokenlist, func):
  line = tokenlist.read()

  try:
    key = line.pop(0)
    if key != 'FUNC':
      raise ManoParserError('Non-function statement in global scope.')

    name = line.pop(0)
    if not isValidIdentifier(name):
      print name
      raise ManoParserError('Invalid function name.')

    key = line.pop(0)
    if key != '(':
      raise ManoParserError('No parenthesis found after function name.')

    while line[0] != ')':
      vartype = parse_type(line)
      varname = line.pop(0)
      if not isValidIdentifier(varname):
        raise ManoParserError('Invalid parameter name.')

      func.addParam(varname, vartype)

      if line[0] == ',':
        line.pop(0)

    key = line.pop(0)
    if key != ')':
      raise ManoParserError('No parenthesis found after parameters.')

    key = line.pop(0)
    if key != 'RETURNS':
      raise ManoParserError('Could not find "RETURNS" in function header.')

    rettype = parse_type(line)
    func.setReturnType(rettype)

    key = line.pop(0)
    if key != ':':
      raise ManoParserError('No colon found after function header.')

    if len(line):
      raise ManoParserError('Garbage found after function header.')
  except IndexError:
    raise ManoParserError('Error parsing function header.')

  return name


def parse_vars(tokenlist, func):
  line = tokenlist.read()

  if line != ['VARS', ':']:
    raise ManoParserError('Error parsing vars header.')

  while tokenlist.peek() != ['CODE', ':']:
    line = tokenlist.read()

    vartype = parse_type(line)
    varname = line.pop(0)
    if not isValidIdentifier(varname):
      raise ManoParserError('Invalid variable name.')

    if len(line):
      raise ManoParserError('Garbage found after var declaration.')

    func.addVar(varname, vartype)


def parse_code(tokenlist, func):
  line = tokenlist.read()

  if line != ['CODE', ':']:
    raise ManoParserError('Error parsing code header.')

  label = None
  while tokenlist.peek() != ['END']:
    try:
      line = tokenlist.read()

      # Non-statements.
      if line[0][0] == '#':
        continue
      elif len(line) >= 2 and line[1] == ':':
        label = line[0]
        continue

      # Condition
      condition = None
      if len(line) >= 2 and line[1] == '?':
        condition = line.pop(0)
        line.pop(0)

      # Statement.
      if line[0] == 'GOTO':
        code  = GotoLine(line[1], label, condition)
      elif line[0] == 'READ':
        code  = ReadLine(line[1], label, condition)
      elif line[0] == 'PRINT':
        if len(line) == 1:
          code  = PrintLine(None, label, condition)
        else:
          if not isValidIdentifier(line[1]):
            line[1] = create_constant(line[1], func)
          code  = PrintLine(line[1], label, condition)
      elif line[0] == 'RETURN':
        if len(line) > 1:
          code  = ReturnLine(line[1], label, condition)
        else:
          code  = ReturnLine(None, label, condition)
      elif '=' in line:
        target = line.pop(0)

        if line[0] == '[' and line[2] == ']':
          index = line[1]
          if not isValidIdentifier(index):
            index = create_constant(index, func)
          line = line [3:]
        else:
          index = None

        line.pop(0)  # =
        expression = parse_expression(line, func)
        code = AssignLine(target, expression, index, label, condition)
      elif line[1] == '(' and line[-1] == ')':
        expression = parse_expression(line, func)
        code = AssignLine(None, expression, None, label, condition)
      else:
        raise ManoParserError('Could not parse statement.')
    except IndexError:
      raise ManoParserError('Error parsing statement.')

    func.addCodeLine(code)
    label = None


def parse_expression(tokens, func):
  if len(tokens) == 1:
    if isValidIdentifier(tokens[0]):
      return Identifier(tokens[0])
    else:
      return Identifier(create_constant(tokens[0], func))
  elif len(tokens) == 4 and tokens[1] == '[' and tokens[-1] == ']':
    name  = tokens[0]
    index = tokens[2]

    if not isValidIdentifier(index):
      index = create_constant(index, func)

    return Identifier(name, index)
  elif len(tokens) >= 3 and tokens[1] == '(' and tokens[-1] == ')':
    calltarget = tokens[0]
    arg_tokens = tokens[2:-1]
    arguments  = []

    for i in xrange(0, len(arg_tokens), 2):
      if not isValidIdentifier(arg_tokens[i]):
        arguments.append(create_constant(arg_tokens[i], func))
      else:
        arguments.append(arg_tokens[i])

    return Call(calltarget, arguments)
  elif tokens[0] in UNARY_OPS:
    operator = tokens[0]
    operand  = tokens[1]

    if not isValidIdentifier(operand):
      operand = parse_number([operand])
      value = eval(operator + str(operand))
      return Identifier(create_constant(str(value), func))

    return UnaryOperation(operator, operand)
  elif tokens[1] in BINARY_OPS:
    operator = tokens[1]
    left   = tokens[0]
    right  = tokens[2]

    if not isValidIdentifier(left) and not isValidIdentifier(right):
      left = parse_number(left)
      right = parse_number(right)
      value = eval(str(left) + operator + str(right))
      return Identifier(create_constant(str(value), func))

    if not isValidIdentifier(left):
      left = create_constant(left, func)
    if not isValidIdentifier(right):
      right = create_constant(right, func)

    return BinaryOperation(operator, left, right)
  else:
    raise ManoParserError('Could not parse expression.')


def parse_type(tokens):
  type = tokens.pop(0)

  if type == 'NONE':
    return None
  elif type == 'WORD':
    return Type('WORD')
  elif type in ('STRING', 'ARRAY'):
    key = tokens.pop(0)
    if key != '[':
      raise ManoParserError('Invalid type.')

    size = parse_number(tokens)

    key = tokens.pop(0)
    if key != ']':
      raise ManoParserError('Invalid type.')

    return Type(type, size)
  else:
    raise ManoParserError('Invalid type.')


def parse_number(tokens):
  num = tokens.pop(0)

  if num.startswith('0x'):
    num = int(num, 16)
  else:
    num = int(num)

  if num <= 0xffff:
    return num
  else:
    raise ManoParserError('Numeric literal too large.')


def create_constant(value, func):
  name = '_CONST_%02d' % len(func.vars)

  if value[0] == '"':
    func.addConst(name, Type('STRING', len(value)-1), value[1:-1])
  else:
    func.addConst(name, Type('WORD'), parse_number([value]))

  return name
