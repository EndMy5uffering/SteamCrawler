class Preader:
    '''
    A simple data wrapper class.
    This class implements some simple helper functions to processes the given data.
    '''
    def __init__(self, raw:str):
        self.raw = raw
        self._c:int = 0
        self._current:str = ''
        pass
    
    def __iter__(self):
        '''Enabling the class to be used as an itterator or in the context of an itterator.'''
        return self
    
    def __next__(self) -> str:
        if not self.has_next():
            raise StopIteration()
        
        return self.next()
    
    def get_current(self) -> str:
        '''Returns the character that was last read or an empty string if nothing was read yet.'''
        return self._current
    
    def next(self) -> str:
        '''Returns the character at the cursor position then moves the cursor one position to the right.'''
        self._current = self.raw[self._c]
        self._c += 1
        return self._current
    
    def has_next(self) -> bool:
        '''Checks if the cursor is allready at the end of the text.'''
        return self._c < len(self.raw)
    
    def peak_next(self) -> str:
        '''Returns the next element without moving the cursor.'''
        if self._c < len(self.raw):
            return self.raw[self._c]
        return ''
    
    def read_to_inc(self, *eos:str) -> str:
        '''
        Reads everything and the given characters.
        When the given characters are found the read data is returned.
        '''
        data = ''
        for l in self:
            data += l
            if l in eos:
                return data 
        
        return data
    
    def read_to_exc(self, *eos:str) -> str:
        '''
        Reads everything up to the given characters.
        When the given characters are found the read data is returned.
        '''
        data = ''
        if self.peak_next() in eos:
            return data
        
        for l in self:
            data += l
            if self.peak_next() in eos:
                return data 
        
        return data
    
    def read_next(self, ammount:int=0) -> str:
        '''Reads the next (ammount) of characters and returns them.'''
        data:str = ''
        for i in range(0, ammount):
            if self.has_next():
                data += self.next()
            else:
                return data
        return data
    
    def read_next_nondestruct(self, ammount:int=0) -> str:
        '''Reads the next (ammount) of characters without moving the cursor.'''
        return self.raw[self._c:self._c+ammount]

    def read_next_destruct(self, ammount:int=0) -> str:
        '''Reads the next (ammount) of characters and moves the cursor.'''
        data:str = self.raw[self._c:self._c+ammount]
        self._c += ammount
        self._reset_current()
        return data
    
    def back(self, n:int=1) -> str:
        '''Moves the cursor back by n.'''
        if n > self._c:
            self._c = 0
        else:
            self._c = self._c - n
        self._reset_current()
        return self._current

    def _reset_current(self):
        '''Resets the char held by the __current__ variable.'''
        if self._c > 0:
            self._current = self.raw[self._c -1]
        else:
            self._current = ''
        pass