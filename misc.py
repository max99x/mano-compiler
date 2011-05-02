import re
import tokenize


RESERVED  = ['FUNC', 'END', 'RETURN', 'RETURNS', 'PRINT', 'READ', 'GOTO',
             'WORD', 'ARRAY', 'STRING', 'VARS', 'CODE']
UNARY_OPS = ['-', '~']
BINARY_OPS= ['-', '+', '/', '*', '%', '&', '|', '^', '<<', '>>', '==', '!=',
             '>', '>=', '<', '<=']
RE_IDENTIFIER = re.compile('^[A-Za-z][A-Za-z0-9_]*$')
RE_STRING = re.compile(r'''^"([^"]|\")*"|'([^']|\')*'$''')
CURLINE = 1


class ManoParserError(Exception):
  def __init__(msg):
    Exception.__init__(self, 'Line %d: %s' % (CURLINE, msg))
class ManoGeneratorError(Exception):
  pass
class ManoCollapserError(Exception):
  pass
class ManoAnalyserError(Exception):
  pass


def isValidIdentifier(item):
  return (item not in RESERVED and
          (RE_IDENTIFIER.match(item) or item.startswith('_CONST')))


def isValidString(item):
  return RE_STRING.match(item)


def isValueOfType(value, type):
  if (type.name == 'WORD' and
    isinstance(value, int)):
      return True
  elif (type.name == 'STRING' and
      isinstance(value, str) and
      len(value) < type.size):
      return True
  elif (type.name == 'ARRAY' and
      isinstance(value, list) and
      all([isinstance(i, int) for i in value]) and
      len(value) < type.size):
      return True
  else:
    return False


class tokenizer(object):
  def __init__(self, text):
    self.finished = False
    self._curline = 1
    self._gen = tokenize.generate_tokens(self._lines(text).next)
    self._line = []

    self._endnext = False
    self._nextline= []

    self.peek()

    global CURLINE
    CURLINE = 1

  def _lines(self, text):
    start = 0

    for i in xrange(len(text)):
      if text[i] == '\n':
        if text[start:i] and not text[start:i].isspace(): yield text[start:i]
        start = i+1

    yield text[start:]

  def read(self):
    line = self._nextline
    self._nextline = []

    self.peek()
    if self._endnext:
      self.finished = True

    global CURLINE
    CURLINE += 1

    return line

  def peek(self):
    if self._nextline:
      return self._nextline

    if self.finished:
      raise ManoParserError, 'No lines remaining.'

    for i in self._gen:
      if self._curline != i[2][0]:
        self._curline += 1
        line = self._line

        if i[1] and not i[1].isspace():
          self._line = [i[1]]
        else:
          self._line = []

        self._nextline = line

        return line

      if i[1] and not i[1].isspace(): self._line.append(i[1])

    self._endnext = True

  def __nonzero__(self):
    return not self.finished
