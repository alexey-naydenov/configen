"""Functions for generation parts of code."""

import configen.utils as cu

_INDENT = '  '

_INTEGER_TYPEDEF_TEMPLATE = 'typedef {signpref}int{bitlen}_t {ns}{name};'
_NUMBER_TYPEDEF_TEMPLATE = 'typedef double {ns}{name};'
_STRING_TYPEDEF_TEMPLATE = 'typedef std::string {ns}{name};'


def to_namespace_prefix(namespace):
    if namespace is None or len(namespace) == 0:
        return ''
    else:
        return '::'.join(namespace) + '::'


def to_type_name(name):
    return [cu.to_camel_case(n) for n in name]


def make_integer_typedef(name, properties=None):
    """Create typedef string for an integer.

    Correct integer length is choosen if min and/or max are present.
    properties is a dictionary with minimum, maximum.

    .. todo::

    This function won't select the correct type if min value is
    -(1<<8) or similar.

    Examples:

    >>> make_integer_typedef('abc')
    'typedef int32_t Abc;'
    >>> make_integer_typedef('abc', {'minimum': 0})
    'typedef uint32_t Abc;'
    >>> make_integer_typedef('abc', {'maximum': 0})
    'typedef int32_t Abc;'
    >>> make_integer_typedef('abc', {'maximum': 128})
    'typedef int8_t Abc;'
    >>> make_integer_typedef('abc', {'maximum': 128, 'minimum': -129})
    'typedef int16_t Abc;'
    >>> make_integer_typedef('abc', {'maximum': 129, 'minimum': 0})
    'typedef uint8_t Abc;'

    """
    if properties is None:
        properties = {}
    if properties.get('minimum', -1) >= 0:
        sign_prefix = 'u'
    else:
        sign_prefix = ''
    bit_length = max(
        cu.calculate_int_bit_length_to_hold(properties.get('minimum', 0)),
        cu.calculate_int_bit_length_to_hold(properties.get('maximum', 0)))
    if bit_length == 0:
        bit_length = 32
    type_name = to_type_name(name)
    return _INTEGER_TYPEDEF_TEMPLATE.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]), 
        bitlen=bit_length, signpref=sign_prefix)


def make_number_typedef(name, properties=None):
    """Create typedef for a double number."""
    type_name = to_type_name(name)
    return _NUMBER_TYPEDEF_TEMPLATE.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


def make_string_typedef(name, properties=None):
    """Create typedef for a string."""
    type_name = to_type_name(name)
    return _STRING_TYPEDEF_TEMPLATE.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


TYPE_TYPDEDEF_MAKER_DICT = {'integer': make_integer_typedef,
                            'number': make_number_typedef,
                            'string': make_string_typedef}


def make_init_declaration(name):
    """Return declaration of init function.

    Examples:

    >>> make_init_declaration(['var'])
    'void InitVar(Var *val)'
    >>> make_init_declaration(['myspace', 'var'])
    'void Myspace::InitVar(Myspace::Var *val)'

    """
    type_name = to_type_name(name)
    return 'void {ns}Init{name}({ns}{name} *val)'.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


def make_validate_declaration(name):
    """Return declaration of init function.

    Examples:

    >>> make_validate_declaration(['myspace', 'var'])
    'void Myspace::ValidateVar(const Myspace::Var &val)'

    """
    type_name = to_type_name(name)
    return 'void {ns}Validate{name}(const {ns}{name} &val)'.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


def _indent(value):
    """Indent a string or all strings in the list.

    Returns list.
    """
    if not isinstance(value, list):
        return _INDENT + value
    return [_INDENT + v for v in value]


def _generate_calls_for_members(function_name, prefix, members):
    """Create list with function call for each member."""
    calls = []
    for member in members:
        type_name = to_type_name(member)
        calls.append('{ns}{fname}{tname}({prefix}val->{vname});'.format(
            fname=function_name, prefix=prefix,
            ns=to_namespace_prefix(type_name[:-1]),
            tname=type_name[-1], vname=member[-1]))
    return calls


def make_init_definition(name, properties, members=None):
    """Create definition for init function.

    .. note::
    
    The default value in properties can not be set if members is
    a nonempty list.

    Examples:

    >>> make_init_definition(['sub_module'], {'default': 1})
    ['void InitSubModule(SubModule *val) {', '  *val = 1;', '}']
    >>> make_init_definition(['sub_module'], {}, [['small_val'], ['sub_module', 'big_val']])
    ['void InitSubModule(SubModule *val) {', '  InitSmallVal(&val->small_val);', '  SubModule::InitBigVal(&val->big_val);', '}']

    """
    if members is None:
        members = []
    definition = [make_init_declaration(name) + ' {']
    if 'default' in properties:
        definition.append(
            _indent('*val = {val};'.format(val=str(properties['default']))))
    init_calls = _indent(_generate_calls_for_members('Init', '&', members))
    definition.extend(init_calls)
    definition.append('}')
    return definition

_CHECK_TEMPLATES = {'minimum': '(val >= {minimum});',
                    'maximum': '(val <= {maximum});'}

def make_validate_definition(name, properties, members=None):
    """Create definition for validate function.

    .. note::
    
    The min/max properties can not be set if members is a nonempty
    list.

    """
    if members is None:
        members = []
    definition = [make_validate_declaration(name) + ' {']
    definition.append(_indent('bool result = true;'))
    checks = _generate_calls_for_members('Validate', '', members)
    for property_key, check_template in _CHECK_TEMPLATES.items():
        if property_key in properties:
            checks.append(check_template.format_map(properties));
    definition.extend([_INDENT + 'result &= ' + c for c in checks])
    definition.append(_indent('return result;'))
    definition.append('}')
    return definition
