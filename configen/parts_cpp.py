"""Functions for generation parts of code."""

import os.path
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


def array_properties_to_typedef_template(array_properties):
    if array_properties is None:
        array_properties = []
    return ('typedef ' + 'std::vector<'*len(array_properties) 
            + '{existing_type}'+ '> '*len(array_properties) + ' {new_type};')


def integer_typedef(name, properties=None, array_properties=None):
    """Create typedef string for an integer.

    Correct integer length is choosen if min and/or max are present.
    properties is a dictionary with minimum, maximum.

    .. todo::

    This function won't select the correct type if min value is
    -(1<<8) or similar.

    Examples:

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
    int_type = sign_prefix + 'int' + str(bit_length) + '_t'
    template = array_properties_to_typedef_template(array_properties)
    return template.format(existing_type=int_type, 
                           new_type=to_type_name(name)[-1])


def number_typedef(name, properties=None):
    """Create typedef for a double number."""
    type_name = to_type_name(name)
    return _NUMBER_TYPEDEF_TEMPLATE.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


def string_typedef(name, properties=None):
    """Create typedef for a string."""
    type_name = to_type_name(name)
    return _STRING_TYPEDEF_TEMPLATE.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]))


TYPE_TYPDEDEF_MAKER_DICT = {'integer': integer_typedef,
                            'number': number_typedef,
                            'string': string_typedef}


def _init_declaration(name, prefix=None):
    """Return declaration of init function.

    Examples:

    >>> init_declaration(['var'])
    'void InitVar(Var *val)'
    >>> init_declaration(['myspace', 'var'])
    'void Myspace::InitVar(Myspace::Var *val)'

    """
    if prefix is None:
        prefix = ''
    else:
        prefix = prefix + ' '
    type_name = to_type_name(name)
    return ['{prefix}void {ns}Init{name}({ns}{name} *val)'.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]),
        prefix=prefix)]


def _validate_declaration(name, prefix=None):
    """Return declaration of init function.

    Examples:

    >>> validate_declaration(['myspace', 'var'])
    'bool Myspace::ValidateVar(const Myspace::Var &val)'

    """
    if prefix is None:
        prefix = ''
    else:
        prefix = prefix + ' '
    type_name = to_type_name(name)
    return '{prefix}bool {ns}Validate{name}(const {ns}{name} &val)'.format(
        name=type_name[-1], ns=to_namespace_prefix(type_name[:-1]),
        prefix=prefix)


def _constructor_declaration(name):
    type_name = to_type_name(name)
    return ['{class_name}() {{'.format(class_name=type_name[-1]),
            indent('Init{name}(this);'.format(name=type_name[-1])),
            '}']

def _isvalid_declaration(name):
    type_name = to_type_name(name)
    return ['bool IsValid() const {{'.format(class_name=type_name[-1]),
            indent('return Validate{name}(*this);'.format(name=type_name[-1])),
            '}']


def indent(value, times=1):
    """Indent a string or all strings in the list.

    Returns list.
    """
    if not isinstance(value, list):
        return _INDENT*times + value
    return [_INDENT*times + v for v in value]


def _generate_calls_for_members(function_name, prefix, members):
    """Create list with function call for each member."""
    calls = []
    for member in members:
        type_name = to_type_name(member[0])
        calls.append('{ns}{fname}{tname}({prefix}{{it}}->{vname});'.format(
            fname=function_name, prefix=prefix,
            ns=to_namespace_prefix(type_name[:-1]),
            tname=type_name[-1], vname=member[1]))
    return calls


def init_definition(name, properties, members=None, array_properties=None):
    """Create definition for init function.

    .. note::
    
    The default value in properties can not be set if members is
    a nonempty list. Only work with 1D arrays.

    Examples:

    >>> init_definition(['sub_module'], {'default': 1})
    ['void InitSubModule(SubModule *val) {', '  *val = 1;', '}']
    >>> init_definition(['sub_module'], {}, [['small_val'], ['sub_module', 'big_val']])
    ['void InitSubModule(SubModule *val) {', '  InitSmallVal(&val->small_val);', '  SubModule::InitBigVal(&val->big_val);', '}']

    """
    if members is None:
        members = []
    array_properties = array_properties if array_properties is not None else []
    definition = [init_declaration(name) + ' {']
    init_body = []
    if 'default' in properties:
        init_body.append(
            indent('*{{it}} = {val};'.format(val=str(properties['default']))))
    init_calls = indent(_generate_calls_for_members('Init', '&', members))
    init_body.extend(init_calls)
    # if array size is given then iterate
    if array_properties:
        if 'maxItems' in []:
            definition.extend([l.format(it='val') for l in init_body])
    else:
        definition.extend([l.format(it='val') for l in init_body])
    definition.append('}')
    return definition


def validate_definition(name, properties, members=None):
    """Create definition for validate function.

    .. note::
    
    The min/max properties can not be set if members is a nonempty
    list.

    """
    if members is None:
        members = []
    definition = [validate_declaration(name) + ' {']
    definition.append(indent('bool result = true;'))
    checks = _generate_calls_for_members('Validate', '', members)
    for property_key, check_template in _CHECK_TEMPLATES.items():
        if property_key in properties:
            checks.append(check_template.format_map(properties));
    definition.extend([_INDENT + 'result &= ' + c for c in checks])
    definition.append(indent('return result;'))
    definition.append('}')
    return definition


def namespace_begin(namespace):
    return ['namespace {0} {{'.format(n) for n in namespace]


def namespace_end(namespace):
    return ['}} // namespace {0}'.format(n) for n in namespace]


def class_definition(name, namespace):
    return 'struct {ns}{cn};'.format(cn=cu.to_camel_case(name),
                                     ns=to_namespace_prefix(namespace))


def class_begin(name):
    return 'struct {0} {{'.format(cu.to_camel_case(name))


def class_end(name):
    return '}}; // struct {0}'.format(cu.to_camel_case(name))


def _name_to_guard(name):
    return '_'.join(name).upper()


def header_guard_front(name):
    guard = _name_to_guard(name)
    return ['#ifndef {0}'.format(guard),
            '#define {0}'.format(guard)]


def header_guard_back(name):
    guard = _name_to_guard(name)
    return ['#endif // {0}'.format(guard)]


def include(filename, path=None):
    path = path if path else ''
    return ['#include <{0}>'.format(os.path.join(path, filename))]

# refactoring stuff

_SCHEMA_TO_CPP_TYPE_DICT = {'bool': 'bool', 'number': 'double',
                            'string': 'std::string'}

def to_cpp_type(schema):
    """Convert schema type name to cpp type."""
    typename = schema['type']
    if typename in _SCHEMA_TO_CPP_TYPE_DICT:
        return _SCHEMA_TO_CPP_TYPE_DICT[typename]
    if typename == 'integer':
        if schema.get('minimum', -1) >= 0:
            sign_prefix = 'u'
        else:
            sign_prefix = ''
        bit_length = max(
            cu.calculate_int_bit_length_to_hold(schema.get('minimum', 0)),
            cu.calculate_int_bit_length_to_hold(schema.get('maximum', 0)))
        if bit_length == 0:
            bit_length = 32
        return sign_prefix + 'int' + str(bit_length) + '_t'
    assert False, 'Type "' + str(typename) + '" is not a simple type'

# ==================== init ====================

def init_declaration():
    return ['{function_prefix}void Init{typename}({typename} *value);']


def variable_init_definition(schema):
    definition = [
        'void {namespace}Init{typename}({namespace}{typename} *value) {lb}']
    if 'default' in schema:
        default = schema['default']
        default_as_string = str(default)
        if isinstance(default, bool):
            default_as_string = default_as_string.lower()
        if isinstance(default, str):
            default_as_string = '"' + default_as_string + '"'
        definition.append(
            indent('*value = {0};'.format(default_as_string)))
    definition.append('{rb}')
    return definition

# ==================== validate ====================

def validate_declaration():
    return ['{function_prefix}bool Validate{typename}(const {typename} &value);',
            '{function_prefix}bool Validate{typename}(const cJSON *node);']

_CHECK_TEMPLATES = {'minimum': '(value >= {minimum});',
                    'maximum': '(value <= {maximum});'}

_TYPE_CHECK_DICT = {
    'bool': 'node->type == cJSON_False || node->type == cJSON_True', 
    'integer': 'node->type == cJSON_Number', 
    'number': 'node->type == cJSON_Number',
    'string': 'node->type == cJSON_String',
    'object': 'node->type == cJSON_Object',
    'array': 'node->type == cJSON_Array'}

_TYPE_VALUE_FIELD_DICT = {
    'bool': 'node->type == cJSON_True ? true : false', 
    'integer': 'node->valueint', 
    'number': 'node->valuedouble',
    'string': 'node->valuestring'}

def _json_type_check(schema):
    """Generate code that checks for correct json type."""
    return ['if (!(' + _TYPE_CHECK_DICT[schema['type']] + ')) return false;']

def _json_extract_value(schema):
    """Generate code that copies json value into a variable."""
    return ['{typename} value = ' + _TYPE_VALUE_FIELD_DICT[schema['type']]+ ';']

def _variable_validate_value(schema):
    definition = [
        'bool {namespace}Validate{typename}(const {namespace}{typename} &value) {lb}']
    body = ['bool result = true;']
    checks = []
    for property_key, check_template in _CHECK_TEMPLATES.items():
        if property_key in schema:
            checks.append(check_template.format_map(schema));
    body.extend(['result &= ' + c for c in checks])
    body.append('return result;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _variable_validate_json(schema):
    definition = [
        'bool {namespace}Validate{typename}(const cJSON *node) {lb}']
    body = ['bool result = true;'] + _json_type_check(schema) \
           + _json_extract_value(schema)
    checks = []
    for property_key, check_template in _CHECK_TEMPLATES.items():
        if property_key in schema:
            checks.append(check_template.format_map(schema));
    body.extend(['result &= ' + c for c in checks])
    body.append('return result;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def variable_validate_definition(schema):
    return _variable_validate_value(schema) + _variable_validate_json(schema)

# ==================== conversion ====================

def conversion_declaration():
    return ['{function_prefix}bool {typename}ToJson(const {typename} &value, cJSON **node);',
            '{function_prefix}bool JsonTo{typename}(const cJSON *node, {typename} *value);']

_TYPE_NODE_CREATE_DICT = {
    'bool': 'cJSON_CreateBool(value)', 
    'integer': 'cJSON_CreateNumber(value)', 
    'number': 'cJSON_CreateNumber(value)',
    'string': 'cJSON_CreateString(value.c_str())'}

def _value_json_conversion(schema):
    definition = [('bool {namespace}{typename}ToJson('
                   'const {namespace}{typename} &value, cJSON **node) {lb}')]
    body = ['cJSON *new_node = ' + _TYPE_NODE_CREATE_DICT[schema['type']] + ';',
            '*node = new_node;',
            'return true;']
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _json_value_conversion(schema):
    definition = [('bool {namespace}JsonTo{typename}('
                   'const cJSON *node, {namespace}{typename} *value) {lb}')]
    body = _json_type_check(schema)
    body.append('*value = ' + _TYPE_VALUE_FIELD_DICT[schema['type']] + ';')
    body.append('return true;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def variable_conversion_definition(schema):
    return _value_json_conversion(schema) + _json_value_conversion(schema)

# ==================== object ====================

def constructor_declaration():
    return ['{typename}() {lb}',
            indent('Init{typename}(this);'),
            '{rb}']

def object_comparison_declaration():
    return ['bool operator==(const {typename} &other) const;',
            'bool operator!=(const {typename} &other) const {lb}',
            indent('return !(*this == other);'),
            '{rb}']

def isvalid_declaration():
    return ['bool IsValid() const {lb}',
            indent('return Validate{typename}(*this);'),
            '{rb}']

def object_json_declarations():
    return ['static bool IsJsonValid(const cJSON *node) {lb}',
            indent('return Validate{typename}(node);'),
            '{rb}',
            'cJSON *ToJson() const {lb}',
            indent('cJSON *child;'),
            indent('{typename}ToJson(*this, &child);'),
            indent('cJSON *parent;'),
            indent('for (int i = kNamesLength - 1; i != -1; --i) {lb}'),
            indent('parent = cJSON_CreateObject();', 2),
            indent('cJSON_AddItemToObject(parent, kNames[i], child);', 2),
            indent('child = parent;', 2),
            indent('{rb}'),
            indent('return parent;'),
            '{rb}',
            'bool FromJson(const cJSON *node) {lb}',
            indent('return JsonTo{typename}(node, this);'),
            '{rb}']

def object_string_declarations():
    return ['std::string ToString() const {lb}',
            indent('return JsonToString(ToJson());'),
            '{rb}',
            'bool FromString(const std::string &serialized, bool validate = true) {lb}',
            indent('cJSON *node = StringToJson(serialized);'),
            indent('if (node == NULL) return false;'),
            indent('if (validate && !IsJsonValid(node)) {lb}'),
            indent('cJSON_Delete(node);', 2),
            indent('return false;', 2),
            indent('{rb}'),
            indent('bool rc = FromJson(node);'),
            indent('cJSON_Delete(node);'),
            indent('return rc;'),
            '{rb}']

def init_call(variable_code):
    return ['{namespace}Init{typename}(&value->{{name}});'.format(
        namespace = variable_code.get('namespace', '{namespace}'),
        typename = variable_code.get('typename', '{typename}'))]

def validate_call(variable_code):
    return ['result &= {namespace}Validate{typename}(value.{{name}});'.format(
        namespace = variable_code.get('namespace', '{namespace}'),
        typename = variable_code.get('typename', '{typename}'))]

def object_init_definition(member_calls):
    definition = [
        'const char * const {namespace}{typename}::kNames[] = {lb}{name_array}{rb};',
        'const std::size_t {namespace}{typename}::kNamesLength = sizeof({namespace}{typename}::kNames)/sizeof({namespace}{typename}::kNames[0]);',
        'void {namespace}Init{typename}({namespace}{typename} *value) {lb}']
    body = []
    for member_call in member_calls:
        body.append(member_call)
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _object_validate_value(member_calls):
    definition = [
        'bool {namespace}Validate{typename}(const {namespace}{typename} &value) {lb}']
    body = ['bool result = true;']
    for member_call in member_calls:
        body.append(member_call)
    body.append('return result;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _object_validate_json(children):
    definition = [
        'bool {namespace}Validate{typename}(const cJSON *node) {lb}']
    body = ['bool result = true;'] + _json_type_check({'type': 'object'})
    # check each element
    body.append(
        'for (cJSON *child = node->child; child; child = child->next) {lb}')
    checks = []
    for child_name, child_code in children.items():
        child_type = child_code.get('typename', cu.to_camel_case(child_name))
        child_namespace = child_code.get('namespace', '{typename}::')
        checks.append(
            'if (strcmp(child->string, "{0}") == 0) {{lb}}'.format(child_name))
        checks.append(indent(
            'result &= {namespace}Validate{typename}(child);'.format(
                typename=child_type, namespace=child_namespace)))
        checks.append(indent('continue;'))
        checks.append('{rb}')
    body.extend(indent(checks))
    body.append('{rb}')
    body.append('return result;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def object_validate_definition(member_calls, children):
    return _object_validate_value(member_calls) \
        + _object_validate_json(children)

def _object_json_conversion(children):
    definition = [('bool {namespace}{typename}ToJson('
                   'const {namespace}{typename} &value, cJSON **node) {lb}')]
    body = ['cJSON *new_node = cJSON_CreateObject();',
            'if (new_node == NULL) return false;',
            'bool rc;',
            'cJSON *child;']
    for child_name, child_code in children.items():
        child_type = child_code.get('typename', cu.to_camel_case(child_name))
        child_namespace = child_code.get('namespace', '{typename}::')
        body.extend([
            'child = NULL;',
            'rc = {namespace}{typename}ToJson(value.{name}, &child);'.format(
                name=child_name, namespace=child_namespace,
                typename=child_type),
            'if (!rc || child == NULL) return false;',
            'cJSON_AddItemToObject(new_node, "{0}", child);'.format(child_name)])
    body.extend(['*node = new_node;', 'return true;'])
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _json_object_conversion(children):
    definition = [('bool {namespace}JsonTo{typename}('
                   'const cJSON *node, {namespace}{typename} *value) {lb}')]
    body = _json_type_check({'type': 'object'})
    body.append(
        'for (cJSON *child = node->child; child; child = child->next) {lb}')
    conversions = []
    for child_name, child_code in children.items():
        child_type = child_code.get('typename', cu.to_camel_case(child_name))
        child_namespace = child_code.get('namespace', '{typename}::')
        conversions.append(
            'if (strcmp(child->string, "{0}") == 0) {{lb}}'.format(child_name))
        conversions.append(indent(
            '{namespace}JsonTo{typename}(child, &(value->{name}));'.format(
                name=child_name, typename=child_type,
                namespace=child_namespace)))
        conversions.append(indent('continue;'))
        conversions.append('{rb}')
    body.extend(indent(conversions))
    body.append('{rb}')
    body.append('return true;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def object_conversion_definition(members):
    return _object_json_conversion(members) + _json_object_conversion(members)

def array_init_definition(typename, length=None, element_ns=None):
    element_ns = element_ns if element_ns is not None else ''
    definition = [
        'void {namespace}Init{typename}({namespace}{typename} *value) {lb}']
    if length is not None:
        body = []
        body.extend(['value->resize({0});'.format(length),
                     ('for (int i = 0; i != {length}; ++i) '
                      '{namespace}Init{typename}(&(*value)[i]);').format(
                          length=length, typename=typename,
                          namespace=element_ns)])
        definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _array_validate_value(typename, element_ns):
    definition = [
        'bool {namespace}Validate{typename}(const {namespace}{typename} &value) {lb}']
    body = ['bool result = true;',
            'for (int i = 0; i != value.size(); ++i) {lb}',
            indent('result &= {namespace}Validate{typename}(value[i]);'.format(
                typename=typename, namespace=element_ns)),
            '{rb}',
            'return result;']
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _array_validate_json(typename, schema, element_ns):
    definition = [
        'bool {namespace}Validate{typename}(const cJSON *node) {lb}']
    # check type and length
    body = ['bool result = true;'] + _json_type_check(schema)
    body.append('unsigned array_length = cJSON_GetArraySize(const_cast<cJSON *>(node));')
    if 'minItems' in schema:
        body.append('if (array_length < ' + str(schema['minItems']) + ') return false;')
    if 'maxItems' in schema:
        body.append('if (array_length > ' + str(schema['maxItems']) + ') return false;')
    # check each element
    body.extend([
        'cJSON *child = node->child;',
        'while (child) {lb}',
        indent('result &= {namespace}Validate{typename}(child);'.format(
            typename=typename, namespace=element_ns)),
        indent('child = child->next;'),
        '{rb}'])
    # finalize
    body.append('return result;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def array_validate_definition(typename, schema, element_ns=None):
    element_ns = element_ns if element_ns is not None else ''
    return _array_validate_value(typename, element_ns) \
        + _array_validate_json(typename, schema, element_ns)

def _array_json_conversion(element_typename, schema, element_ns):
    definition = [('bool {namespace}{typename}ToJson('
                   'const {namespace}{typename} &value, cJSON **node) {lb}')]
    body = ['cJSON *new_node = cJSON_CreateArray();',
            'if (new_node == NULL) return false;',
            'for (unsigned i = 0; i != value.size(); ++i) {lb}',
            indent('cJSON *item;'),
            indent('if (!{namespace}{typename}ToJson(value[i], &item)) '
                   'return false;').format(namespace=element_ns,
                                           typename=element_typename),
            indent('cJSON_AddItemToArray(new_node, item);'),
            '{rb}']
    body.extend(['*node = new_node;', 'return true;'])
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def _json_array_conversion(element_typename, schema, element_ns):
    definition = [('bool {namespace}JsonTo{typename}('
                   'const cJSON *node, {namespace}{typename} *value) {lb}')]
    body = _json_type_check(schema)
    body.extend([
        'value->resize(cJSON_GetArraySize(const_cast<cJSON *>(node)));',
        'cJSON *child = node->child;',
        'for (unsigned i = 0; i != value->size(); ++i) {lb}',
        indent('{namespace}JsonTo{typename}(child, &(*value)[i]);'.format(
            typename=element_typename, namespace=element_ns)),
        indent('child = child->next;'),
        '{rb}'])
    body.append('return true;')
    definition.extend(indent(body))
    definition.append('{rb}')
    return definition

def array_conversion_definition(element_typename, schema, element_ns=None):
    element_ns = element_ns if element_ns is not None else ''
    return _array_json_conversion(element_typename, schema, element_ns) \
        + _json_array_conversion(element_typename, schema, element_ns)

def json_to_string_declaration():
    """Generate function that convert json node to string and cleans up."""
    return ['std::string JsonToString(cJSON *node);']

def json_to_string_definition():
     return ['std::string JsonToString(cJSON *node) {lb}',
            indent('std::string serialized;'),
            indent('if (node == NULL) return serialized;'),
            indent('char *json_string = cJSON_PrintUnformatted(node);'),
            indent('if (json_string == NULL) {lb}'),
            indent('cJSON_Delete(node);', 2),
            indent('return serialized;', 2),
            indent('{rb}'),
            indent('serialized = json_string;'),
            indent('free(json_string);'),
            indent('cJSON_Delete(node);'),
            indent('return serialized;'),
            '{rb}']
def string_to_json_declaration():
    """Generate function that convert a string to a json node which must be deleted."""
    return ['cJSON *StringToJson(const std::string &serialized);']

def string_to_json_definition():
    return ['cJSON *StringToJson(const std::string &serialized) {lb}',
            indent('cJSON *node = cJSON_Parse(serialized.c_str());'),
            indent('return node;'),
            '{rb}']
