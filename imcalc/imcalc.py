'''imcalc - image calculator in rpn'''

import sys
#from optparse import OptionParser  # optparse is deprecated - what's new?
import numpy as np
from astropy.io import fits

def positive(number):
    '''Return number

    This is an analogue to np.negative to cater for expression '%1 +'.
    '''
    return number

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



def imcalc(command, filenames):
    '''Function to perform image calculations

Parameters
----------
    command [str]:
        Command to perform. FITS file names are referenced by '%1', '%2', etc.
    filenames [list]:
        list of names of FITS files

Returns
-------
   A FITS HDU.

'''
    # parse command line options
    tokenlist = command.split()

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

    return fits.PrimaryHDU(result)


def main(argv):
    '''Analyse command line options'''
    commandstr = argv[1]
    filelist = argv[2:]

    outhdu = imcalc(commandstr, filelist)
    outhdu.writeto(sys.stdout)


if __name__ == "__main__":
    main(sys.argv)
