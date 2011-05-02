from misc import ManoParserError, isValidIdentifier, isValueOfType, UNARY_OPS, BINARY_OPS


class Type(object):
  def __init__(self, name, size=None):
    if name == 'WORD':
      self.name = name
      self.size = 1
    elif name in ('STRING', 'ARRAY'):
      if size is not None and size > 0:
        self.name = name
        self.size = size
      else:
        raise ManoParserError('Invalid var size.')
    else:
      raise ManoParserError('Invalid type.')

  def __repr__(self):
    if self.name == 'WORD':
      return self.name
    else:
      return '%s[%d]' % (self.name, self.size)

  def __eq__(self, other):
    return (type(other) == type(self) and
            self.name == other.name and 
            self.size == other.size)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(self.name + str(Self.size))


class CodeLine(object):
  def __init__(self, label, condition):
    self.label = label
    self.condition = condition

  def __repr__(self):
    out = ''
    if self.label:
      out += ' %s: ' % self.label
    if self.condition:
      out += ' %s ? ' % self.condition
    return out

class GotoLine(CodeLine):
  def __init__(self, target, label=None, condition=None):
    if not isValidIdentifier(target):
      raise ManoParserError('Invalid identifier in goto statement.')

    self.target = target
    CodeLine.__init__(self, label, condition)

  def __repr__(self):
    return '%s GOTO %s' % (CodeLine.__repr__(self), self.target)

class PrintLine(CodeLine):
  def __init__(self, target=None, label=None, condition=None):
    if target and not isValidIdentifier(target):
      raise ManoParserError('Invalid identifier in print statement.')

    self.target = target
    CodeLine.__init__(self, label, condition)

  def __repr__(self):
    return '%s PRINT %s' % (CodeLine.__repr__(self), self.target or '(New line)')

class ReadLine(CodeLine):
  def __init__(self, target, label=None, condition=None):
    if not isValidIdentifier(target):
      raise ManoParserError('Invalid identifier in read statement.')

    self.target = target
    CodeLine.__init__(self, label, condition)

  def __repr__(self):
    return '%s READ %s' % (CodeLine.__repr__(self), self.target)

class ReturnLine(CodeLine):
  def __init__(self, target=None, label=None, condition=None):
    if target and not isValidIdentifier(target):
      raise ManoParserError('Invalid identifier in return statement.')

    self.target = target
    CodeLine.__init__(self, label, condition)

  def __repr__(self):
    return '%s RETURN %s' % (CodeLine.__repr__(self), self.target or '(None)')

class AssignLine(CodeLine):
  def __init__(self, target, expression, index=None, label=None, condition=None):
    if target and not isValidIdentifier(target):
      raise ManoParserError('Invalid identifier in assignment statement.')
    if index and not isValidIdentifier(index):
      raise ManoParserError('Invalid index in assignment statement.')
    if not isinstance(expression, Expression):
      raise ManoParserError('Invalid expression in assignment statement.')

    self.target = target
    self.index = index
    self.expression = expression
    CodeLine.__init__(self, label, condition)

  def __repr__(self):
    return '%s %s = %s' % (CodeLine.__repr__(self), self.target, self.expression)


class Expression(object):
  pass


class Call(Expression):
  def __init__(self, function, arguments):
    if not isValidIdentifier(function):
      raise ManoParserError('Invalid function identifier in call expression.')

    self.function  = function
    self.arguments = []

    for i in arguments:
      if not isValidIdentifier(i):
        raise ManoParserError('Invalid argument identifier in call expression.')

      self.arguments.append(i)

  def __repr__(self):
    return '%s(%s)' % (self.function, ', '.join(self.arguments))

class Identifier(Expression):
  def __init__(self, name, index=None):
    if not isValidIdentifier(name):
      raise ManoParserError('Invalid base identifier name.')
    if index and not isValidIdentifier(index):
      raise ManoParserError('Invalid index identifier name.')

    self.name  = name
    self.index = index

  def __repr__(self):
    if self.index:
      return '%s[%s]' % (self.name, self.index)
    else:
      return self.name

class UnaryOperation(Expression):
  def __init__(self, operator, operand):
    if operator not in UNARY_OPS:
      raise ManoParserError('Invalid unary operator.')
    if not isValidIdentifier(operand):
      raise ManoParserError('Invalid operand for unary operator %s.' % operator)

    self.operator = operator
    self.operand  = operand

  def __repr__(self):
    return '%s%s' % (self.operator, self.operand)

class BinaryOperation(Expression):
  def __init__(self, operator, left, right):
    if operator not in BINARY_OPS:
      raise ManoParserError('Invalid binary operator.')
    if not isValidIdentifier(left):
      raise ManoParserError('Invalid left operand for operator %s.' % operator)
    if not isValidIdentifier(right):
      raise ManoParserError('Invalid right operand for operator %s.' % operator)

    self.operator = operator
    self.left   = left
    self.right  = right

  def __repr__(self):
    return '%s%s%s' % (self.left, self.operator, self.right)


class Function(object):
  def __init__(self):
    self.params = []
    self.vars   = {}
    self.consts = {}

    self.return_type = None

    self.code   = []

  def setReturnType(self, typ):
    if typ is not None and not isinstance(typ, Type):
      raise ManoParserError('Attempted assign a non-Type object as function '
                            'return type.')

    self.return_type = typ

  def addCodeLine(self, line):
    if not isinstance(line, CodeLine):
      raise ManoParserError('Attempted to assign a non-CodeLine object as '
                            'function code.')

    self.code.append(line)

  def addVar(self, name, typ):
    if not isValidIdentifier(name):
      raise ManoParserError('Invalid identifier name.')
    if name in self.vars or name in self.params:
      raise ManoParserError('Duplicate variable declaration.')
    if not isinstance(typ, Type):
      raise ManoParserError('Attempted assign a non-Type object as '
                            'variable type.')

    self.vars[name] = (typ, None)

  def addParam(self, name, typ):
    if not isValidIdentifier(name):
      raise ManoParserError('Invalid identifier name.')
    if name in self.vars or name in self.params:
      raise ManoParserError('Duplicate parameter declaration.')
    if not isinstance(typ, Type):
      raise ManoParserError('Attempted to assign a non-Type object as '
                            'parameter type.')

    self.params.append(name)
    self.vars[name] = (typ, None)

  def addConst(self, name, typ, value=None):
    if not isValidIdentifier(name):
      raise ManoParserError('Invalid const identifier.')
    if name in self.vars or name in self.params:
      raise ManoParserError('Duplicate constant declaration.')
    if not isinstance(typ, Type):
      raise ManoParserError('Attempted to assign a non-Type object as '
                            'constant type.')
    if not isValueOfType(value, typ):
      raise ManoParserError('Attempted to assign an invalid default value.')

    self.vars[name] = (typ, value)

  def __repr__(self):
    out = []
    out.append('(%s) -> %s' % (', '.join(self.params), self.return_type))

    out.append('  vars:')
    for i in sorted(self.vars):
      out.append('  %s %s' % (self.vars[i][0], i))

    out.append('  code:')
    for i in self.code:
      out.append('  %s' % i)

    return '\n'.join(out)

