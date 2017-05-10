'''imcalc - image calculator in rpn'''

import sys
#from optparse import OptionParser  # optparse is deprecated - what's new?
import argparse

import numpy as np
from astropy.io import fits

def positive(number):
    '''Return number

    This is an analogue to np.negative to cater for expression '%1 +'.
    '''
    return number


def ifelse(logic, truearr, falsearr):
    '''Fill array with values from truearr or falsearr, according to logic'''

    return logic * truearr + (1. - logic) * falsearr


FUNC2 = {'+' : np.add,
         '-' : np.subtract,
         '*' : np.multiply,
         '/' : np.divide,
         '**' : np.power,
         '^' : np.power,
         'pow' : np.power,
         'atan2' : np.arctan2,
         'max' : np.maximum,
         'fmax' : np.fmax,
         'min' : np.minimum,
         'fmin': np.fmin,
         '>' : np.greater,
         '<' : np.less,
         '==' : np.equal,
         '>=' : np.greater_equal,
         '<=' : np.less_equal}

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

FUNC0 = {'rand' : np.random.rand,
         'randn' : np.random.randn}


def imcalc(command, filenames, bitpix=None):
    '''Function to perform image calculations

Parameters
----------
    command [str]:
        Command to perform. FITS file names are referenced by '%1', '%2', etc.
    filenames [list]:
        list of names of FITS files
    bitpix [str or dtype]:
        bitpix of the result

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

    # Get size of image
    naxes = []
    naxes.append(fits.getval(filenames[0], 'NAXIS2'))
    naxes.append(fits.getval(filenames[0], 'NAXIS1'))

    if 'x' in tokenlist:
        xarr = np.mgrid[0:naxes[0], 0:naxes[1]][1] + 1.

    if 'y' in tokenlist:
        yarr = np.mgrid[0:naxes[0], 0:naxes[1]][0] + 1.

    for token in tokenlist:
        if token[0] == '%':     # FITS image
            index = int(token[1:]) - 1

            if token not in images.keys():
                images[token] = fits.getdata(filenames[index])

            stack.append(images[token])
        elif token == 'x':     # X array
            stack.append(xarr)
        elif token == 'y':     # Y array
            stack.append(yarr)
        elif token in ['+', '-']:   # can be unary or binary
            right = stack.pop()
            try:
                left = stack.pop()
                result = FUNC2[token](left, right)
            except IndexError:
                result = FUNC1[token](right)
            stack.append(result)
        elif token in FUNC0.keys():  # functions not operating on an image
            result = FUNC0[token](naxes[1], naxes[0])
            stack.append(result)
        elif token in FUNC1.keys():  # unary operators
            right = stack.pop()
            result = FUNC1[token](right)
            stack.append(result)
        elif token in FUNC2.keys():   # binary operators
            right = stack.pop()
            left = stack.pop()
            result = FUNC2[token](left, right)
            print(result.dtype, file=sys.stderr)
            stack.append(result)
        elif token == '?':
            logic = stack.pop()
            false = stack.pop()
            true = stack.pop()
            result = ifelse(logic, true, false)
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

    header = fits.getheader(filenames[0])
    header.add_history("imcalc '" + command + "'")

    if bitpix is not None:
        print("bitpix: ", bitpix)
        result = result.astype(bitpix)

    return fits.PrimaryHDU(result, header)


def imcreate(command, naxes, bitpix=None):
    '''Create an image of size naxes[0] x naxes[1]

Parameters
----------
    command [str]:
        Command to perform. FITS file names are referenced by '%1', '%2', etc.
    naxes [tuple or array]:
        y and x size of output image
    bitpix [str or dtype]:
        bitpix of the result

Returns
-------
   A FITS HDU.

'''

    # parse command line options
    tokenlist = command.split()

    print("Command: ", tokenlist, file=sys.stderr)

    if 'x' in tokenlist:
        xarr = np.mgrid[0:naxes[0], 0:naxes[1]][1] + 1.

    if 'y' in tokenlist:
        yarr = np.mgrid[0:naxes[0], 0:naxes[1]][0] + 1.


    stack = list()

    for token in tokenlist:
        if token == 'x':
            stack.append(xarr)
        elif token == 'y':
            stack.append(yarr)
        elif token in ['+', '-']:   # can be unary or binary
            right = stack.pop()
            try:
                left = stack.pop()
                result = FUNC2[token](left, right)
            except IndexError:
                result = FUNC1[token](right)
            stack.append(result)
        elif token in FUNC0.keys():  # functions not operating on an image
            result = FUNC0[token](naxes[1], naxes[0])
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
        elif token == '?':
            logic = stack.pop()
            false = stack.pop()
            true = stack.pop()
            result = ifelse(logic, true, false)
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

    header = fits.Header()
    header.add_history("imcalc '" + command + "'")

    if bitpix is not None:
        try:
            result = result.astype(bitpix)
        except TypeError:
            print("is np.int16: ", bitpix is np.int16, file=sys.stderr)
            print("Old type: ", result.dtype, file=sys.stderr)
            print("bitpix: ", bitpix, file=sys.stderr)

    return fits.PrimaryHDU(result, header)


def main(* argv):
    '''Analyse command line options'''

    bitpixmap = {'8' : np.uint8,
                 '16' : np.int16,
                 '32' : np.int32,
                 '-32' : np.float32,
                 '-64' : np.float64}

    def convertvalues(value):
        '''get the value from the bitpixmap dictionary'''
        return bitpixmap.get(value)

    parser = argparse.ArgumentParser(
        description='FITS image calculator',
        epilog='Command string has to be reverse polish')

    # -c : create image, arguments are image size
    parser.add_argument('-c', nargs=2, dest='naxes', type=int)

    # -p : bitpix for output file
    parser.add_argument('-p', dest='bitpix', type=convertvalues)

    # commandstr : command string
    parser.add_argument('commandstr', metavar='command', type=str,
                        help='command string')

    # filelist : FITS files referenced in commandstr
    parser.add_argument('filelist', type=str, nargs='*',
                        help='FITS file names')

    args = parser.parse_args()

    if args.naxes is None:
        outhdu = imcalc(args.commandstr,
                        args.filelist, args.bitpix)
    else:
        outhdu = imcreate(args.commandstr, args.naxes, args.bitpix)

    outhdu.writeto(sys.stdout)


if __name__ == "__main__":
    main(sys.argv)
