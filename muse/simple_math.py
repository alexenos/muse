from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import map
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
#\!/usr/bin/python2.4

# A really simple expression evaluator supporting the
# four basic math functions, parentheses, and variables.

# Initial Code from:
# Blake at http://www.nerdparadise.com/tech/python/parsemath/

# Modifications:
# Dax Garner 4/2012 Modified for initial use in trick_plot
#                   Removed exception handling; added functionality (std, mean, ...)
#                   Supports simple element operations on time-series vectors of length three
#                      - Note: vector * vector is not a dot or cross product!

import sys
from . import pputils
import numpy as np
import math
from . import pputils as pp


class Parser(object):

    def __init__(self, string, vars={}):
        self.string = string
        self.index = 0
        self.expand = True
        self.vars = {
            'pi': np.pi
        }
        self.funcs = {
            'std': lambda x: np.std(x),
            'mean': lambda x: [np.mean(x)],
            'log': lambda x: self.parseFuncArguments('LOG10', x, 1),
            'rss': lambda x: self.parseFuncArguments('RSS',   x, 3),
            'last': lambda x: self.LAST(x),
            'max': lambda x: [max(x)],
        }
        for var in vars:
            if self.vars.get(var) != None:
                print("Cannot redefine the value of " + var)
            self.vars[var] = vars[var]

    def getValue(self, size=1):
        value = self.parseExpression()
        if type(value) == type([]) or type(value) == type(np.array([])):
            value = list(value)
        self.skipWhitespace()
        if self.hasNext():
            print("Unexpected character found: '" + self.peek() + "' at index " + str(self.index))
        value, length = self.getBaseValue(value)

        if self.expand and size > 1 and (type(value) != type([]) and type(value) != type(np.array([]))):
            val_array = []
            for i in range(size):
                val_array.append(value)
            value = val_array

        return value, length

    def getBaseValue(self, value):
        if type(value) != type([]) and type(value) != type(np.array([])):
            length = 1
            value = self.getPrecision(value)
        else:
            length = len(value)
            for i in range(length):
                value[i], l = self.getBaseValue(value[i])
        return value, length

    def getPrecision(self, value):
        if math.isnan(value):
            return float(0.0)
        # Return a negative integer value
        if value < 0 and int(-value) == -value:
            return -int(-value)
        # Return a positive integer type if the answer is an integer
        if int(value) == value:
            return int(value)
        # If Python made some silly precision error
        # like x.99999999999996, just return x + 1 as an integer
        epsilon = 0.0000000001
        if int(value + epsilon) != int(value):
            value = int(value + epsilon)
        elif int(value - epsilon) != int(value):
            value = int(value)
        return value

    def peek(self):
        return self.string[self.index:self.index + 1]

    def hasNext(self):
        return self.index < len(self.string)

    def skipWhitespace(self):
        while self.hasNext():
            if self.peek() in ' \t\n\r':
                self.index += 1
            else:
                return

    def parseExpression(self):
        return self.parseAddition()

    def parseAddition(self):
        flag = False
        values = [self.parseMultiplication()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '+':
                flag = True
                self.index += 1
                values.append(self.parseMultiplication())
            elif char == '-':
                flag = True
                self.index += 1
                negative = self.parseMultiplication()
                values.append(self.applyNegative(negative))
            else:
                break
        value = self.Array_Op('Add', values, flag)
        return value

    def applyNegative(self, values):
        negative = 0
        if type(values) == type([]) or type(values) == type(np.array([])):
            negative = []
            for v in values:
                negative.append(self.applyNegative(v))
        else:
            negative = -values
        return negative

    def Array_Op(self, Op, A, flag):
        if flag:                                                                 # Operate
            # Gather information about any arrays present
            array_info = self.array_check(A)
            # If all arrays are the same length,
            if self.length_check(A, array_info['lengths']):
                if array_info['flag']:  # If there is at least one array, repackage and regress
                    B = []  # Set B to empty array, B will be of array type
                    # For each index in an array of A
                    for i in range(len(A[array_info['index']])):
                        C = []  # Construct new array for regression operation
                        for j in range(len(A)):  # For each index in A
                            if type(A[j]) == type([]) or type(A[j]) == type(np.array([])):  # If value is an array
                                C.append(A[j][i])  # Append value in new array
                            else:  # Else, value is a scalar
                                # Append scalar value in new array
                                C.append(A[j])
                        # Operate on constructed array
                        B.append(self.Array_Op(Op, C, flag))
                else:  # Else, operate on the scalar values
                    B = eval('self.' + Op + '(A)')  # Operate on scalar values
            else:  # Else, arrays not the same length
                print('Error: Inconsistent Array Lengths')  # Print error.
        # Do not operate, pass through.
        else:
            if type(A) == type([]) or type(A) == type(np.array([])):  # If A is an array.
                if len(A) == 1:  # If A is a single array within a
                    B = A[0]  # Remove extra array structure.
                else:  # Else, multiple values (either array or scalars).
                    B = A  # Direct pass through.
            else:  # Else, no array
                B = A  # Direct pass through.
        # Return result.
        return B

    def array_check(self, A):
        # Default false. If at least one array is within A, flag becomes true
        array_flag = False
        # Index for an array if present. Happens to be the last array in A
        last_array = 0
        # Array of array lengths for check later.
        array_length = []
        # For each index in A, determine if array and length of array
        for i in range(len(A)):
            if type(A[i]) == type([]) or type(A[i]) == type(np.array([])):  # If array
                array_flag = True  # Set array flag, at least one value is an array
                last_array = i  # Set index for the last array in A
                array_length.append(len(A[i]))  # Set array length
            else:  # Otherwise, not an array
                array_length.append(1)  # Set array length as 1
        # Return array information
        return {'flag': array_flag, 'index': last_array, 'lengths': array_length}

    def length_check(self, A, lengths):
        # Default True. Only two arrays with unequal lengths set False
        check = True
        # For each index in A, check for consistent array lengths
        for i in range(len(A)):
            if type(A[i]) == type([]) or type(A[i]) == type(np.array([])):  # If array
                for j in range(len(A)):  # For each index in A
                    if (type(A[j]) == type([]) or type(A[j]) == type(np.array([]))) and i != j:  # If array and not the same array
                        check = check and lengths[i] == lengths[j]  # Check length
        # Return whether the array match (True) or not (False)
        return check

    def Add(self, values):
        value = sum(values)
        return value

    def parseMultiplication(self):
        flag = False
        values = [self.parseExponent()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '*':
                flag = True
                self.index += 1
                values.append(self.parseExponent())
            elif char == '/':
                flag = True
                div_index = self.index
                self.index += 1
                denominator = self.parseExponent()
                values.append(self.applyDivision(denominator, div_index))
            else:
                break
        value = self.Array_Op('Mult', values, flag)
        return value

    def applyDivision(self, values, index):
        if type(values) == type([]) or type(values) == type(np.array([])):
            denominator = []
            for d in values:
                if d == 0:
                    print("Division by 0 kills baby whales (occured at index " + str(index) + ")")
                denominator.append(self.applyDivision(d, index))
        else:
            if values == 0:
                print("Division by 0 kills baby whales (occured at index " + str(index) + ")")
            denominator = old_div(1.0, values)
        return denominator

    def Mult(self, A):
        # Set B to one for multiplication
        B = 1
        for value in A:                                                          # For each value in A
            B *= value  # Multiply
        # Return result.
        return B

    def parseParenthesis(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '(':
            self.index += 1
            value = self.parseExpression()
            self.skipWhitespace()
            if self.peek() != ')':
                print("No closing parenthesis found at character " + str(self.index))
            self.index += 1
            return value
        else:
            return self.parseNegative()

    def parseExponent(self):
        flag = False
        values = [self.parseParenthesis()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '^':
                flag = True
                self.index += 1
                values.append(self.parseParenthesis())
            else:
                break
        value = self.Array_Op('Exp', values, flag)
        return value

    def Exp(self, A):
        # Set counter to length of array minus one
        n = len(A) - 1
        # Initialize B to last value in array
        B = A[n]
        # While n is greater than one. (move through the array backwards)
        while n >= 1:
            n = n - 1  # Iterate n one less
            B = A[n]**B  # Raise the next value by the exponent
        # Return result
        return B

    def parseNegative(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '-':
            self.index += 1
            return -1 * self.parseParenthesis()
        else:
            return self.parseValue()

    def parseValue(self):
        self.skipWhitespace()
        char = self.peek()
        if char in '0123456789.':
            return self.parseNumber()
        else:
            return self.parseVariable()

    def parseVariable(self):
        self.skipWhitespace()
        var = ''
        while self.hasNext():
            char = self.peek()
            if char.lower() in '._abcdefghijklmnopqrstuvwxyz0123456789[]':
                var += char
                self.index += 1
            else:
                break
        value = self.vars.get(var, None)
        if type(value) == type({}):
            value = self.vars.get(var, None).get('data', None)
        elif value == None:
            if self.findKey(var):
                value = self.parseKey(var)
            elif value == None:
                try:
                    value = self.funcs[var](self.parseParenthesis())
                except KeyError:
                    print("Unknown variable or function: " + var + ", in plot definition.")
                    pp.end_script(-1)
            else:
                print("Unrecognized variable or function: '" + var + "'")
        return value

    def findKey(self, key):
        flag = True
        for i in range(3):  # Currently only works for vectors (arrays of length 3)
            key_full = key + '[' + str(i) + ']'
            if key_full not in self.vars:
                flag = flag and False
        return flag

    def parseKey(self, key):
        x = self.vars.get(key + '[0]')  # .get('data', None)
        y = self.vars.get(key + '[1]')  # .get('data', None)
        z = self.vars.get(key + '[2]')  # .get('data', None)
        return [x, y, z]

    def parseNumber(self):
        self.skipWhitespace()
        strValue = ''
        decimal_found = False
        char = ''
        while self.hasNext():
            char = self.peek()
            if char == '.':
                if decimal_found:
                    print("Found an extra period in a number at character " + str(self.index) + ". Are you European?")
                decimal_found = True
                strValue += '.'
            elif char in '0123456789':
                strValue += char
            else:
                break
            self.index += 1

        if len(strValue) == 0:
            if char == '':
                print("Unexpected end found")
            else:
                print("I was expecting to find a number at character " + str(self.index) + " but instead I found a '" + char + "'. What's up with that?")
        return float(strValue)

    def parseFuncArguments(self, Op, x, num_args):
        # If the argument is a list/array
        if type(x) == type([]) or type(x) == type(np.array([])):
            args = ''  # Instantiate string list of arguments
            for i in range(len(x) - 1):  # For each argument in list, except the last
                # Append the argument in the argument string list
                args = args + 'x[' + str(i) + '], '
            # Append the last argument to the string, with no comma
            args = args + 'x[' + str(len(x) - 1) + ']'
            # If the first argument is an array/list and the number of
            # arguments is expected
            if (type(x[0]) == type([]) or type(x[0]) == type(np.array([]))) and len(x) == num_args:
                # Apply funtion iteratively (map) through the list of
                # arguments, return
                return eval('map(' + 'self.' + Op + ', ' + args + ')')
            # Else, If only the length of the x matches the number of expected
            # arguments
            elif len(x) == num_args:
                # Evaluate function with arguments and return
                return eval('self.' + Op + '(' + args + ')')
            else:  # Else,
                # Apply function iteratively (map) with the list of arguemnts
                # directly passed, return
                return list(map(eval('self.' + Op), x))
        else:                                                                  # Else, argument is a scalar
            # Valuate function with argument and return
            return eval('self.' + Op + '(x)')

    def RSS(self, a, b, c):
        return math.sqrt(a * a + b * b + c * c)

    def LOG10(self, x):
        return np.log10(x)

    def LAST(self, x):
        self.expand = False
        return x[-1]


def evaluate(expression, vars={}, size=1):
    p = Parser(expression, vars)
    return p.getValue(size)
