#!/usr/bin/python2

import sys
import mparser
import analyser
import collapser
import generator


def compile(infile, outfile, optimize=False):
  generator.OPTIMIZED_MODE = optimize
  fset = mparser.parse_program(open(infile).read())
  analyser.analyse_program(fset)
  collapser.collapse_program(fset)
  out = generator.generate_program(fset)
  open(outfile, 'w').write(out)


if __name__ == '__main__':
  args = sys.argv[1:]

  if len(args) == 3 and args[0] == '-O':
    compile(args[1], args[2], True)
  elif len(args) == 2 and args[0] == '-O':
    compile(args[1], 'out.txt', True)
  elif len(args) == 2:
    compile(args[0], args[1], False)
  elif len(args) == 1:
    compile(args[0], 'out.txt', False)
  else:
    print 'Usage: compiler [-O] source_file [object_file]'
