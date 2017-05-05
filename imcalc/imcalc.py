'''imcalc - image calculator in rpn'''

import sys
from optparse import OptionParser
import numpy as np
from astropy.io import fits

def positive(x):
    return(x)

FUNC2 = {'+' : np.add,
         '-' : np.subtract,
         '*' : np.multiply,
         '/' : np.divide,
         '**' : np.power,
         '^' : np.power,
         'atan2' : np.arctan2}
FUNC1 = {'+' : positive,
         '-' : np.negative,
         'sin' : np.sin,
         'cos' : np.cos,
         'exp' : np.exp,
         'log' : np.log,
         'log10' : np.log10,
         'sqrt' : np.sqrt,
         'asin' : np.arcsin,
         'acos' : np.arccos,
         'atan' : np.arctan}



if __name__ == "__main__":

    # parse command line options
    tokenlist = sys.argv[1].split()
    filenames = sys.argv[2:]

    print("Command: ", tokenlist, file=sys.stderr)
    print("Files: ", filenames, file=sys.stderr)

    images = dict()

    stack = list()

    for token in tokenlist:
        if token[0] == '%':
            index = int(token[1:]) - 1

            if token not in images.keys():
                images[token] = fits.getdata(filenames[index])

            stack.append(images[token])
        elif token in ['+', '-']:   # can be unary or binary
            right = stack.pop()
            try:
                left = stack.pop()
                result = FUNC2[token](left, right)
            except IndexError:
                result = FUNC1[token](right)
            stack.append(result)
        elif token in FUNC1.keys():  # unary operators
            right = stack.pop()
            result = FUNC1[token](right)
            stack.append(result)
        elif token in FUNC2.keys():   # binary operators
            right = stack.pop()
            left = stack.pop()
            result = FUNC2[token](left, right)
            stack.append(result)
        else:
            try:    # test if numerical value
                token = float(token)
                stack.append(token)
            except ValueError:   # unknown
                sys.exit("Undefined operation " + token)


    if len(stack) != 1:
        print("Stack has improper length: ", stack, file=sys.stderr)
    else:
        result = stack.pop()
        fits.writeto(sys.stdout, result)
