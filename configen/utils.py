"""Common utilities."""

import math as m

_STANDARD_INT_LENGTHS = [8, 16, 32, 64]


def to_camel_case(name):
    """Convert words with underscore into camel case format.

    If the word is in camel case nothing happens.
    """
    if not name:
        return name
    return ''.join([w[0].upper() + w[1:] for w in name.strip().split('_')])


def calculate_int_bit_length_to_hold(value):
    """Calculate int length  necessary to represent given value.

    The length is adjusted to standard values 8, 16, 32, 64.

    .. todo::

    This function returns incorrect result if the value is -(1<<8) or
    similar.

    """
    if value == 0:
        return 0
    required_length = m.ceil(m.log2(abs(value)))
    if value < 0:
        required_length += 1
    for standard_length in _STANDARD_INT_LENGTHS:
        if required_length <= standard_length:
            return standard_length
    return _STANDARD_LENGTHS[-1]


def rewrite(templates_list, format_dict):
    return [t.format_map(format_dict) for t in templates_list]
