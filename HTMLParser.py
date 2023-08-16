import requests
from Plexer import Plexer, Token as T, PlexerParseingException
from Parser import Parser, ParserException, ParserParsingException
from Preader import Preader
import time

_DATA = 'DATA'
_HTML_OPEN = 'HTML_OPEN'
_HTML_CLOSE = 'HTML_CLOSE'
_HTML_OPEN_EXIT = 'HTML_OPEN_EXIT'
_HTML_COMMENT_OPEN = 'HTML_COMMENT_OPEN'
_HTML_COMMENT_CLOSE = 'HTML_COMMENT_CLOSE'
_DELIMITER = 'DELIMITER'
_ASSIGNMENT = 'ASSIGNMENT'
_TEXT_DELIMITER = 'TEXT_DELIMITER'
_BRACKET_OPEN = 'BRACKET_OPEN'
_BRACKET_CLOSE = 'BRACKET_CLOSE'
_LITERAL = 'LITERAL'
_ESCAPE_CHAR = 'ESCAPE_CHAR'

_HTML_VOID_TYPES = ['area', 'base', 'br', 'col', 'hr', 'img', 'input', 'link', 'meta', 'param']

class HTMLTag:
    def __init__(self, raw, data):
        self.open_tag = data[0]['Data'] == '<'
        self.comment_tag = data[0]['Data'] == '<!--'
        self.closing_tag = data[0]['Data'] == '</'
        self.raw = raw
        self._raw_data = data
        self.tag_data = {}
        self.html_data = []
        self.tag_name = data[1]['Data']
        self._build_tag_data()
    
    def _build_tag_data(self):
        for i in range(0, len(self._raw_data)):
            if self.get_raw_data_at(i):
                if self.get_raw_data_at(i+1):
                    if self.get_raw_data_at(i+2):
                        if self._raw_data[i]['Token'] == _DATA:
                            if self._raw_data[i+1]['Token'] == _ASSIGNMENT:
                                if self._raw_data[i+2]['Token'] == _LITERAL:
                                    self.tag_data[self._raw_data[i]['Data']] = self._raw_data[i+2]['Data'][1:-1]
                                elif self._raw_data[i+2]['Token'] == _DATA:
                                    self.tag_data[self._raw_data[i]['Data']] = self._raw_data[i+2]['Data']

    def has_tag_data(self, entry_name):
        return entry_name in self.tag_data
    
    def get_tag_data(self, entry_name):
        return self.tag_data[entry_name] or None

    def get_raw_data_at(self, index=0):
        if index >= len(self._raw_data):
            return None
        return self._raw_data[index]

    def get_tag_type(self):
        return self.tag_name

    def set_HTML_Data(self, data):
        self.html_data = data
    
    def has_HTML_Data(self):
        return self.html_data != None

class HTMLData:

    def __init__(self, data):
        self.raw = data

class HTMLPage:

    def __init__(self):
        self.tags:list[HTMLTag] = []
        self.data:list[HTMLData] = []
        self.raw_data = []
    
    def has_tag_with_data(self, data_name):
        for element in self.tags:
            if element.has_tag_data(data_name):
                return True
        return False

    def get_tags_with_data(self, data_name) -> list[HTMLTag]:
        found_tags = []
        for element in self.tags:
            if element.has_tag_data(data_name):
                found_tags.append(element)
        return found_tags
    
    def get_tags_with_type(self, type_name) -> list[HTMLTag]:
        found_tags = []
        for element in self.tags:
            if element.tag_name == type_name:
                found_tags.append(element)
        return found_tags

class HTMLParser:

    def __init__(self):
        self._HTML_DATA = []
        self._last_tag = None
        self.plexer = Plexer()
        self.parser = Parser()
        self._setup_rules()
    
    def _setup_rules(self):
        self.plexer.set_default_token(_DATA)
        self.plexer += T(_HTML_OPEN), '<'
        self.plexer += T(_HTML_OPEN_EXIT), '</'
        self.plexer += T(_HTML_CLOSE), '>'
        self.plexer += T(_HTML_COMMENT_OPEN), '<!--'
        self.plexer += T(_HTML_COMMENT_CLOSE), '-->'
        self.plexer += T(_DELIMITER), ' ', '\n', '\r', '\t'
        self.plexer += T(_ASSIGNMENT), '='
        self.plexer += T(_TEXT_DELIMITER), '\'', '"'
        self.plexer += T(_BRACKET_OPEN), '(', '[', '{'
        self.plexer += T(_BRACKET_CLOSE), ')', ']', '}'
        self.plexer += T(_ESCAPE_CHAR), '\\'

        self.parser.set_previous_token('')

        self.parser += '', _HTML_OPEN
        self.parser += '', _DELIMITER
        self.parser += _HTML_OPEN, _DATA
        self.parser += _DATA, _DATA
        self.parser += _DATA, _HTML_CLOSE, self._build_HTML_Tag
        self.parser += _HTML_CLOSE, _HTML_OPEN
        self.parser += _DATA, _ASSIGNMENT
        self.parser += _ASSIGNMENT, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _DATA
        self.parser += _DATA, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _HTML_CLOSE, self._build_HTML_Tag
        self.parser += _ASSIGNMENT, _DATA
        self.parser += _HTML_CLOSE, _DATA
        self.parser += _DATA, _HTML_OPEN_EXIT, self._build_text
        self.parser += _HTML_OPEN_EXIT, _DATA
        self.parser += _ASSIGNMENT, _ASSIGNMENT
        self.parser += _HTML_CLOSE, _BRACKET_OPEN
        self.parser += _BRACKET_OPEN, _DATA
        self.parser += _DATA, _BRACKET_OPEN
        self.parser += _BRACKET_OPEN, _BRACKET_CLOSE
        self.parser += _BRACKET_CLOSE, _BRACKET_OPEN
        self.parser += _BRACKET_CLOSE, _DELIMITER
        self.parser += _DELIMITER, _BRACKET_OPEN
        self.parser += _ASSIGNMENT, _BRACKET_OPEN
        self.parser += _TEXT_DELIMITER, _BRACKET_CLOSE
        self.parser += _BRACKET_CLOSE, _DATA
        self.parser += _DATA, _BRACKET_CLOSE
        self.parser += _BRACKET_CLOSE, _BRACKET_CLOSE
        self.parser += _BRACKET_OPEN, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _ASSIGNMENT
        self.parser += _BRACKET_CLOSE, _ASSIGNMENT
        self.parser += _BRACKET_OPEN, _BRACKET_OPEN
        self.parser += _BRACKET_CLOSE, _HTML_OPEN_EXIT, self._build_text
        self.parser += _HTML_CLOSE, _HTML_OPEN_EXIT, self._build_text
        self.parser += _DATA, _HTML_OPEN, self._build_text
        self.parser += _DATA, _ESCAPE_CHAR
        self.parser += _ESCAPE_CHAR, _DATA
        self.parser += _BRACKET_CLOSE, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _BRACKET_OPEN
        self.parser += _BRACKET_OPEN, _ESCAPE_CHAR
        self.parser += _ESCAPE_CHAR, _ESCAPE_CHAR
        self.parser += _BRACKET_CLOSE, _ESCAPE_CHAR
        self.parser += _DATA, _DELIMITER
        self.parser += _DELIMITER, _DATA
        self.parser += _TEXT_DELIMITER, _DELIMITER
        self.parser += _BRACKET_OPEN, _DELIMITER
        self.parser += _DELIMITER, _HTML_OPEN_EXIT, self._build_text
        self.parser += _DELIMITER, _ASSIGNMENT
        self.parser += _ASSIGNMENT, _DELIMITER
        self.parser += _DELIMITER, _BRACKET_CLOSE
        self.parser += _HTML_CLOSE, _DELIMITER
        self.parser += _DELIMITER, _HTML_OPEN, self._build_text
        self.parser += _DELIMITER, _DELIMITER
        self.parser += _DELIMITER, _ESCAPE_CHAR
        self.parser += _DELIMITER, _HTML_CLOSE, self._build_HTML_Tag
        self.parser += _DELIMITER, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _TEXT_DELIMITER, _HTML_OPEN, self._build_text
        self.parser += _ASSIGNMENT, _ESCAPE_CHAR
        self.parser += _ESCAPE_CHAR, _TEXT_DELIMITER
        self.parser += _HTML_OPEN, _ESCAPE_CHAR
        self.parser += _HTML_CLOSE, _ESCAPE_CHAR
        self.parser += _HTML_CLOSE, _TEXT_DELIMITER, self._read_string_literals
        self.parser += _BRACKET_CLOSE, _HTML_OPEN, self._build_text
        self.parser += _ASSIGNMENT, _BRACKET_CLOSE
        self.parser += _HTML_CLOSE, _ASSIGNMENT
        self.parser += _ASSIGNMENT, _HTML_OPEN, self._build_text
        self.parser += _BRACKET_OPEN, _HTML_OPEN, self._build_text
        self.parser += _DELIMITER, _HTML_COMMENT_OPEN
        self.parser += _HTML_COMMENT_OPEN, _DELIMITER
        self.parser += _DELIMITER, _HTML_COMMENT_CLOSE
        self.parser += _HTML_COMMENT_CLOSE, _DELIMITER
        self.parser += _ASSIGNMENT, _HTML_OPEN_EXIT, self._build_text
        self.parser += _HTML_OPEN, _ASSIGNMENT
        self.parser += _ASSIGNMENT, _HTML_CLOSE
        self.parser += _ESCAPE_CHAR, _DELIMITER
        self.parser += _TEXT_DELIMITER, _ESCAPE_CHAR
        self.parser += _TEXT_DELIMITER, _HTML_OPEN_EXIT, self._build_text
        self.parser += _ESCAPE_CHAR, _HTML_OPEN
        self.parser += _HTML_CLOSE, _BRACKET_CLOSE
        self.parser += _BRACKET_OPEN, _ASSIGNMENT
        self.parser += _BRACKET_OPEN, _HTML_OPEN_EXIT, self._build_text
        self.parser += _ESCAPE_CHAR, _BRACKET_OPEN
        self.parser += _ESCAPE_CHAR, _HTML_OPEN_EXIT, self._build_text
        pass

    def _build_HTML_Tag(self, parser:Parser, element):
        tag = ''
        data = []
        while len(parser._stack) > 0:
            elem = parser._stack.pop(0)
            tag += elem['Data']
            data.append(elem)
        tag += element['Data']
        data.append(element)
        buildTag = HTMLTag(tag, data)
        self._HTML_DATA.append(buildTag)
        self._last_tag = buildTag
        pass

    def _build_text(self, parser:Parser, element):
        data = ''
        while len(parser._stack) > 0:
            elem = parser._stack.pop(0)
            data+= elem['Data']
        parser._stack.append(element)
        self._HTML_DATA.append(HTMLData(data))
        pass

    def _read_string_literals(self, parser:Parser, element):
        last = element
        data = element['Data']
        cursor = len(parser._stack) -1
        #print(last)
        while cursor > 0:
            next_elment = parser._stack[cursor]
            data = next_elment['Data'] + data
            #print(next_elment)
            if next_elment['Token'] == _TEXT_DELIMITER and next_elment['Data'] == last['Data']:
                if cursor -1 > 0 and parser._stack[cursor-1]['Token'] == _ESCAPE_CHAR:
                    cursor -= 1
                    continue
                del parser._stack[cursor:]
                #print('Read:', data)
                parser._stack.append({'Token': _LITERAL, 'Data': data})
                return
            cursor -= 1
        parser._stack.append(element)

    def html_parse(self, page_url:str = '', request_pause = 0) -> HTMLPage:
        self._HTML_DATA = []
        time.sleep(request_pause)
        page = requests.get(page_url).text
        
        data = self.plexer.parse(page)

        try:
            self.parser.parse(data)
        except ParserException as ex:
            print(ex)
            for e in self.parser._stack:
                print(e)

        #compackt data into open tag
        outer_count = 0
        while outer_count < len(self._HTML_DATA):
            outer_elment = self._HTML_DATA[outer_count]
            if isinstance(outer_elment, HTMLTag) and outer_elment.open_tag:
                inner_count = outer_count + 1
                while inner_count < len(self._HTML_DATA):
                    inner_element = self._HTML_DATA[inner_count]
                    if isinstance(inner_element, HTMLTag) and not inner_element.tag_name in _HTML_VOID_TYPES:
                        outer_elment.set_HTML_Data(self._HTML_DATA[outer_count+1:inner_count])
                        break

                    inner_count += 1

            outer_count += 1


        htmlPage = HTMLPage()
        for element in self._HTML_DATA:
            htmlPage.raw_data.append(element)
            if isinstance(element, HTMLTag):
                htmlPage.tags.append(element)
            if isinstance(element, HTMLData):
                htmlPage.data.append(element)

        return htmlPage