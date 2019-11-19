from enum import Enum, IntEnum


class TokenType(Enum):
    OPERATOR = 0
    STRING = 1
    NUMBER = 2
    BOOLEAN = 3
    NULL = 4
    BUFFER_READ = 5


class _Operators(IntEnum):
    BS = 8  # /b
    TAB = 9  # /t
    LF = 10  # /n
    FF = 12  # /f
    CR = 13  # /r
    DOUBLE_QUOTES = 34  # "
    COMMA = 44  # ,
    MINUS = 45  # -
    POINT = 46  # .
    FORWARD_SLASH = 47  # /
    ZERO = 48  # 0
    COLON = 58  # :
    LEFT_BRACE = 91  # [
    BACKWARD_SLASH = 92  # \
    RIGHT_BRACE = 93  # ]
    LOWER_CASE_A = 97  # a
    LOWER_CASE_B = 98  # b
    LOWER_CASE_E = 101  # e
    LOWER_CASE_F = 102  # f
    LOWER_CASE_L = 108  # l
    LOWER_CASE_N = 110  # n
    LOWER_CASE_R = 114  # r
    LOWER_CASE_S = 115  # s
    LOWER_CASE_U = 117  # u
    LOWER_CASE_T = 116  # f
    LEFT_BRACKET = 123  # {
    RIGHT_BRACKET = 125  # }


class _TokenizerState(Enum):
    WHITESPACE = 0
    INTEGER_0 = 1
    INTEGER_SIGN = 2
    INTEGER = 3
    INTEGER_EXP = 4
    INTEGER_EXP_0 = 5
    FLOATING_POINT_0 = 6
    FLOATING_POINT = 8
    STRING = 9
    STRING_ESCAPE = 10
    STRING_END = 11
    TRUE_1 = 12
    TRUE_2 = 13
    TRUE_3 = 14
    FALSE_1 = 15
    FALSE_2 = 16
    FALSE_3 = 17
    FALSE_4 = 18
    NULL_1 = 19
    NULL_2 = 20
    NULL_3 = 21
    UNICODE_1 = 22
    UNICODE_2 = 23
    UNICODE_3 = 24
    UNICODE_4 = 25
    UNICODE_5 = 26
    UNICODE_6 = 27


class JsonTokenize(object):
    def __init__(self, stream, buffer_events=False):
        self.__stream = stream
        self.__buffer_events = buffer_events
        self.__total_read = 0
        self.__buffer_index = 0

    @property
    def position(self):
        return self.__total_read + self.__buffer_index

    def tokenize(self):
        stream = self.__stream
        buffer_events = self.__buffer_events

        def is_delimiter(char):
            return char in b" \t\n{}[]:,"

        current_token = bytearray()
        local_char_code = bytearray()

        processor = _TokenizerState.WHITESPACE
        buffer_size = 1024 * 1024
        chars = stream.read(buffer_size)

        while chars:
            self.__buffer_index = 0

            l = len(chars)
            while self.__buffer_index < l:
                char = chars[self.__buffer_index]

                if processor == _TokenizerState.STRING:
                    if char == _Operators.DOUBLE_QUOTES:
                        self.__buffer_index += 1
                        yield (TokenType.STRING, current_token)
                        current_token = bytearray()
                        processor = _TokenizerState.STRING_END
                        continue

                    if char == _Operators.BACKWARD_SLASH:
                        processor = _TokenizerState.STRING_ESCAPE
                        self.__buffer_index += 1
                        continue

                    current_token.append(char)
                    self.__buffer_index += 1
                    continue

                if processor == _TokenizerState.WHITESPACE:
                    if char in b' \t\n':
                        self.__buffer_index += 1
                        continue

                    if char in b"{}[],:":
                        self.__buffer_index += 1
                        yield (TokenType.OPERATOR, char)
                        continue

                    if char == _Operators.DOUBLE_QUOTES:
                        self.__buffer_index += 1
                        processor = _TokenizerState.STRING
                        continue

                    if char in b"123456789":
                        processor = _TokenizerState.INTEGER
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.ZERO:
                        processor = _TokenizerState.INTEGER_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.MINUS:
                        processor = _TokenizerState.INTEGER_SIGN
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_F:
                        processor = _TokenizerState.FALSE_1
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_T:
                        processor = _TokenizerState.TRUE_1
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_N:
                        processor = _TokenizerState.NULL_1
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.STRING_ESCAPE:
                    if char in b"\\\"":
                        current_token.append(char)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_B:
                        current_token.append(_Operators.BS)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_F:
                        processor = _TokenizerState.STRING
                        current_token.append(_Operators.FF)
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_N:
                        current_token.append(_Operators.LF)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_T:
                        current_token.append(_Operators.TAB)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_R:
                        current_token.append(_Operators.CR)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.FORWARD_SLASH:
                        current_token.append(char)
                        processor = _TokenizerState.STRING
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.LOWER_CASE_U:
                        processor = _TokenizerState.UNICODE_1
                        local_char_code = bytearray()
                        self.__buffer_index += 1
                        continue

                    raise ValueError(f"Invalid string escape: {char}")

                if processor == _TokenizerState.STRING_END:
                    if is_delimiter(char):
                        processor = _TokenizerState.WHITESPACE
                        self.__buffer_index += 0
                        continue

                    raise ValueError(f"Expected whitespace or an operator after string.  Got '{char} at {self.__buffer_index}'")

                if processor == _TokenizerState.FLOATING_POINT_0:
                    if char in b"0123456789":
                        processor = _TokenizerState.FLOATING_POINT
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    raise ValueError("A number with a decimal point must be followed by a fractional part")

                if processor == _TokenizerState.INTEGER_0:
                    if char == _Operators.POINT:
                        processor = _TokenizerState.FLOATING_POINT_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char in b"eE":
                        processor = _TokenizerState.INTEGER_EXP_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if is_delimiter(char):
                        self.__buffer_index += 0
                        yield (TokenType.NUMBER, 0)
                        current_token = bytearray()

                        processor = _TokenizerState.WHITESPACE
                        continue

                    raise ValueError("A 0 must be followed by a '.' or a 'e'.  Got '{0}'".format(char))

                if processor == _TokenizerState.INTEGER:
                    if char in b"0123456789":
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char == _Operators.POINT:
                        processor = _TokenizerState.FLOATING_POINT_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char in b"eE":
                        processor = _TokenizerState.INTEGER_EXP_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if is_delimiter(char):
                        self.__buffer_index += 0
                        processor = _TokenizerState.WHITESPACE
                        yield (TokenType.NUMBER, int(current_token))
                        current_token = bytearray()
                        continue

                    raise ValueError("A number must contain only digits.  Got '{}'".format(char))

                if processor == _TokenizerState.INTEGER_SIGN:
                    if char == _Operators.ZERO:
                        processor = _TokenizerState.INTEGER_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char in b"123456789":
                        processor = _TokenizerState.INTEGER
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    raise ValueError("A - must be followed by a digit.  Got '{0}'".format(char))

                if processor == _TokenizerState.INTEGER_EXP_0:
                    if char in b"+-0123456789":
                        processor = _TokenizerState.INTEGER_EXP
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    raise ValueError("An e in a number must be followed by a '+', '-' or digit.  Got '{0}'".format(char))

                if processor == _TokenizerState.INTEGER_EXP:
                    if char in b"0123456789":
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if is_delimiter(char):
                        processor = _TokenizerState.WHITESPACE
                        self.__buffer_index += 0
                        yield (TokenType.NUMBER, float(current_token))
                        current_token = bytearray()
                        continue

                    raise ValueError("A number exponent must consist only of digits.  Got '{}'".format(char))

                if processor == _TokenizerState.FLOATING_POINT:
                    if char in b"0123456789":
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if char in b"eE":
                        processor = _TokenizerState.INTEGER_EXP_0
                        current_token.append(char)
                        self.__buffer_index += 1
                        continue

                    if is_delimiter(char):
                        self.__buffer_index += 0
                        yield (TokenType.NUMBER, float(current_token))
                        current_token = bytearray()
                        processor = _TokenizerState.WHITESPACE
                        continue

                    raise ValueError("A number must include only digits")

                if processor == _TokenizerState.FALSE_1:
                    if char == _Operators.LOWER_CASE_A:
                        processor = _TokenizerState.FALSE_2
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.FALSE_2:
                    if char == _Operators.LOWER_CASE_L:
                        processor = _TokenizerState.FALSE_3
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.FALSE_3:
                    if char == _Operators.LOWER_CASE_S:
                        processor = _TokenizerState.FALSE_4
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.FALSE_4:
                    if char == _Operators.LOWER_CASE_E:
                        processor = _TokenizerState.WHITESPACE
                        self.__buffer_index += 1
                        yield (TokenType.BOOLEAN, False)
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.TRUE_1:
                    if char == _Operators.LOWER_CASE_R:
                        processor = _TokenizerState.TRUE_2
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.TRUE_2:
                    if char == _Operators.LOWER_CASE_U:
                        processor = _TokenizerState.TRUE_3
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.TRUE_3:
                    if char == _Operators.LOWER_CASE_E:
                        processor = _TokenizerState.WHITESPACE
                        self.__buffer_index += 1
                        yield (TokenType.BOOLEAN, True)
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.NULL_1:
                    if char == _Operators.LOWER_CASE_U:
                        processor = _TokenizerState.NULL_2
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.NULL_2:
                    if char == _Operators.LOWER_CASE_L:
                        processor = _TokenizerState.NULL_3
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.NULL_3:
                    if char == _Operators.LOWER_CASE_L:
                        processor = _TokenizerState.WHITESPACE
                        self.__buffer_index += 1
                        yield (TokenType.NULL, None)
                        continue

                    raise ValueError("Invalid JSON character: '{0}'".format(char))

                if processor == _TokenizerState.UNICODE_1:
                    if char in b"0123456789abcdefABCDEF":
                        local_char_code.append(char)
                        processor = _TokenizerState.UNICODE_2
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid character code: {}".format(char))

                if processor == _TokenizerState.UNICODE_2:
                    if char in b"0123456789abcdefABCDEF":
                        local_char_code.append(char)
                        processor = _TokenizerState.UNICODE_3
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid character code: {}".format(char))

                if processor == _TokenizerState.UNICODE_3:
                    if char in b"0123456789abcdefABCDEF":
                        local_char_code.append(char)
                        processor = _TokenizerState.UNICODE_4
                        self.__buffer_index += 1
                        continue

                    raise ValueError("Invalid character code: {}".format(char))

                if processor == _TokenizerState.UNICODE_4:
                    if char in b"0123456789abcdefABCDEF":
                        local_char_code.append(char)

                        uni = int(local_char_code[:4], 16)

                        if 0xd800 <= uni <= 0xdbff:
                            processor = _TokenizerState.UNICODE_5
                        else:
                            processor = _TokenizerState.STRING

                        if len(local_char_code) == 8:
                            processor = _TokenizerState.STRING
                            uni2 = int(local_char_code[4:], 16)
                            if 0xdc00 <= uni2 <= 0xdfff:
                                uni = 0x10000 + (((uni - 0xd800) << 10) | (uni2 - 0xdc00))

                            current_token.extend(chr(uni).encode('utf8'))

                        self.__buffer_index += 1
                        continue

                    raise ValueError(f"Invalid character code: {char} {current_token} {local_char_code}")

                if processor == _TokenizerState.UNICODE_5:
                    if char != _Operators.BACKWARD_SLASH:
                        processor = _TokenizerState.STRING
                        uni = int(local_char_code, 16)
                        current_token.extend(chr(uni).encode('utf8'))
                        self.__buffer_index += 0
                        continue

                    processor = _TokenizerState.UNICODE_6
                    self.__buffer_index += 1
                    continue

                if processor == _TokenizerState.UNICODE_6:
                    if char != _Operators.LOWER_CASE_U:
                        processor = _TokenizerState.STRING_ESCAPE
                        uni = int(local_char_code, 16)
                        current_token.extend(chr(uni).encode('utf8'))
                        self.__buffer_index += 0
                        continue

                    processor = _TokenizerState.UNICODE_1
                    self.__buffer_index += 1
                    continue

            if chars == b' ':
                break

            if buffer_events:
                yield (TokenType.BUFFER_READ, buffer_size)

            self.__total_read += len(chars)
            chars = stream.read(buffer_size)
            buffer_size = len(chars)

            if not chars:
                chars = b' '

        if buffer_events:
            yield (TokenType.BUFFER_READ, buffer_size)

    def yajl_events(self):
        stack = []
        pending_value = False
        for token, value in self.tokenize():
            if token == TokenType.STRING:
                if not pending_value:
                    yield (JSONStreamerEvents.KEY_EVENT, value.decode('utf-8'))
                    continue

                yield (JSONStreamerEvents.VALUE_EVENT, value.decode('utf-8'))

                continue

            if token in (TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL):
                top = stack[-1]
                if top == _JSONCompositeType.OBJECT:
                    yield (JSONStreamerEvents.VALUE_EVENT, value)
                elif top is _JSONCompositeType.ARRAY:
                    yield (JSONStreamerEvents.ELEMENT_EVENT, value)
                else:
                    raise RuntimeError('Invalid json-streamer state')

                continue

            if token == TokenType.OPERATOR:
                if value == _Operators.LEFT_BRACKET:
                    yield (JSONStreamerEvents.OBJECT_START_EVENT, None)
                    stack.append(_JSONCompositeType.OBJECT)
                    pending_value = False
                    continue

                if value == _Operators.RIGHT_BRACKET:
                    stack.pop()
                    yield (JSONStreamerEvents.OBJECT_END_EVENT, None)
                    pending_value = False
                    continue

                if value == _Operators.RIGHT_BRACE:
                    stack.pop()
                    yield (JSONStreamerEvents.ARRAY_END_EVENT, None)
                    pending_value = False
                    continue

                if value == _Operators.LEFT_BRACE:
                    stack.append(_JSONCompositeType.ARRAY)
                    yield (JSONStreamerEvents.ARRAY_START_EVENT, None)
                    continue

                if value == _Operators.COLON:
                    pending_value = True
                    continue

                if value == _Operators.COMMA:
                    if stack[-1] == _JSONCompositeType.OBJECT:
                        pending_value = False

                    continue

                raise Exception('unknown operator')

            if token == TokenType.BUFFER_READ:
                yield (JSONStreamerEvents.BUFFER_READ, value)
                continue

            raise Exception('unknown token %s', token)


class _YajlState(Enum):
    NONE = 0
    STATE_MAP_START = 1


class JSONStreamerEvents(Enum):
    DOC_START = 1
    DOC_END = 2
    OBJECT_START_EVENT = 3
    OBJECT_END_EVENT = 4
    ARRAY_START_EVENT = 5
    ARRAY_END_EVENT = 6
    KEY_EVENT = 7
    VALUE_EVENT = 8
    ELEMENT_EVENT = 8
    BUFFER_READ = 10


class _JSONCompositeType(Enum):
    OBJECT = 1
    ARRAY = 2


class ObjectStreamerEvents(Enum):
    OBJECT_STREAM_START_EVENT = 1
    OBJECT_STREAM_END_EVENT = 2
    ARRAY_STREAM_START_EVENT = 3
    ARRAY_STREAM_END_EVENT = 4
    PAIR_EVENT = 5
    ELEMENT_EVENT = 6
    BUFFER_READ = 10


def yajl_object_streamer(gen):
    root = None
    obj_stack = []
    key_stack = []

    def _process_deep_entities():
        o = obj_stack.pop()
        key_depth = len(key_stack)
        if key_depth == 0:
            if len(obj_stack) == 0:
                yield ObjectStreamerEvents.ELEMENT_EVENT, o
                return

            obj_stack[-1].append(o)
        elif key_depth == 1:
            if len(obj_stack) == 0:
                k = key_stack.pop()
                yield ObjectStreamerEvents.PAIR_EVENT, (k, o)
                return

            top = obj_stack[-1]
            if isinstance(top, list):
                top.append(o)
            else:
                k = key_stack.pop()
                top[k] = o
        elif key_depth > 1:
            current_obj = obj_stack[-1]
            if type(current_obj) is list:
                current_obj.append(o)
            else:
                k = key_stack.pop()
                current_obj[k] = o

    for event, value in gen:
        if event == JSONStreamerEvents.OBJECT_START_EVENT:
            if root is None:
                root = _JSONCompositeType.OBJECT
                yield (ObjectStreamerEvents.OBJECT_STREAM_START_EVENT, None)
            else:
                d = {}
                obj_stack.append(d)

            continue

        if event == JSONStreamerEvents.OBJECT_END_EVENT:
            if len(obj_stack) > 0:
                yield from _process_deep_entities()
            else:
                yield (ObjectStreamerEvents.OBJECT_STREAM_END_EVENT, None)
                break

            continue

        if event == JSONStreamerEvents.ARRAY_START_EVENT:
            if root is None:
                root = _JSONCompositeType.ARRAY
                yield (ObjectStreamerEvents.ARRAY_START_EVENT, None)
            else:
                obj_stack.append([])

            continue

        if event == JSONStreamerEvents.ARRAY_END_EVENT:
            if len(obj_stack) > 0:
                yield from _process_deep_entities()
            else:
                yield (ObjectStreamerEvents.ARRAY_STREAM_END_EVENT, None)
                break

            continue

        if event == JSONStreamerEvents.KEY_EVENT:
            key_stack.append(value)
            continue

        if event == JSONStreamerEvents.VALUE_EVENT:
            k = key_stack.pop()
            if len(obj_stack) == 0:
                yield (ObjectStreamerEvents.PAIR_EVENT, (k, value))
            else:
                obj_stack[-1][k] = value

            continue

        if event == JSONStreamerEvents.ELEMENT_EVENT:
            if len(obj_stack) == 0:
                yield (ObjectStreamerEvents.ELEMENT_EVENT, value)
            else:
                obj_stack[-1].append(value)

            continue

        if event == JSONStreamerEvents.BUFFER_READ:
            yield (ObjectStreamerEvents.BUFFER_READ, value)
            continue
