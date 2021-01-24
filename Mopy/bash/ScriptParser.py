# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash.  If not, see <https://www.gnu.org/licenses/>.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2020 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

# Parser.py =======================================
#  A generic class for handling parsing of
#  scripts and equations.
#  - The following operators are supported by default:
#   + Addition
#   - Subtraction
#   * Multiplication
#   / Division
#   % Modulus
#   ^ Exponent
#   () Parenthesis
#  - The parser follows the order of operations
#  - Variables are also handled, all are treated
#    as float's.  The variable is initialized
#    on its first appearance to '0.0'.  Multiple
#    assignment is allowed, but only the default
#    assignment operator is defined by default
#  - Constants can be defined
#  - Keywords can be defined
#  - Functions can be defined
#
# Defined functions to use are:
#  SetOperator
#  SetKeyword
#  SetFunction
#  SetConstant
#  SetVariable
#  PushFlow
#  PopFlow
#  PeekFlow
#  LenFlow
#  PurgeFlow
#  RunLine
#  error
#  ExecuteTokens
#  TokensToRPN
#  ExecuteRPN
#==================================================
from __future__ import division

import operator
from string import digits, whitespace

#--------------------------------------------------
name_start = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
name_chars = name_start + u'0123456789'

# validName ---------------------------------------
#  Test if a string can be used as a valid name
#--------------------------------------------------
def validName(string):
    try:
        if string[0] not in name_start: return False
        for i in string:
            if i not in name_chars: return False
        return True
    except (TypeError, KeyError): # TypeError means not iterable
        return False

# validNumber -------------------------------------
#  Test if a string can be used as a valid number
#--------------------------------------------------
def validNumber(string):
    try:
        float(string)
        if u'.' in string and string == u'.': return False
        return True
    except ValueError:
        return False

# Define Some Constants ---------------------------

# Some error string
ERR_CANNOT_SET = u"Cannot set %s '%s': type is '%s'."
ERR_TOO_FEW_ARGS = u"Too few arguments to %s '%s':  got %s, expected %s."
ERR_TOO_MANY_ARGS = u"Too many arguments to %s '%s':  got %s, expected %s."

class KEY(object):
    # Constants for keyword args
    NO_MAX = -1     # No maximum arguments
    NA = 0          # Not a variable argument keyword

class OP(object):
    # Constants for operator precedences
    PAR = 0     # Parenthesis
    EXP = 1     # Exponent
    UNA = 2     # Unary (++, --)
    MUL = 3     # Multiplication (*, /, %)
    ADD = 4     # Addition (+, -)
    CO1 = 5     # Comparison (>=,<=,>,<)
    CO2 = 6     # Comparison (!=, ==)
    MEM = 7     # Membership test (a in b)
    NOT = 8     # Logical not (not, !)
    AND = 9     # Logical and (and, &)
    OR  = 10    # Logical or (or, |)
    ASS = 11    # Assignment (=,+=,etc

# Constants for operator associations
LEFT = 0
RIGHT = 1

# Constants for the type of a token
UNKNOWN = 0
NAME = 1            # Can be a name token, but not used yet
CONSTANT = 2
VARIABLE = 3
FUNCTION = 4
KEYWORD = 5
OPERATOR = 6
INTEGER = 7
DECIMAL = 8
OPEN_PARENS = 9
CLOSE_PARENS = 10
COMMA = 11
WHITESPACE = 12
STRING = 13
OPEN_BRACKET = 14
CLOSE_BRACKET = 15
COLON = 16

Types = {UNKNOWN:u'UNKNOWN',
         NAME:u'NAME',
         CONSTANT:u'CONSTANT',
         VARIABLE:u'VARIABLE',
         FUNCTION:u'FUNCTION',
         KEYWORD:u'KEYWORD',
         OPERATOR:u'OPERATOR',
         INTEGER:u'INTEGER',
         DECIMAL:u'DECIMAL',
         OPEN_PARENS:u'OPEN_PARENS',
         CLOSE_PARENS:u'CLOSE_PARENS',
         COMMA:u'COMMA',
         WHITESPACE:u'WHITESPACE',
         STRING:u'STRING',
         OPEN_BRACKET:u'OPEN_BRACKET',
         CLOSE_BRACKET:u'CLOSE_BRACKET',
         COLON:u'COLON',
         }

# getType ---------------------------------------
#  determines the type of a string.  If 'parser'
#  is passed, then it will attempt it against
#  various names as well.
#------------------------------------------------
def getType(item, parser=None):
    if isinstance(item, unicode):
        if not parser: return STRING
        if item in parser.constants: return CONSTANT
        if item in parser.variables: return VARIABLE
        if item in parser.keywords : return KEYWORD
        if item in parser.functions: return FUNCTION
        if item in parser.operators: return OPERATOR
        if item == u'(': return OPEN_PARENS
        if item == u')': return CLOSE_PARENS
        if item == u'[': return OPEN_BRACKET
        if item == u']': return CLOSE_BRACKET
        if item == u':': return COLON
        if item == u',': return COMMA
        if validName(item): return NAME
        if validNumber(item):
            if u'.' in item: return DECIMAL
            return INTEGER
        for i in item:
            if i not in whitespace: return UNKNOWN
        return WHITESPACE
    if isinstance(item, int): return INTEGER
    if isinstance(item, float): return DECIMAL
    return UNKNOWN

# FlowControl -------------------------------------
#  Flow control object, to hold info about a flow
#  control statement
#--------------------------------------------------
class FlowControl(object):
    def __init__(self, statement_type, active, keywords=[], **attribs):
        self.type = statement_type
        self.active = active
        self.keywords = keywords
        for i in attribs:
            setattr(self, i, attribs[i])

# Token -------------------------------------------
#  Token object, to hold info about a token
#--------------------------------------------------

# ParserError -------------------------------------
#  So when we catch exceptions we know if it's a
#  problem with the parser, or a problem with the
#  script
#--------------------------------------------------
class ParserError(SyntaxError): pass
gParser = None
def error(msg):
    if gParser:
        raise ParserError(u'(Line %s, Column %s): %s' % (gParser.cLine, gParser.cCol, msg))
    else:
        raise ParserError(msg)

# Parser ------------------------------------------
#  This is where the magic happens
#--------------------------------------------------
class Parser(object):
    class ParserType(object):
        @property
        def Type(self): return self.__class__.__name__

    class Callable(ParserType):
        def __init__(self, callable_name, function, min_args=0,
                     max_args=KEY.NA, passTokens=False, passCommas=False):
            self.callable_name = callable_name
            self.function = function
            self.passTokens = passTokens
            self.passCommas = passCommas
            if max_args == KEY.NA: max_args = min_args
            if min_args > max_args >= 0: max_args = min_args
            self.minArgs = min_args
            self.maxArgs = max_args

        def __call__(self, *args):
            # Remove commas if necessary, pass values if necessary
            if not self.passCommas or not self.passTokens:
                args = [(x.tkn,x)[self.passTokens] for x in args if x.type != COMMA or self.passCommas]
            return self.execute(*args)

        def execute(self, *args):
            # Ensure correct number of arguments
            numArgs = len(args)
            if self.maxArgs != KEY.NO_MAX and numArgs > self.maxArgs:
                if self.minArgs == self.maxArgs:
                    error(ERR_TOO_MANY_ARGS % (
                        self.Type, self.callable_name, numArgs, self.minArgs))
                else:
                    error(ERR_TOO_MANY_ARGS % (
                        self.Type, self.callable_name, numArgs,
                        u'min: %s, max: %s' % (self.minArgs,self.maxArgs)))
            if numArgs < self.minArgs:
                if self.maxArgs == KEY.NO_MAX:
                    error(ERR_TOO_FEW_ARGS % (
                        self.Type, self.callable_name, numArgs,
                        u'min: %s' % self.minArgs))
                elif self.minArgs == self.maxArgs:
                    error(ERR_TOO_FEW_ARGS % (
                        self.Type, self.callable_name, numArgs, self.minArgs))
                else:
                    error(ERR_TOO_FEW_ARGS % (
                        self.Type, self.callable_name, numArgs,
                        u'min: %s, max: %s' % (self.minArgs, self.maxArgs)))
            return self.function(*args)

    class Operator(Callable):
        def __init__(self, operator_name, function, precedence,
                     association=LEFT, passTokens=True):
            self.precedence = precedence
            self.association = association
            if self.precedence in (OP.UNA, OP.NOT):
                min_args = 1
            else:
                min_args = 2
            super(Parser.Operator,self).__init__(operator_name, function,
                                                 min_args,
                                                 passTokens=passTokens)

    class Keyword(Callable):
        def __init__(self, keyword_name, function, min_args=0, max_args=KEY.NA,
                     passTokens=False, splitCommas=True, passCommas=False):
            self.splitCommas = splitCommas
            super(Parser.Keyword,self).__init__(keyword_name, function,
                                                min_args, max_args,
                                                passTokens, passCommas)

        def __call__(self, *args):
            gParser.StripOuterParens(args)
            if not self.splitCommas:
                return super(Parser.Keyword,self).__call__(*args)
            args = gParser.SplitAtCommas(args)
            if not self.passTokens:
                if len(args) == 1:
                    if len(args[0]) > 0:
                        args = [gParser.ExecuteTokens(args[0])]
                    else:
                        args = []
                else:
                    for i,arg in enumerate(args):
                        if len(arg) > 0:
                            args[i] = gParser.ExecuteTokens(arg)
                        else:
                            args[i] = None
            return self.execute(*args)

    class Function(Callable):
        def __init__(self, function_name, function, min_args=0,
                     max_args=KEY.NA, passTokens=False, dotFunction=False):
            """function: function that will be called with the args
               num_args: number of args required for the function
               passTokens: whether tokens or the data within should be passed as args
               dotFunction: whether this function can be called using the dot operator
               """
            super(Parser.Function,self).__init__(function_name, function,
                                                 min_args, max_args,
                                                 passTokens)
            self.dotFunction = dotFunction

    class Token(object):
        def __init__(self, token_or_text, Type=None, parser=None, line=None,
                     pos=(None, None)):
            if isinstance(token_or_text, Parser.Token):
                self.text = token_or_text.text
                self.type = token_or_text.type
                self.parser = token_or_text.parser
                self.line = token_or_text.line
                self.pos = token_or_text.pos
                self.numArgs = token_or_text.numArgs
            else:
                self.text = token_or_text
                self.type = Type or getType(token_or_text, parser)
                self.parser = parser
                self.line = line
                self.pos = pos
                self.numArgs = 0

        def GetData(self):
            """:rtype: Parser.Function | Parser.Keyword | Parser.Operator |
            unicode | int | float
            """
            if self.parser:
                if self.type == FUNCTION: return self.parser.functions[self.text]
                if self.type == KEYWORD : return self.parser.keywords[self.text]
                if self.type == OPERATOR: return self.parser.operators[self.text]
                if self.type == VARIABLE: return self.parser.variables[self.text]
                if self.type == CONSTANT: return self.parser.constants[self.text]
                if self.type == DECIMAL : return float(self.text)
                if self.type == INTEGER : return int(self.text)
            return self.text
        tkn = property(GetData) # did I catch all uses ?

        # Implement rich comparisons, __cmp__ is deprecated
        def __eq__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn == other.tkn
            return self.tkn == other
        def __ne__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn != other.tkn
            return self.tkn != other
        def __lt__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn < other.tkn
            return self.tkn < other
        def __le__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn <= other.tkn
            return self.tkn <= other
        def __gt__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn > other.tkn
            return self.tkn > other
        def __ge__(self, other):
            if isinstance(other, Parser.Token):
                return self.tkn >= other.tkn
            return self.tkn >= other

        def __add__(self, other): return Parser.Token(self.tkn + other.tkn)
        def __sub__(self, other): return Parser.Token(self.tkn - other.tkn)
        def __mul__(self, other): return Parser.Token(self.tkn * other.tkn)
        def __mod__(self, other): return Parser.Token(self.tkn % other.tkn)
        def __truediv__(self, other): return Parser.Token(self.tkn / other.tkn)
        def __floordiv__(self, other): return Parser.Token(self.tkn // other.tkn)
        def __divmod__(self, other): return Parser.Token(divmod(self.tkn, other.tkn))
        def __pow__(self, other): return Parser.Token(self.tkn ** other.tkn)
        def __lshift__(self, other): return Parser.Token(self.tkn << other.tkn)
        def __rshift__(self, other): return Parser.Token(self.tkn >> other.tkn)
        def __and__(self, other): return Parser.Token(self.tkn & other.tkn)
        def __xor__(self, other): return Parser.Token(self.tkn ^ other.tkn)
        def __or__(self, other): return Parser.Token(self.tkn | other.tkn)
        def __nonzero__(self): return bool(self.tkn)
        def __neg__(self): return Parser.Token(-self.tkn)
        def __pos__(self): return Parser.Token(+self.tkn)
        def __abs__(self): return abs(self.tkn)
        def __int__(self): return int(self.tkn)
        def __index__(self): return operator.index(self.tkn)
        def __float__(self): return float(self.tkn)
        def __str__(self): return unicode(self.tkn)

        def __repr__(self): return u'<Token-%s:%s>' % (Types[self.type],self.text)

        # Fall through to function/keyword
        def __call__(self, *args, **kwdargs): return self.tkn(*args, **kwdargs)

    # Now for the Parser class
    def __init__(self,
                 doImplicit=u'*',
                 dotOperator=u'.',
                 comment=u';',
                 constants={u'True':True,u'False':False},
                 variables=None
                 ):
        self.doImplicit = doImplicit
        self.dotOperator = dotOperator
        self.comment = comment

        self.runon = False
        self.cLineStart = 0
        self.cCol = 0
        self.cLine = 0
        self.tokens = []
        self.Flow = []

        self.opChars = u''
        self.operators = {}
        self.keywords = {}
        self.functions = {}
        self.constants = constants or {}
        self.variables = variables or {}
        self.escapes = {u'n':u'\n',
                        u't':u'\t'
                        }

        self.word = None
        self.wordStart = None

        if dotOperator:
            self.SetOperator(dotOperator, self.opDotOperator, OP.PAR)
        # Special function
        self.functions[u']index['] = Parser.Function(u'<index>', self.fnIndex,
                                                     2, 4)

        global gParser
        gParser = self

    # Dummy function for the dot operator
    def opDotOperator(self, l, r): pass

    # Indexing operator function
    _marker = object()
    def fnIndex(self, item, start, stop=None, step=None):
        try:
            fn = u'item['

            # Start
            if start is not Parser._marker:
                fn += u'%i'% start
            elif stop is None:
                fn += u':'

            # Stop
            if stop is Parser._marker:
                fn += u':'
            elif stop is not None:
                fn += u':%i' % stop

            # Step
            if step is Parser._marker:
                fn += u':'
            elif step is not None:
                fn += u':%i' % step

            fn += u']'
            return eval(fn)
        except:
            error(_(u'IndexError'))

    def SetOperator(self, op_name, *args, **kwdargs):
        type_ = getType(op_name, self)
        if type_ not in [NAME,OPERATOR,UNKNOWN]:
            error(ERR_CANNOT_SET % (u'operator', op_name, Types[type_]))
        self.operators[op_name] = Parser.Operator(op_name, *args, **kwdargs)
        for i in op_name:
            if i not in self.opChars: self.opChars += i
    def SetKeyword(self, keywrd_name, *args, **kwdargs):
        type_ = getType(keywrd_name, self)
        if type_ not in [NAME,KEYWORD]:
            error(ERR_CANNOT_SET % (u'keyword', keywrd_name, Types[type_]))
        self.keywords[keywrd_name] = Parser.Keyword(keywrd_name, *args, **kwdargs)
    def SetFunction(self, fun_name, *args, **kwdargs):
        type_ = getType(fun_name, self)
        if type_ not in [NAME,FUNCTION]:
            error(ERR_CANNOT_SET % (u'function', fun_name, Types[type_]))
        self.functions[fun_name] = Parser.Function(fun_name, *args, **kwdargs)
    def SetConstant(self, const_name, value):
        type_ = getType(const_name, self)
        if type_ not in [NAME,CONSTANT]:
            error(ERR_CANNOT_SET % (u'constant', const_name, Types[type_]))
        self.constants[const_name] = value
    def SetVariable(self, var_name, value):
        type_ = getType(var_name, self)
        if type_ not in [NAME, VARIABLE]:
            error(ERR_CANNOT_SET % (u'variable', var_name, Types[type_]))
        self.variables[var_name] = value

    # Flow control stack
    def PushFlow(self, stmnt_type, active, keywords, **attribs):
        self.Flow.append(FlowControl(stmnt_type, active, keywords, **attribs))
    def PopFlow(self): return self.Flow.pop()
    def PopFrontFlow(self): return self.Flow.pop(0)
    def PeekFlow(self,index=-1): return self.Flow[index]
    def LenFlow(self): return len(self.Flow)
    def PurgeFlow(self): self.Flow = []

    # Run a line of code: returns True if more lines are needed to make a complete line, False if not
    def RunLine(self, line):
        # First reset tokens if we're starting a new line
        if not self.runon:
            self.cLineStart = self.cLine
            self.tokens = []

        # Now parse the tokens
        self.cLine += 1
        self.TokenizeLine(line)
        if self.runon: return True

        # No tokens?
        if len(self.tokens) == 0: return False

        # See if we're in currently within a flow control construct
        if self.LenFlow() > 0:
            i = self.PeekFlow()
            if not i.active and self.tokens[0].text not in i.keywords:
                return False

        # If we have a keyword, just run it
        if self.tokens[0].type == KEYWORD:
            kwrd = self.tokens.pop(0)
            kwrd(*self.tokens)
        # It's just an expression, didnt start with a keyword
        else:
            # Convert to reverse-polish notation and execute
            self.ExecuteTokens()
        return False

    # Removes any commas from a list of tokens
    def SkipCommas(self, tokens=None):
        if tokens is None:
            self.tokens = [x for x in self.tokens if x.type != COMMA]
            return self.tokens
        tokens = [x for x in tokens if x.type != COMMA]
        return tokens

    # Split tokens at commas
    def SplitAtCommas(self, tokens=None):
        tokens = tokens or self.tokens
        parenDepth = 0
        bracketDepth = 0
        ret = [[]]
        for tok in tokens:
            if tok.type == OPEN_PARENS:
                parenDepth += 1
            elif tok.type == CLOSE_PARENS:
                parenDepth -= 1
                if parenDepth < 0:
                    error(_(u'Mismatched parenthesis.'))
            elif tok.type == OPEN_BRACKET:
                bracketDepth += 1
            elif tok.type == CLOSE_BRACKET:
                bracketDepth -= 1
                if bracketDepth < 0:
                    error(_(u'Mismatched brackets.'))
            if tok.type == COMMA and parenDepth == 0 and bracketDepth == 0:
                    ret.append([])
            else:
                ret[-1].append(tok)
        return ret

    def StripOuterParens(self, tokens=None):
        tokens = tokens or self.tokens
        while len(tokens) > 2 and tokens[0].type == OPEN_PARENS and tokens[-1].type == CLOSE_PARENS:
            tokens = tokens[1:-1]
        return tokens

    # Split a string into tokens
    def TokenizeLine(self, line):
        self.word = None
        self.wordStart = None
        self.cCol = 0
        self.runon = False

        state = self._stateSpace
        for i in line:
            state = state(i)
            if not state: return None
            self.cCol += 1
        self._emit()

        return self.tokens

    # Run a list of tokens
    def ExecuteTokens(self, tokens=None):
        tokens = tokens or self.tokens
        self.TokensToRPN(list(tokens))
        return self.ExecuteRPN()

    # Convert a list of tokens to rpn
    def TokensToRPN(self, tokens=None):
        tokens = tokens or self.tokens
        rpn = []
        stack = []

        # Add an item to the rpn, and increase arg count for
        # the last parens
        def rpnAppend(item):
            for i in reversed(stack):
                if i.type in [OPEN_PARENS,OPEN_BRACKET]:
                    i.numArgs = 1
                    break
            rpn.append(item)

        # Now the rest of it
        for idex,i in enumerate(tokens):
            if i.type in [INTEGER,DECIMAL,CONSTANT,VARIABLE,NAME,STRING]:
                rpnAppend(i)
            elif i.type == COMMA:
                while len(stack) > 0 and stack[-1].type != OPEN_PARENS:
                    rpn.append(stack.pop())
                if len(stack) == 0:
                    error(_(u"Misplaced ',' or missing parenthesis."))
                if len(stack) > 1 and stack[-2].type == FUNCTION:
                    stack[-2].numArgs += stack[-1].numArgs
                    stack[-1].numArgs = 0
            elif i.type == COLON:
                temp_tokens = []
                while len(stack) > 0 and stack[-1].type != OPEN_BRACKET:
                    temp_tokens.append(stack.pop())
                if len(stack) <= 1:
                    error(_(u"Misplaced ':' or missing bracket."))
                stack[-2].numArgs += stack[-1].numArgs
                if len(temp_tokens) == 0 and stack[-1].numArgs == 0:
                    rpn.append(Parser.Token(Parser._marker,Type=UNKNOWN,parser=self))
                    stack[-2].numArgs += 1
                else:
                    rpn.extend(temp_tokens)
                stack[-1].numArgs = 0
            elif i.type == FUNCTION:
                stack.append(i)
            elif i.type == OPERATOR:
                # Dot operator
                if i.text == self.dotOperator:
                    if idex+1 >= len(tokens):
                        error(_(u'Dot operator: no function to call.'))
                    if tokens[idex+1].type != FUNCTION:
                        error(_(u"Dot operator: cannot access non-function '%s'.") % tokens[idex+1].text)
                    if not tokens[idex+1].tkn.dotFunction:
                        error(_(u"Dot operator: cannot access function '%s'.") % tokens[idex+1].text)
                    tokens[idex+1].numArgs += 1
                # Other operators
                else:
                    while len(stack) > 0 and stack[-1].type == OPERATOR:
                        if i.tkn.association == LEFT and i.tkn.precedence >= stack[-1].tkn.precedence:
                            rpn.append(stack.pop())
                        elif i.tkn.association == RIGHT and i.tkn.precedence > stack[-1].tkn.precedence:
                            rpn.append(stack.pop())
                        else:
                            break
                    if i.text == u'-':
                        # Special unary minus type
                        if idex == 0 or tokens[idex-1].type in [OPEN_BRACKET,OPEN_PARENS,COMMA,COLON,OPERATOR,KEYWORD]:
                            rpnAppend(Parser.Token(u'0',parser=self))
                    stack.append(i)
            elif i.type == OPEN_PARENS:
                stack.append(i)
            elif i.type == OPEN_BRACKET:
                stack.append(Parser.Token(u']index[', parser=self))
                stack.append(i)
            elif i.type == CLOSE_PARENS:
                while len(stack) > 0 and stack[-1].type != OPEN_PARENS:
                    rpn.append(stack.pop())
                if len(stack) == 0:
                    error(_(u'Unmatched parenthesis.'))
                numArgs = stack[-1].numArgs
                stack.pop()
                if len(stack) > 0 and stack[-1].type == FUNCTION:
                    stack[-1].numArgs += numArgs
                    rpn.append(stack.pop())
            elif i.type == CLOSE_BRACKET:
                temp_tokens = []
                while len(stack) > 0 and stack[-1].type != OPEN_BRACKET:
                    temp_tokens.append(stack.pop())
                if len(stack) == 0:
                    error(_(u'Unmatched brackets.'))
                numArgs = stack[-1].numArgs
                stack.pop()
                if len(temp_tokens) == 0 and numArgs == 0 and stack[-1].numArgs != 0:
                    rpn.append(Parser.Token(Parser._marker,Type=UNKNOWN,parser=self))
                    numArgs += 1
                rpn.extend(temp_tokens)
                stack[-1].numArgs += numArgs + 1
                if stack[-1].numArgs == 1:
                    error(_(u'IndexError'))
                rpn.append(stack.pop())
            else:
                error(_(u"Unrecognized token: '%s', type: %s") % (i.text, Types[i.type]))
        while len(stack) > 0:
            i = stack.pop()
            if i.type in [OPEN_PARENS,CLOSE_PARENS]:
                error(_(u'Unmatched parenthesis.'))
            rpn.append(i)
        self.rpn = rpn
        return rpn

    def ExecuteRPN(self, rpn=None):
        rpn = rpn or self.rpn

        stack = []
        for i in rpn:
            if i.type == OPERATOR:
                if len(stack) < i.tkn.minArgs:
                    error(ERR_TOO_FEW_ARGS % (u'operator', i.text, len(stack), i.tkn.minArgs))
                args = []
                while len(args) < i.tkn.minArgs:
                    args.append(stack.pop())
                args.reverse()
                ret = i(*args)
                if isinstance(ret, list):
                    stack.extend([Parser.Token(x) for x in ret])
                else:
                    stack.append(Parser.Token(ret))
            elif i.type == FUNCTION:
                if len(stack) < i.numArgs:
                    error(ERR_TOO_FEW_ARGS % (u'function', i.text, len(stack), i.numArgs))
                args = []
                while len(args) < i.numArgs:
                    args.append(stack.pop())
                args.reverse()
                ret = i(*args)
                if isinstance(ret, list):
                    stack.extend([Parser.Token(x) for x in ret])
                else:
                    stack.append(Parser.Token(ret))
            else:
                stack.append(i)
        if len(stack) == 1:
            return stack[0].tkn
        error(_(u'Too many values left at the end of evaluation.'))

    def error(self, msg):
        raise ParserError(u'(Line %s, Column %s): %s' % (self.cLine, self.cCol, msg))

    #Functions for parsing a line into tokens
    def _grow(self, c):
        if self.word: self.word += c
        else:
            self.word = c
            self.wordStart = self.cCol

    def _emit(self, word=None, type_=None):
        word = word or self.word
        if word is None: return
        if self.wordStart is None: self.wordStart = self.cCol - 1
        type_ = type_ or getType(word, self)

        # Try to figure out if it's multiple operators bunched together
        rightWord = None
        if type_ == UNKNOWN:
            for idex in xrange(len(word),0,-1):
                newType = getType(word[0:idex], self)
                if newType != UNKNOWN:
                    rightWord = word[idex:]
                    rightWordStart = self.wordStart + idex
                    word = word[0:idex]
                    break

        # Implicit multiplication
        if self.doImplicit:
            if len(self.tokens) > 0:
                left = self.tokens[-1].type
                if left in [CLOSE_PARENS,CLOSE_BRACKET]:
                    if type_ in [OPEN_PARENS, DECIMAL, INTEGER, FUNCTION, VARIABLE, CONSTANT, NAME]:
                        self.tokens.append(Parser.Token(self.doImplicit,OPERATOR,self,self.cLine))
                elif left in [DECIMAL,INTEGER]:
                    if type_ in [OPEN_PARENS, FUNCTION, VARIABLE, CONSTANT, NAME]:
                        self.tokens.append(Parser.Token(self.doImplicit,OPERATOR,self,self.cLine))
                elif left in [VARIABLE, CONSTANT, NAME]:
                    if type_ == OPEN_PARENS:
                        self.tokens.append(Parser.Token(self.doImplicit,OPERATOR,self,self.cLine))
        self.tokens.append(Parser.Token(word, type_, self, self.cLine, (self.wordStart, self.cCol)))
        self.word = None
        self.wordStart = None

        if rightWord is not None:
            state = self._stateSpace
            self.cCol = rightWordStart
            for i in rightWord:
                state = state(i)
                if not state: return
                self.cCol += 1

    def _stateSpace(self, c):
        self._emit()
        if c in whitespace: return self._stateSpace
        if c == u"'": return self._stateSQuote
        if c == u'"': return self._stateDQuote
        if c == u'\\': return self._stateEscape
        if c == self.comment: return self._stateComment
        self._grow(c)
        if c in name_start: return self._stateName
        if c in self.opChars: return self._stateOperator
        if c in digits: return self._stateNumber
        if c == u'.': return self._stateDecimal
        if c == u'(': return self._stateSpace
        if c == u'[': return self._stateSpace
        if c == u')': return self._stateEndBracket
        if c == u']': return self._stateEndBracket
        if c == u',': return self._stateSpace
        error(_(u"Invalid character: '%s'") % c)

    def _stateSQuote(self, c):
        if c == u'\\': return self._stateSQuoteEscape
        if c == u"'":
            if not self.word: self.word = u''
            self._emit(type_=STRING)
            return self._stateSpace
        if c == u'\n':
            error(_(u'Unterminated single quote.'))
        self._grow(c)
        return self._stateSQuote
    def _stateSQuoteEscape(self, c):
        if c in self.escapes: self._grow(self.escapes[c])
        else: self._grow(c)
        return self._stateSQuote

    def _stateDQuote(self, c):
        if c == u'\\': return self._stateDQuoteEscape
        if c == u'"':
            if not self.word: self.word = u''
            self._emit(type_=STRING)
            return self._stateSpace
        if c == u'\n':
            error(_(u'Unterminated double quote.'))
        self._grow(c)
        return self._stateDQuote
    def _stateDQuoteEscape(self, c):
        if c in self.escapes: self._grow(self.escapes[c])
        else: self._grow(c)
        return self._stateDQuote

    def _stateEscape(self, c):
        if c == u'\n':
            self.runon = True
            return
        return self._stateSpace(c)

    def _stateComment(self, c): return self._stateComment

    def _stateName(self, c):
        if c in name_chars:
            self._grow(c)
            return self._stateName
        if c in [u"'",u'"']:
            error(_(u'Unexpected quotation %s following name token.') % c)
        if c == u':' and self.word.endswith(u'in'):
            self._grow(c)
            return self._stateOperator
        return self._stateSpace(c)

    def _stateOperator(self, c):
        if c in self.opChars:
            self._grow(c)
            return self._stateOperator
        return self._stateSpace(c)

    def _stateNumber(self, c):
        if c in digits:
            self._grow(c)
            return self._stateNumber
        if c == u'.':
            self._grow(c)
            return self._stateDecimal
        if c in [u'"',u"'"]:
            error(_(u'Unexpected quotation %s following number token.') % c)
        return self._stateSpace(c)
    def _stateDecimal(self, c):
        if c in digits:
            self._grow(c)
            return self._stateDecimal
        if c in [u'"',u"'",u'.']:
            error(_(u'Unexpected %s following decimal token.') % c)
        return self._stateSpace(c)

    def _stateEndBracket(self, c):
        if c in [u'"',u"'"]:
            error(_(u'Unexpected quotation %s following parenthesis.') % c)
        return self._stateSpace(c)
