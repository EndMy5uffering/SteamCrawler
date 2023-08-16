from __future__ import annotations
from Plexer import Plexer

class ParserException(Exception):
    '''This is the general exception type for the parser.'''
    pass

class ParserParsingException(ParserException):
    '''Raised when the given data could not be parsed.'''
    pass

class ParserUnrecognizedTokenException(ParserException):
    '''Raised when the parser encounters an unrecognized token.'''
    pass

class ParserArumentException(ParserException):
    '''This exception is raised when a wrong argument was provided to a funciton.'''
    pass

def default_transition_funciton(parser:Parser, element):
    parser._stack.append(element)
    pass
  
class Parser:
    
    def __init__(self):
        self._transitions:dict = {} # {(from, to): func, ...}
        self._stack:list = []
        self._prev_token = None
        self.default_function = default_transition_funciton
        self.status_callback = None
        pass
    
    def parse(self, plexer_data):
        for i in range(len(plexer_data)):
            if self.status_callback:
                self.status_callback(self, i, len(plexer_data)-1)
            transition = (self._prev_token, plexer_data[i]['Token'])
            if transition in self._transitions:
                func = self._transitions[transition]
                if func:
                    func(self, plexer_data[i])
                    self._prev_token = plexer_data[i]['Token']
                else:
                    prev = self._prev_token or 'None'
                    raise ParserParsingException('No parseing funciton for transition:' + prev + ' -> ' + plexer_data[i]['Token'])
            else:
                raise ParserUnrecognizedTokenException('Unrecognized token: ' + plexer_data[i]['Token'] + ' for transition: (' + (self._prev_token or 'None') + ', ' + plexer_data[i]['Token'] + ')' + ' with ' + plexer_data[i]['Data'])
        if len(self._stack) > 0:
            raise ParserParsingException('Stack was not empty at the end of the parse. ' + str(len(self._stack)) + ' elements left on the stack.')
        pass
    
    def __iadd__(self, other):
        '''
        Allows you to add a transion to the Parser via +=
                pr = Parser()
                pr += 'Token0', 'Token1', func
                pr += None, 'Token0', func2
        '''
        if not isinstance(other, tuple):
            raise ParserArumentException('Expected type Tuple(str, str, function) wher funciton can be omited.')
        if len(other) < 2:
            raise ParserArumentException('At least two strings are required (Token_from, Token_to)')
        if len(other) < 3:
            self.add_transition(other[0], other[1])
            return self
        self.add_transition(other[0], other[1], other[2])
        return self

    def add_transition(self, token_from, token_to, transition_func=None) -> Parser:
        '''
        Adds a transition to the parser.
        The first transition should go from None to some token.
        All other tokens should not be None.
        '''
        if not isinstance(token_from, str):
            raise ParserArumentException('token_from needs to be a string.')
        if not isinstance(token_to, str):
            raise ParserArumentException('token_to needs to be a string.')
        if transition_func and not callable(transition_func):
            raise ParserArumentException('Given transition function is not a callable.')
        transition = (token_from, token_to)
        if transition in self._transitions:
            raise ParserArumentException('Transition for ' + token_from + ' to ' + token_to + ' allready exist.')
        if transition_func:
            self._transitions[transition] = transition_func
        else:
            self._transitions[transition] = default_transition_funciton
        return self
    
    def set_previous_token(self, token:str):
        '''
        Sets the previous token.
        Can be used to define a start point for the parser.
        '''
        self._prev_token = token
        pass
    
    def __ior__(self, other) -> Parser:
        if not callable(other):
            raise ParserArumentException('Given object was not callable.')
        self.default_function = other
        return self
