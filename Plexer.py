from __future__ import annotations
from Preader import Preader

class PlexerException(Exception):
    '''Raised by the Plexer when it encounters an exception.'''
    pass

class PlexerArgumentException(PlexerException):
    '''Raised by the Plexer when some argument is not correct.'''
    pass

class PlexerParseingException(PlexerException):
    '''Raised by the Plexer when it encounters an unrecognized symbol.'''
    pass

def default_consumer(pl:Plexer, pr:Preader):
    '''
    The default consumer function.
    It will read everything until it finds a key symbol from the symbol list.
    '''
    text = ''
    tk_list = pl._tokens
    while pr.has_next():
        current = pr.peak_next()
        for kw in tk_list:
            if current == kw:
                return 'TEXT', text
        text += pr.next()
    return 'TEXT', text

class Token:
    def __init__(self, token):
        self.token = token

class Plexer:
    '''
    The Plexer is a lexer or tokanizer that will take a text as input and tokanize it.
    You can add tokens to the list of tokens with the add_token method or the += opperator.
    To parse some text use the parse method.
    When the plexer is done parsing you can get the data with the get_data method.
        -> get_data will return a list of dictionarys of the form:
                    {'Token': 'TOKEN_NAME', 'Data': 'READ_DATA'}
    '''
    def __init__(self):
        self._tokens:dict[str, str] = {} # {'key_word': (TOKEN, post_reader), 'key_word': TOKEN, ...}
        self._data:list[dict[str, str]] = [] # [{'TOKEN':'token', 'DATA':'data'}, {...}, ...]
        self.reader:Preader = None
        self.consumer:function = default_consumer
        self.default_token:str = None
        self.status_callback = None
        pass
    
    def parse(self, data:str='') -> list[dict[str, str]]:
        '''
        This funciton will parse a given text and generate a list of tokens.
        If no token can be matched the default function will be used.
        If no default funciton is set an exception will be raised.
        A default funciton is provided. To remove it use the set_consumer to set it to None.

            Parameters:
                data (str): Some text you want to be tokanized
            Returns:
                A list of data that was tokanized in the form of:
                    [{'Token':'Token_Name', 'Data':'Read_Data'}, ...]
        '''
        self._data = []
        pr = Preader(data)
        while pr.has_next():
            if self.status_callback:
                self.status_callback(self, pr._c, len(pr.raw)-1)
            current = pr.peak_next()
            candidates = []        
            for kw in self._tokens:
                if current in kw:
                    candidates.append((kw, self._tokens[kw]))

            candidates.sort(key=lambda a: len(a[0]), reverse=True)
            if len(candidates) == 0 and self.consumer:
                token, text = self.consumer(self, pr)
                if not isinstance(token, str) and not isinstance(text, str):
                    raise PlexerParseingException('Output of consumer was not of type str make sure that the consumer returns the token and the consumed text')
                if self.default_token:
                    token = self.default_token
                self._data.append({'Token':token, 'Data':text})
                continue

            elif len(candidates) == 0 and not self.consumer:
                raise PlexerParseingException('Could not find a fitting token for symbol: ' + current)

            elif len(candidates) > 0:
                added = False
                for c in candidates:
                    kw, token_post_func = c
                    token, post_func = token_post_func
                    kw_len = len(kw)
                    word = pr.read_next_nondestruct(kw_len)
                    if word == kw:
                        self._data.append({'Token':token, 'Data':word})
                        pr.read_next_destruct(kw_len)
                        if post_func:
                            post_token, post_data = post_func(self, pr)
                            if isinstance(post_token, str) and isinstance(post_data, str):
                                self._data.append({'Token': post_token, 'Data': post_data})
                            else:
                                ptt = type(post_token).__name__ or 'None'
                                pdt = type(post_data).__name__ or 'None'
                                raise PlexerParseingException('Post funciton did not return the correct data expected (token:str, data:str) got (' + ptt + ',' + pdt +')')
                        added = True
                        break
                if added:
                    continue
                if self.consumer:
                    token, text = self.consumer(self, pr)
                    if not isinstance(token, str) and not isinstance(text, str):
                        raise PlexerParseingException('Output of consumer was not of type str make sure that the consumer returns the token and the consumed text')
                    if self.default_token:
                        token = self.default_token
                    self._data.append({'Token':token, 'Data':text})
                else:
                    raise PlexerParseingException('Could not parse symbol: ' + current)
        return self._data
    
    def __iadd__(self, other:tuple) -> Plexer:
        if not isinstance(other, tuple):
            raise PlexerArgumentException('the += opperator exprects either a tuple of strings (token_name, key_word) or a tuple of these tuples.')
        if isinstance(other[0], tuple):
            for entry in other:
                if isinstance(entry, tuple):
                    self += entry
                else:
                    raise PlexerArgumentException('Argument was not of type tuple but: ' + type(entry))
        else:
            post_func = None
            token = None
            for element in other:
                if isinstance(element, Token):
                    token = element
                elif callable(element):
                    post_func = element
            if not token:
                raise PlexerArgumentException('Expected at least one Token object got none.')
            for element in other:
                if element != post_func and element != token:
                    self._tokens[element] = (token.token, post_func)
            
        return self
    
    def add_token(self, token_name:str, symbole:str, *more) -> Plexer:
        '''
        Adds a token for a given set of symbols.
        '''
        if not isinstance(token_name, str):
            raise PlexerArgumentException('Given token was not of type str')
        if not isinstance(symbole, str):
            raise PlexerArgumentException('Given key word was not of type str')
        self._addt(token_name, symbole)
        if len(more) > 0:
            for kw in more:
                if not isinstance(kw, str):
                    raise PlexerArgumentException('Can not add none string argument as key word for argument *more')
        pass

    def set_default_token(self, token:str='TEXT'):
        '''Default token used by the default consumer function to mark the read data as.'''
        self.default_token = token
        pass

    def set_consumer(self, consumer:function) -> None:
        '''Sets the default consumer funciton if no symbol could be matched.'''
        if not consumer:
            self.consumer = None
            return
        if not callable(consumer):
            raise PlexerArgumentException('Consumer was not of type funciton')
        if consumer.__code__.co_argcount < 2:
            raise PlexerArgumentException('Consumer function exprects 2 arguments: Plexer and Preader')
        self.consumer = consumer

    def get_data(self) -> list[dict[str, str]]:
        return self._data
        pass
        
    def _addt(self, token:str, key_word:str) -> None:
        if key_word in self._tokens:
            raise PlexerArgumentException('The given key word is allready in the list of key words. Can not add key word twice: ' + key_word)
        self._tokens[key_word] = token
        pass
    
    def __ior__(self, other:function) -> Plexer:
        self.set_consumer(other)
        return self
