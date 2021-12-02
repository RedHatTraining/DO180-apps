# -*- coding: utf-8 -*-

# public api to export
__all__ = [
    'is_string',
    'is_full_string',
    'is_number',
    'is_integer',
    'is_decimal',
    'is_url',
    'is_email',
    'is_credit_card',
    'is_camel_case',
    'is_snake_case',
    'is_json',
    'is_uuid',
    'is_ip_v4',
    'is_ip_v6',
    'is_ip',
    'is_isbn_10',
    'is_isbn_13',
    'is_isbn',
    'is_palindrome',
    'is_pangram',
    'is_isogram',
    'is_slug',
    'contains_html',
    'words_count',
]

import json
import string
from typing import Any, Optional, List

from ._regex import *
from .errors import InvalidInputError


# PRIVATE API


class __ISBNChecker:
    def __init__(self, input_string: str, normalize: bool = True):
        if not is_string(input_string):
            raise InvalidInputError(input_string)

        self.input_string = input_string.replace('-', '') if normalize else input_string

    def is_isbn_13(self) -> bool:
        if len(self.input_string) == 13:
            product = 0

            try:
                for index, digit in enumerate(self.input_string):
                    weight = 1 if (index % 2 == 0) else 3
                    product += int(digit) * weight

                return product % 10 == 0

            except ValueError:
                pass

        return False

    def is_isbn_10(self) -> bool:
        if len(self.input_string) == 10:
            product = 0

            try:
                for index, digit in enumerate(self.input_string):
                    product += int(digit) * (index + 1)

                return product % 11 == 0

            except ValueError:
                pass

        return False


# PUBLIC API

def is_string(obj: Any) -> bool:
    """
    Checks if an object is a string.

    *Example:*

    >>> is_string('foo') # returns true
    >>> is_string(b'foo') # returns false

    :param obj: Object to test.
    :return: True if string, false otherwise.
    """
    return isinstance(obj, str)


def is_full_string(input_string: Any) -> bool:
    """
    Check if a string is not empty (it must contains at least one non space character).

    *Examples:*

    >>> is_full_string(None) # returns false
    >>> is_full_string('') # returns false
    >>> is_full_string(' ') # returns false
    >>> is_full_string('hello') # returns true

    :param input_string: String to check.
    :type input_string: str
    :return: True if not empty, false otherwise.
    """
    return is_string(input_string) and input_string.strip() != ''


def is_number(input_string: str) -> bool:
    """
    Checks if a string is a valid number.

    The number can be a signed (eg: +1, -2, -3.3) or unsigned (eg: 1, 2, 3.3) integer or double
    or use the "scientific notation" (eg: 1e5).

    *Examples:*

    >>> is_number('42') # returns true
    >>> is_number('19.99') # returns true
    >>> is_number('-9.12') # returns true
    >>> is_number('1e3') # returns true
    >>> is_number('1 2 3') # returns false

    :param input_string: String to check
    :type input_string: str
    :return: True if the string represents a number, false otherwise
    """
    if not isinstance(input_string, str):
        raise InvalidInputError(input_string)

    return NUMBER_RE.match(input_string) is not None


def is_integer(input_string: str) -> bool:
    """
    Checks whether the given string represents an integer or not.

    An integer may be signed or unsigned or use a "scientific notation".

    *Examples:*

    >>> is_integer('42') # returns true
    >>> is_integer('42.0') # returns false

    :param input_string: String to check
    :type input_string: str
    :return: True if integer, false otherwise
    """
    return is_number(input_string) and '.' not in input_string


def is_decimal(input_string: str) -> bool:
    """
    Checks whether the given string represents a decimal or not.

    A decimal may be signed or unsigned or use a "scientific notation".

    >>> is_decimal('42.0') # returns true
    >>> is_decimal('42') # returns false

    :param input_string: String to check
    :type input_string: str
    :return: True if integer, false otherwise
    """
    return is_number(input_string) and '.' in input_string


# Full url example:
# scheme://username:password@www.domain.com:8042/folder/subfolder/file.extension?param=value&param2=value2#hash
def is_url(input_string: Any, allowed_schemes: Optional[List[str]] = None) -> bool:
    """
    Check if a string is a valid url.

    *Examples:*

    >>> is_url('http://www.mysite.com') # returns true
    >>> is_url('https://mysite.com') # returns true
    >>> is_url('.mysite.com') # returns false

    :param input_string: String to check.
    :type input_string: str
    :param allowed_schemes: List of valid schemes ('http', 'https', 'ftp'...). Default to None (any scheme is valid).
    :type allowed_schemes: Optional[List[str]]
    :return: True if url, false otherwise
    """
    if not is_full_string(input_string):
        return False

    valid = URL_RE.match(input_string) is not None

    if allowed_schemes:
        return valid and any([input_string.startswith(s) for s in allowed_schemes])

    return valid


def is_email(input_string: Any) -> bool:
    """
    Check if a string is a valid email.

    Reference: https://tools.ietf.org/html/rfc3696#section-3

    *Examples:*

    >>> is_email('my.email@the-provider.com') # returns true
    >>> is_email('@gmail.com') # returns false

    :param input_string: String to check.
    :type input_string: str
    :return: True if email, false otherwise.
    """
    # first simple "pre check": it must be a non empty string with max len 320 and cannot start with a dot
    if not is_full_string(input_string) or len(input_string) > 320 or input_string.startswith('.'):
        return False

    try:
        # we expect 2 tokens, one before "@" and one after, otherwise we have an exception and the email is not valid
        head, tail = input_string.split('@')

        # head's size must be <= 64, tail <= 255, head must not start with a dot or contain multiple consecutive dots
        if len(head) > 64 or len(tail) > 255 or head.endswith('.') or ('..' in head):
            return False

        # removes escaped spaces, so that later on the test regex will accept the string
        head = head.replace('\\ ', '')
        if head.startswith('"') and head.endswith('"'):
            head = head.replace(' ', '')[1:-1]

        return EMAIL_RE.match(head + '@' + tail) is not None

    except ValueError:
        # borderline case in which we have multiple "@" signs but the head part is correctly escaped
        if ESCAPED_AT_SIGN.search(input_string) is not None:
            # replace "@" with "a" in the head
            return is_email(ESCAPED_AT_SIGN.sub('a', input_string))

        return False


def is_credit_card(input_string: Any, card_type: str = None) -> bool:
    """
    Checks if a string is a valid credit card number.
    If card type is provided then it checks against that specific type only,
    otherwise any known credit card number will be accepted.

    Supported card types are the following:

    - VISA
    - MASTERCARD
    - AMERICAN_EXPRESS
    - DINERS_CLUB
    - DISCOVER
    - JCB

    :param input_string: String to check.
    :type input_string: str
    :param card_type: Card type. Default to None (any card).
    :type card_type: str

    :return: True if credit card, false otherwise.
    """
    if not is_full_string(input_string):
        return False

    if card_type:
        if card_type not in CREDIT_CARDS:
            raise KeyError(
                'Invalid card type "{}". Valid types are: {}'.format(card_type, ', '.join(CREDIT_CARDS.keys()))
            )
        return CREDIT_CARDS[card_type].match(input_string) is not None

    for c in CREDIT_CARDS:
        if CREDIT_CARDS[c].match(input_string) is not None:
            return True

    return False


def is_camel_case(input_string: Any) -> bool:
    """
    Checks if a string is formatted as camel case.

    A string is considered camel case when:

    - it's composed only by letters ([a-zA-Z]) and optionally numbers ([0-9])
    - it contains both lowercase and uppercase letters
    - it does not start with a number

    *Examples:*

    >>> is_camel_case('MyString') # returns true
    >>> is_camel_case('mystring') # returns false

    :param input_string: String to test.
    :type input_string: str
    :return: True for a camel case string, false otherwise.
    """
    return is_full_string(input_string) and CAMEL_CASE_TEST_RE.match(input_string) is not None


def is_snake_case(input_string: Any, separator: str = '_') -> bool:
    """
    Checks if a string is formatted as "snake case".

    A string is considered snake case when:

    - it's composed only by lowercase/uppercase letters and digits
    - it contains at least one underscore (or provided separator)
    - it does not start with a number

    *Examples:*

    >>> is_snake_case('foo_bar_baz') # returns true
    >>> is_snake_case('foo') # returns false

    :param input_string: String to test.
    :type input_string: str
    :param separator: String to use as separator.
    :type separator: str
    :return: True for a snake case string, false otherwise.
    """
    if is_full_string(input_string):
        re_map = {
            '_': SNAKE_CASE_TEST_RE,
            '-': SNAKE_CASE_TEST_DASH_RE
        }
        re_template = r'([a-z]+\d*{sign}[a-z\d{sign}]*|{sign}+[a-z\d]+[a-z\d{sign}]*)'
        r = re_map.get(
            separator,
            re.compile(re_template.format(sign=re.escape(separator)), re.IGNORECASE)
        )

        return r.match(input_string) is not None

    return False


def is_json(input_string: Any) -> bool:
    """
    Check if a string is a valid json.

    *Examples:*

    >>> is_json('{"name": "Peter"}') # returns true
    >>> is_json('[1, 2, 3]') # returns true
    >>> is_json('{nope}') # returns false

    :param input_string: String to check.
    :type input_string: str
    :return: True if json, false otherwise
    """
    if is_full_string(input_string) and JSON_WRAPPER_RE.match(input_string) is not None:
        try:
            return isinstance(json.loads(input_string), (dict, list))
        except (TypeError, ValueError, OverflowError):
            pass

    return False


def is_uuid(input_string: Any, allow_hex: bool = False) -> bool:
    """
    Check if a string is a valid UUID.

    *Example:*

    >>> is_uuid('6f8aa2f9-686c-4ac3-8766-5712354a04cf') # returns true
    >>> is_uuid('6f8aa2f9686c4ac387665712354a04cf') # returns false
    >>> is_uuid('6f8aa2f9686c4ac387665712354a04cf', allow_hex=True) # returns true

    :param input_string: String to check.
    :type input_string: str
    :param allow_hex: True to allow UUID hex representation as valid, false otherwise (default)
    :type allow_hex: bool
    :return: True if UUID, false otherwise
    """
    # string casting is used to allow UUID itself as input data type
    s = str(input_string)

    if allow_hex:
        return UUID_HEX_OK_RE.match(s) is not None

    return UUID_RE.match(s) is not None


def is_ip_v4(input_string: Any) -> bool:
    """
    Checks if a string is a valid ip v4.

    *Examples:*

    >>> is_ip_v4('255.200.100.75') # returns true
    >>> is_ip_v4('nope') # returns false (not an ip)
    >>> is_ip_v4('255.200.100.999') # returns false (999 is out of range)

    :param input_string: String to check.
    :type input_string: str
    :return: True if an ip v4, false otherwise.
    """
    if not is_full_string(input_string) or SHALLOW_IP_V4_RE.match(input_string) is None:
        return False

    # checks that each entry in the ip is in the valid range (0 to 255)
    for token in input_string.split('.'):
        if not (0 <= int(token) <= 255):
            return False

    return True


def is_ip_v6(input_string: Any) -> bool:
    """
    Checks if a string is a valid ip v6.

    *Examples:*

    >>> is_ip_v6('2001:db8:85a3:0000:0000:8a2e:370:7334') # returns true
    >>> is_ip_v6('2001:db8:85a3:0000:0000:8a2e:370:?') # returns false (invalid "?")

    :param input_string: String to check.
    :type input_string: str
    :return: True if a v6 ip, false otherwise.
    """
    return is_full_string(input_string) and IP_V6_RE.match(input_string) is not None


def is_ip(input_string: Any) -> bool:
    """
    Checks if a string is a valid ip (either v4 or v6).

    *Examples:*

    >>> is_ip('255.200.100.75') # returns true
    >>> is_ip('2001:db8:85a3:0000:0000:8a2e:370:7334') # returns true
    >>> is_ip('1.2.3') # returns false

    :param input_string: String to check.
    :type input_string: str
    :return: True if an ip, false otherwise.
    """
    return is_ip_v6(input_string) or is_ip_v4(input_string)


def is_palindrome(input_string: Any, ignore_spaces: bool = False, ignore_case: bool = False) -> bool:
    """
    Checks if the string is a palindrome (https://en.wikipedia.org/wiki/Palindrome).

    *Examples:*

    >>> is_palindrome('LOL') # returns true
    >>> is_palindrome('Lol') # returns false
    >>> is_palindrome('Lol', ignore_case=True) # returns true
    >>> is_palindrome('ROTFL') # returns false

    :param input_string: String to check.
    :type input_string: str
    :param ignore_spaces: False if white spaces matter (default), true otherwise.
    :type ignore_spaces: bool
    :param ignore_case: False if char case matters (default), true otherwise.
    :type ignore_case: bool
    :return: True if the string is a palindrome (like "otto", or "i topi non avevano nipoti" if strict=False),\
    False otherwise
    """
    if not is_full_string(input_string):
        return False

    if ignore_spaces:
        input_string = SPACES_RE.sub('', input_string)

    string_len = len(input_string)

    # Traverse the string one char at step, and for each step compares the
    # "head_char" (the one on the left of the string) to the "tail_char" (the one on the right).
    # In this way we avoid to manipulate the whole string in advance if not necessary and provide a faster
    # algorithm which can scale very well for long strings.
    for index in range(string_len):
        head_char = input_string[index]
        tail_char = input_string[string_len - index - 1]

        if ignore_case:
            head_char = head_char.lower()
            tail_char = tail_char.lower()

        if head_char != tail_char:
            return False

    return True


def is_pangram(input_string: Any) -> bool:
    """
    Checks if the string is a pangram (https://en.wikipedia.org/wiki/Pangram).

    *Examples:*

    >>> is_pangram('The quick brown fox jumps over the lazy dog') # returns true
    >>> is_pangram('hello world') # returns false

    :param input_string: String to check.
    :type input_string: str
    :return: True if the string is a pangram, False otherwise.
    """
    if not is_full_string(input_string):
        return False

    return set(SPACES_RE.sub('', input_string)).issuperset(set(string.ascii_lowercase))


def is_isogram(input_string: Any) -> bool:
    """
    Checks if the string is an isogram (https://en.wikipedia.org/wiki/Isogram).

    *Examples:*

    >>> is_isogram('dermatoglyphics') # returns true
    >>> is_isogram('hello') # returns false

    :param input_string: String to check.
    :type input_string: str
    :return: True if isogram, false otherwise.
    """
    return is_full_string(input_string) and len(set(input_string)) == len(input_string)


def is_slug(input_string: Any, separator: str = '-') -> bool:
    """
    Checks if a given string is a slug (as created by `slugify()`).

    *Examples:*

    >>> is_slug('my-blog-post-title') # returns true
    >>> is_slug('My blog post title') # returns false

    :param input_string: String to check.
    :type input_string: str
    :param separator: Join sign used by the slug.
    :type separator: str
    :return: True if slug, false otherwise.
    """
    if not is_full_string(input_string):
        return False

    rex = r'^([a-z\d]+' + re.escape(separator) + r'*?)*[a-z\d]$'

    return re.match(rex, input_string) is not None


def contains_html(input_string: str) -> bool:
    """
    Checks if the given string contains HTML/XML tags.

    By design, this function matches ANY type of tag, so don't expect to use it
    as an HTML validator, its goal is to detect "malicious" or undesired tags in the text.

    *Examples:*

    >>> contains_html('my string is <strong>bold</strong>') # returns true
    >>> contains_html('my string is not bold') # returns false

    :param input_string: Text to check
    :type input_string: str
    :return: True if string contains html, false otherwise.
    """
    if not is_string(input_string):
        raise InvalidInputError(input_string)

    return HTML_RE.search(input_string) is not None


def words_count(input_string: str) -> int:
    """
    Returns the number of words contained into the given string.

    This method is smart, it does consider only sequence of one or more letter and/or numbers
    as "words", so a string like this: "! @ # % ... []" will return zero!
    Moreover it is aware of punctuation, so the count for a string like "one,two,three.stop"
    will be 4 not 1 (even if there are no spaces in the string).

    *Examples:*

    >>> words_count('hello world') # returns 2
    >>> words_count('one,two,three.stop') # returns 4

    :param input_string: String to check.
    :type input_string: str
    :return: Number of words.
    """
    if not is_string(input_string):
        raise InvalidInputError(input_string)

    return len(WORDS_COUNT_RE.findall(input_string))


def is_isbn_10(input_string: str, normalize: bool = True) -> bool:
    """
    Checks if the given string represents a valid ISBN 10 (International Standard Book Number).
    By default hyphens in the string are ignored, so digits can be separated in different ways, by calling this
    function with `normalize=False` only digit-only strings will pass the validation.

    *Examples:*

    >>> is_isbn_10('1506715214') # returns true
    >>> is_isbn_10('150-6715214') # returns true
    >>> is_isbn_10('150-6715214', normalize=False) # returns false

    :param input_string: String to check.
    :param normalize: True to ignore hyphens ("-") in the string (default), false otherwise.
    :return: True if valid ISBN 10, false otherwise.
    """
    checker = __ISBNChecker(input_string, normalize)
    return checker.is_isbn_10()


def is_isbn_13(input_string: str, normalize: bool = True) -> bool:
    """
    Checks if the given string represents a valid ISBN 13 (International Standard Book Number).
    By default hyphens in the string are ignored, so digits can be separated in different ways, by calling this
    function with `normalize=False` only digit-only strings will pass the validation.

    *Examples:*

    >>> is_isbn_13('9780312498580') # returns true
    >>> is_isbn_13('978-0312498580') # returns true
    >>> is_isbn_13('978-0312498580', normalize=False) # returns false

    :param input_string: String to check.
    :param normalize: True to ignore hyphens ("-") in the string (default), false otherwise.
    :return: True if valid ISBN 13, false otherwise.
    """
    checker = __ISBNChecker(input_string, normalize)
    return checker.is_isbn_13()


def is_isbn(input_string: str, normalize: bool = True) -> bool:
    """
    Checks if the given string represents a valid ISBN (International Standard Book Number).
    By default hyphens in the string are ignored, so digits can be separated in different ways, by calling this
    function with `normalize=False` only digit-only strings will pass the validation.

    *Examples:*

    >>> is_isbn('9780312498580') # returns true
    >>> is_isbn('1506715214') # returns true

    :param input_string: String to check.
    :param normalize: True to ignore hyphens ("-") in the string (default), false otherwise.
    :return: True if valid ISBN (10 or 13), false otherwise.
    """
    checker = __ISBNChecker(input_string, normalize)
    return checker.is_isbn_13() or checker.is_isbn_10()
