# -*- coding: utf-8 -*-

import re

# INTERNAL USE ONLY REGEX!

NUMBER_RE = re.compile(r'^([+\-]?)((\d+)(\.\d+)?(e\d+)?|\.\d+)$')

URLS_RAW_STRING = (
    r'([a-z-]+://)'  # scheme
    r'([a-z_\d-]+:[a-z_\d-]+@)?'  # user:password
    r'(www\.)?'  # www.
    r'((?<!\.)[a-z\d]+[a-z\d.-]+\.[a-z]{2,6}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|localhost)'  # domain
    r'(:\d{2,})?'  # port number
    r'(/[a-z\d_%+-]*)*'  # folders
    r'(\.[a-z\d_%+-]+)*'  # file extension
    r'(\?[a-z\d_+%-=]*)?'  # query string
    r'(#\S*)?'  # hash
)

URL_RE = re.compile(r'^{}$'.format(URLS_RAW_STRING), re.IGNORECASE)

URLS_RE = re.compile(r'({})'.format(URLS_RAW_STRING), re.IGNORECASE)

ESCAPED_AT_SIGN = re.compile(r'(?!"[^"]*)@+(?=[^"]*")|\\@')

EMAILS_RAW_STRING = r"[a-zA-Z\d._\+\-'`!%#$&*/=\?\^\{\}\|~\\]+@[a-z\d-]+\.?[a-z\d-]+\.[a-z]{2,4}"

EMAIL_RE = re.compile(r'^{}$'.format(EMAILS_RAW_STRING))

EMAILS_RE = re.compile(r'({})'.format(EMAILS_RAW_STRING))

CAMEL_CASE_TEST_RE = re.compile(r'^[a-zA-Z]*([a-z]+[A-Z]+|[A-Z]+[a-z]+)[a-zA-Z\d]*$')

CAMEL_CASE_REPLACE_RE = re.compile(r'([a-z]|[A-Z]+)(?=[A-Z])')

SNAKE_CASE_TEST_RE = re.compile(r'^([a-z]+\d*_[a-z\d_]*|_+[a-z\d]+[a-z\d_]*)$', re.IGNORECASE)

SNAKE_CASE_TEST_DASH_RE = re.compile(r'([a-z]+\d*-[a-z\d-]*|-+[a-z\d]+[a-z\d-]*)$', re.IGNORECASE)

SNAKE_CASE_REPLACE_RE = re.compile(r'(_)([a-z\d])')

SNAKE_CASE_REPLACE_DASH_RE = re.compile(r'(-)([a-z\d])')

CREDIT_CARDS = {
    'VISA': re.compile(r'^4\d{12}(?:\d{3})?$'),
    'MASTERCARD': re.compile(r'^5[1-5]\d{14}$'),
    'AMERICAN_EXPRESS': re.compile(r'^3[47]\d{13}$'),
    'DINERS_CLUB': re.compile(r'^3(?:0[0-5]|[68]\d)\d{11}$'),
    'DISCOVER': re.compile(r'^6(?:011|5\d{2})\d{12}$'),
    'JCB': re.compile(r'^(?:2131|1800|35\d{3})\d{11}$')
}

JSON_WRAPPER_RE = re.compile(r'^\s*[\[{]\s*(.*)\s*[\}\]]\s*$', re.MULTILINE | re.DOTALL)

UUID_RE = re.compile(r'^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$', re.IGNORECASE)

UUID_HEX_OK_RE = re.compile(r'^[a-f\d]{8}-?[a-f\d]{4}-?[a-f\d]{4}-?[a-f\d]{4}-?[a-f\d]{12}$', re.IGNORECASE)

SHALLOW_IP_V4_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

IP_V6_RE = re.compile(r'^([a-z\d]{0,4}:){7}[a-z\d]{0,4}$', re.IGNORECASE)

WORDS_COUNT_RE = re.compile(r'\W*[^\W_]+\W*', re.IGNORECASE | re.MULTILINE | re.UNICODE)

HTML_RE = re.compile(
    r'((<([a-z]+:)?[a-z]+[^>]*/?>)(.*?(</([a-z]+:)?[a-z]+>))?|<!--.*-->|<!doctype.*>)',
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

HTML_TAG_ONLY_RE = re.compile(
    r'(<([a-z]+:)?[a-z]+[^>]*/?>|</([a-z]+:)?[a-z]+>|<!--.*-->|<!doctype.*>)',
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

SPACES_RE = re.compile(r'\s')

PRETTIFY_RE = {
    # match repetitions of signs that should not be repeated (like multiple spaces or duplicated quotes)
    'DUPLICATES': re.compile(
        r'(\({2,}|\){2,}|\[{2,}|\]{2,}|{{2,}|\}{2,}|:{2,}|,{2,}|;{2,}|\+{2,}|-{2,}|\s{2,}|%{2,}|={2,}|"{2,}|\'{2,})',
        re.MULTILINE
    ),

    # check that a sign cannot have a space before or missing a space after,
    # unless it is a dot or a comma, where numbers may follow (5.5 or 5,5 is ok)
    'RIGHT_SPACE': re.compile(
        r'('
        r'(?<=[^\s\d]),(?=[^\s\d])|\s,\s|\s,(?=[^\s\d])|\s,(?!.)|'  # comma (,)
        r'(?<=[^\s\d.])\.+(?=[^\s\d.])|\s\.+\s|\s\.+(?=[^\s\d])|\s\.+(?!\.)|'  # dot (.)
        r'(?<=\S);(?=\S)|\s;\s|\s;(?=\S)|\s;(?!.)|'  # semicolon (;)
        r'(?<=\S):(?=\S)|\s:\s|\s:(?=\S)|\s:(?!.)|'  # colon (:)
        r'(?<=[^\s!])!+(?=[^\s!])|\s!+\s|\s!+(?=[^\s!])|\s!+(?!!)|'  # exclamation (!)
        r'(?<=[^\s?])\?+(?=[^\s?])|\s\?+\s|\s\?+(?=[^\s?])|\s\?+(?!\?)|'  # question (?)
        r'\d%(?=\S)|(?<=\d)\s%\s|(?<=\d)\s%(?=\S)|(?<=\d)\s%(?!.)'  # percentage (%)
        r')',
        re.MULTILINE | re.DOTALL
    ),

    'LEFT_SPACE': re.compile(
        r'('

        # quoted text ("hello world")
        r'\s"[^"]+"(?=[?.:!,;])|(?<=\S)"[^"]+"\s|(?<=\S)"[^"]+"(?=[?.:!,;])|'

        # text in round brackets
        r'\s\([^)]+\)(?=[?.:!,;])|(?<=\S)\([^)]+\)\s|(?<=\S)(\([^)]+\))(?=[?.:!,;])'

        r')',
        re.MULTILINE | re.DOTALL
    ),

    # finds the first char in the string (therefore this must not be MULTILINE)
    'UPPERCASE_FIRST_LETTER': re.compile(r'^\s*\w', re.UNICODE),

    # match chars that must be followed by uppercase letters (like ".", "?"...)
    'UPPERCASE_AFTER_SIGN': re.compile(r'([.?!]\s\w)', re.MULTILINE | re.UNICODE),

    'SPACES_AROUND': re.compile(
        r'('
        r'(?<=\S)\+(?=\S)|(?<=\S)\+\s|\s\+(?=\S)|'  # plus (+)
        r'(?<=\S)-(?=\S)|(?<=\S)-\s|\s-(?=\S)|'  # minus (-)
        r'(?<=\S)/(?=\S)|(?<=\S)/\s|\s/(?=\S)|'  # division (/)
        r'(?<=\S)\*(?=\S)|(?<=\S)\*\s|\s\*(?=\S)|'  # multiplication (*)
        r'(?<=\S)=(?=\S)|(?<=\S)=\s|\s=(?=\S)|'  # equal (=)

        # quoted text ("hello world")
        r'\s"[^"]+"(?=[^\s?.:!,;])|(?<=\S)"[^"]+"\s|(?<=\S)"[^"]+"(?=[^\s?.:!,;])|'

        # text in round brackets
        r'\s\([^)]+\)(?=[^\s?.:!,;])|(?<=\S)\([^)]+\)\s|(?<=\S)(\([^)]+\))(?=[^\s?.:!,;])'

        r')',
        re.MULTILINE | re.DOTALL
    ),

    'SPACES_INSIDE': re.compile(
        r'('
        r'(?<=")[^"]+(?=")|'  # quoted text ("hello world")
        r'(?<=\()[^)]+(?=\))'  # text in round brackets
        r')',
        re.MULTILINE | re.DOTALL
    ),

    'SAXON_GENITIVE': re.compile(
        r'('
        r'(?<=\w)\'\ss\s|(?<=\w)\s\'s(?=\w)|(?<=\w)\s\'s\s(?=\w)'
        r')',
        re.MULTILINE | re.UNICODE
    )
}

NO_LETTERS_OR_NUMBERS_RE = re.compile(r'[^\w\d]+|_+', re.IGNORECASE | re.UNICODE)

MARGIN_RE = re.compile(r'^[^\S\r\n]+')

LOCALE_RE = re.compile(r'^[a-z]{2}_[A-Z]{2}$')

INSENSITIVE_LOCALE_RE = re.compile(r'^[a-z]{2}_[a-z]{2}$', re.IGNORECASE)
