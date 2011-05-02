from misc import ManoGeneratorError
from objs import *


BUFFER = []
SERIAL = 0
OPTIMIZED_MODE = True


class AsmLine(object):
  def __init__(self, label, instruction, target, indirect, comment):
    self.label = label
    self.instruction = instruction
    self.target = target
    self.indirect = indirect
    self.comment = comment


def genName(prefix='id'):
  global SERIAL
  name = prefix[:3] + '%03d' % SERIAL
  SERIAL += 1
  return name


def emit(instruction, label=None, comment=None):
  if instruction:
    parts = instruction.split()
    if len(parts) == 3:
      (instruction, target) = parts[:2]
      indirect = True
    elif len(parts) == 2:
      (instruction, target) = parts
      indirect = False
    else:
      instruction = parts[0]
      target = None
      indirect = False

    line = AsmLine(label, instruction, target, indirect, comment)

    if OPTIMIZED_MODE and BUFFER:
      lastLine = BUFFER[-1]
      if lastLine.instruction == 'NOP' and line.label is None:
        line.label = lastLine.label
        BUFFER.pop()
      elif (lastLine.instruction == 'BSA' and
            lastLine.target == 'push' and
            lastLine.indirect == False and
            line.instruction == 'BSA' and
            line.target == 'pop' and
            line.indirect == False):
        BUFFER.pop()
        return
      elif (lastLine.instruction == 'STA' and
            line.instruction == 'LDA' and
            lastLine.target == line.target and
            lastLine.indirect == line.indirect):
        BUFFER.pop()
        return
    BUFFER.append(line)
  elif not OPTIMIZED_MODE:
    BUFFER.append(None)  # Empty line.


def concatenate(buffer):
  for i in xrange(len(buffer)):
    if buffer[i]:
      if buffer[i].instruction == 'NOP':
        buffer[i].instruction = 'CLE'
        if not buffer[i].comment:
          buffer[i].comment = 'NOP'

      if buffer[i].label:
        line = '%-11s %3s %-6s %s' % (buffer[i].label+',',
                        buffer[i].instruction,
                        buffer[i].target or '',
                        'I' if buffer[i].indirect else ' ')
      else:
        line = (' ' * 12) + '%3s %-6s %s' % (buffer[i].instruction,
                           buffer[i].target or '',
                           'I' if buffer[i].indirect else ' ')

      if buffer[i].comment and not OPTIMIZED_MODE:
        line = line + ' ;' + buffer[i].comment

      buffer[i] = line
    else:
      buffer[i] = ''

  return '\n'.join(buffer) + '\n'


def generate_program(functionset):
  if not (isinstance(functionset, dict) and functionset.has_key('main')):
    raise ManoGeneratorError, 'Program contains no "main" function.'

  global BUFFER, SERIAL

  BUFFER = []
  SERIAL = 0

  # Entry point.
  emit('ORG 0', comment='Entry point')
  emit('LDA main')
  emit('BSA push')
  emit('BSA call')
  emit('HLT')

  for k in functionset:
    emit('')
    emit('')
    generate_function(k, functionset[k])

  return concatenate(BUFFER)


def generate_function(name, func):
  generate_vars(func)
  emit('')

  funcname = genName('fnc')
  # AddressOf actual function
  emit('AND %s' % funcname, name, 'Address of %s' % name)
  # Just for the label.
  emit('NOP', funcname, 'Function %s' % name)

  emit('BSA pop', comment='Getting return address')
  emit('STA temp1')
  for varname in reversed(func.params):
    emit('BSA pop', comment='Processing arg %s' % varname)
    emit('STA %s' % varname)
  emit('LDA temp1')
  emit('BSA push', comment='Putting return address back')

  generate_code(func)


def generate_vars(func):
  for varname in sorted(func.vars.keys()):
    (type, value) = func.vars[varname]
    if type.name == 'WORD':
      emit('DEC %d' % (value or 0), varname)
    else:
      if varname in func.params:
        comment  = 'PARAM: '
      else:
        comment  = ''

      if value:
        comment += '%s[%d] %s = %s' % (type.name, type.size, varname, repr(value))
      else:
        comment += '%s[%d] %s' % (type.name, type.size, varname)

      if value:
        value = [ord(i) for i in value]

      actualName = genName('var')

      emit('AND %s' % actualName, varname, comment)
      emit('DEC %d' % (value[0] if value else 0), actualName)

      for i in xrange(1,type.size):
        if value and len(value) > i:
          emit('DEC %d' % value[i])
        else:
          emit('DEC 0')


def generate_code(func):
  for codeline in func.code:
    condName = None
    if codeline.condition:
      condStart = genName('cnd')
      condEnd = genName('skp')

      emit('LDA %s' % codeline.condition, comment='condition: %s' % codeline.condition)
      emit('SZA')
      emit('BUN %s' % condStart)
      emit('BUN %s' % condEnd)
      emit('NOP', condStart)

    if isinstance(codeline, GotoLine):
      emit('BUN %s' % codeline.target, codeline.label, 'GOTO %s' % codeline.target)
    elif isinstance(codeline, PrintLine):
      generate_print(func, codeline)
    elif isinstance(codeline, ReadLine):
      raise ManoGeneratorError, 'ReadLine not implemented yet.'
    elif isinstance(codeline, ReturnLine):
      generate_return(func, codeline)
    elif isinstance(codeline, AssignLine):
      generate_assign(func, codeline)
    else:
      pass


    if codeline.condition:
      emit('NOP', condEnd)

    emit('')


def generate_print(func, codeline):
  if codeline.target:
    type, junk = func.vars[codeline.target]

    if type.name == 'WORD':
      emit('LDA %s' % codeline.target, codeline.label, 'PRINT word %s' % codeline.target)
      emit('BSA outdec')
    elif type.name == 'STRING':
      emit('LDA %s' % codeline.target, codeline.label, 'PRINT string %s' % codeline.target)
      emit('BSA push')
      emit('BSA outstr')
    elif type.name == 'ARRAY':
      emit('LDA %s' % codeline.target, codeline.label, 'PRINT array %s' % codeline.target)
      emit('STA temp1')
      for i in xrange(type.size):
        emit('LDA temp1 I')
        emit('BSA outdec')
        emit('LDA chrspc')
        emit('BSA outchr')
        emit('ISZ temp1', comment='Always > 0 so just a memory INC')
      emit('BSA outnln')
    else:
      raise ManoGeneratorError, 'Unrecognized type in PRINT sentence.'
  else:
    emit('BSA outnln', codeline.label, 'Print new line')


def generate_return(func, codeline):
  emit('BSA pop', codeline.label, comment='RETURN %s' % (codeline.target or ''))
  emit('STA temp1')

  emit('LDA %s' % (codeline.target or 'null'))
  emit('BSA push')

  emit('BUN temp1 I')


def generate_assign(func, codeline):
  if codeline.target:
    comment  = '{%s} %s' % (func.vars[codeline.target][0], codeline.target)
    if codeline.index is not None:
      comment += '[' + codeline.index + ']'
    comment += ' = '
  else:
    comment = ''
  comment += str(codeline.expression)


  emit('NOP', codeline.label, comment)

  generate_expression(func, codeline.expression)

  if codeline.target:
    if codeline.index is None:
      if func.vars[codeline.target][0].name == 'WORD':
        emit('BSA pop')
        emit('STA %s' % codeline.target)
      else:
        emit('LDA %s' % codeline.target)
        emit('STA temp1')
        emit('BSA pop')
        emit('STA temp2')

        for i in xrange(func.vars[codeline.target][0].size):
          emit('LDA temp2 I')
          emit('STA temp1 I')
          emit('ISZ temp1', comment='Always > 0 so just a memory INC')
          emit('ISZ temp2', comment='Always > 0 so just a memory INC')
    else:
      #Calculate effective address
      emit('LDA %s' % codeline.target)
      emit('ADD %s' % codeline.index)
      emit('STA temp1')

      #Assign
      emit('BSA pop')
      emit('STA temp1 I')
  else:
    emit('BSA pop')


def generate_expression(func, expression):
  if isinstance(expression, Identifier):
    generate_exp_identifier(func, expression)
  elif isinstance(expression, Call):
    generate_exp_call(func, expression)
  elif isinstance(expression, UnaryOperation):
    generate_exp_unary(func, expression)
  elif isinstance(expression, BinaryOperation):
    generate_exp_binary(func, expression)
  else:
    raise ManoGeneratorError, 'Unrecognized expression type in assignment sentence.'


def generate_exp_identifier(func, expression):
  if expression.index is None:

    emit('LDA %s' % expression.name)
    emit('BSA push')
  else:
    #Calculate effective address
    emit('LDA %s' % expression.name)
    emit('ADD %s' % expression.index)
    emit('STA temp1')

    #Return value
    emit('LDA temp1 I')
    emit('BSA push')


def generate_exp_call(func, expression):
  for arg in expression.arguments:
    emit('LDA %s' % arg)
    emit('BSA push')

  emit('LDA %s' % expression.function)
  emit('BSA push')
  emit('BSA call')


def generate_exp_unary(func, expression):
  if expression.operator == '-':
    emit('LDA %s' % expression.operand)
    emit('BSA neg')
    emit('BSA push')
  elif expression.operator == '~':
    emit('LDA %s' % expression.operand)
    emit('CMA')
    emit('BSA push')
  else:
    raise ManoGeneratorError, 'Unrecognized unary operand in assignment sentence.'



def generate_exp_binary(func, expression):
  if expression.operator == '+':
    emit('LDA %s' % expression.left)
    emit('ADD %s' % expression.right)
    emit('BSA push')
  elif expression.operator == '-':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA sub')
    emit('BSA push')
  elif expression.operator == '*':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA mul')
    emit('BSA push')
  elif expression.operator == '/':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA div')
    emit('BSA push')
  elif expression.operator == '%':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA mod')
    emit('BSA push')
  elif expression.operator == '&':
    emit('LDA %s' % expression.left)
    emit('AND %s' % expression.right)
    emit('BSA push')
  elif expression.operator == '|':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA or')
    emit('BSA push')
  elif expression.operator == '^':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA xor')
    emit('BSA push')
  elif expression.operator == '<<':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA shftl')
    emit('BSA push')
  elif expression.operator == '>>':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA shftr')
    emit('BSA push')
  elif expression.operator == '==':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA equal')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  elif expression.operator == '!=':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA nequal')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  elif expression.operator == '<':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA less')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  elif expression.operator == '<=':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA lesseq')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  elif expression.operator == '>':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA more')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  elif expression.operator == '>=':
    emit('LDA %s' % expression.right)
    emit('BSA push')
    emit('LDA %s' % expression.left)
    emit('BSA moreeq')
    emit('CLA')
    emit('CIL')
    emit('BSA push')
  else:
    raise ManoGeneratorError, 'Unrecognized binary operand in assignment sentence.'


