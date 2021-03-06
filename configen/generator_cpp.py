from datetime import datetime
import os.path
from pprint import pprint
import configen.utils as cu
import configen.parts_cpp as cpp

_FILE_FORMAT_DICT = {'lb': '{', 'rb': '}', 'namespace': '',
                     'function_prefix': ''}

def generate_header(name_code_dict, namespace=None, includes=None, 
                    filename=None):
    header = []
    guard_parts = [filename, datetime.now().strftime('%y_%m_%d_%H_%M')]
    # headers start
    header.extend(cpp.header_guard_front(guard_parts))
    for include_file in includes:
        header.extend(cpp.include(include_file))
    header.extend(cpp.namespace_begin(namespace) + ['']
                  + cpp.json_to_string_declaration()
                  + cpp.string_to_json_declaration() + [''])
    # header typedefs and 
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
        format_dict['name'] = name
        header.extend([p.format_map(format_dict) for p in code['predefine']])
    # header declarations
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
        format_dict['name'] = name
        for template in code.get('declarations', []):
            header.append(template.format_map(format_dict))
    # header end
    header.extend(cpp.namespace_end(namespace))
    header.extend(cpp.header_guard_back(guard_parts))
    return header

def generate_source(name_code_dict, namespace=None, includes=None, 
                    filename=None, include_path=None):
    source = []
    # source start
    source.extend(cpp.include(filename + '.h', include_path))
    for include_file in includes:
        source.extend(cpp.include(include_file))
    source.extend(cpp.namespace_begin(namespace) + ['']
                  + cu.rewrite(cpp.json_to_string_definition(),
                               _FILE_FORMAT_DICT)
                  + cu.rewrite(cpp.string_to_json_definition(),
                               _FILE_FORMAT_DICT))
    # definitions
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
        format_dict['name'] = name
        format_dict['name_array'] = '"' + name + '"'
        for template in code.get('definitions', []):
            source.append(template.format_map(format_dict))
    # source end
    source.extend(cpp.namespace_end(namespace))
    return source

def generate_variable(schema):
    code_parts = {}
    code_parts['predefine'] = [('typedef ' + cpp.to_cpp_type(schema) 
                               + ' {typename};')]
    code_parts['declarations'] = ([''] + cpp.init_declaration()
                                  + cpp.validate_declaration() 
                                  + cpp.conversion_declaration())
    code_parts['definitions'] = (cpp.variable_init_definition(schema)
                                 + cpp.variable_validate_definition(schema)
                                 + cpp.variable_conversion_definition(schema))
    return code_parts

def generate_object(members):
    code_parts = {'predefine': ['struct {typename};'],
                  'declarations': 
                  (cpp.init_declaration() + cpp.validate_declaration()
                   + cpp.conversion_declaration() 
                   + ['', 'struct {typename} {lb}',
                      cpp.indent('static const std::size_t kNamesLength;'),
                      cpp.indent('static const char * const kNames[];'),
                      cpp.indent('bool (*pre_update)(const {typename} &current_value,'
                                 ' const {typename} &new_value);')]),
                  'definitions': []}
    # lists to collect code parts
    member_defines = []
    member_declarations = []
    function_declarations = []
    function_definitions = []
    member_init = [] # accumulate calls to member init functions
    member_validate = [] # accumulate calls to member validate functions
    for member_name, member_code in members.items():
        if 'typename' in member_code:
            member_type = member_code['typename'] 
        else:
            member_type = cu.to_camel_case(member_name)
        member_format_dict = {
            'name_array': '{name_array}, "' + member_name + '"',
            'namespace': '{namespace}{typename}::', 'function_prefix': 'static ', 
            'typename': member_type, 'lb': '{lb}', 'rb': '{rb}'}
        # member predefines
        member_defines.extend(cu.rewrite(member_code['predefine'],
                                         member_format_dict))
        # member variables
        member_declarations.append('{0} {1};'.format(member_type, member_name))
        # member declarations for init and validate
        function_declarations.extend(cu.rewrite(member_code['declarations'],
                                                member_format_dict))
        # member definitions for init and validate
        function_definitions.extend(cu.rewrite(member_code['definitions'],
                                               member_format_dict))
        # accumulate necessary member info to init and validate them
        calls_format_dict = {'name': member_name, 'typename': member_type,
                             'namespace': '{typename}::'}
        member_init.extend(cu.rewrite(cpp.init_call(member_code),
                                      calls_format_dict))
        member_validate.extend(cu.rewrite(cpp.validate_call(member_code),
                               calls_format_dict))
    # constructor and validate
    function_declarations.extend(
        [''] + cpp.constructor_declaration() + cpp.isvalid_declaration()
        + cpp.object_json_declarations() + cpp.object_string_declarations()
        + cpp.object_comparison_declaration())
    function_definitions.extend(
        cpp.object_init_definition(member_init)
        + cpp.object_validate_definition(member_validate, members)
        + cpp.object_conversion_definition(members) 
        + cpp.object_comparison_definition(members))
    # finalize and return
    code_parts['declarations'].extend(cpp.indent(member_defines))
    code_parts['declarations'].append('')
    code_parts['declarations'].extend(cpp.indent(function_declarations))
    code_parts['declarations'].append('')
    code_parts['declarations'].extend(cpp.indent(member_declarations))
    code_parts['declarations'].append('{rb}; // {typename}')
    code_parts['definitions'].extend(function_definitions)
    return code_parts

def generate_reference(schema):
    code_parts = {'predefine': [],
                  'declarations': [],
                  'definitions': []}
    namespace_list = [cu.to_camel_case(name) 
                      for name in  schema['$ref'].split('.')]
    code_parts['typename'] = '::'.join(namespace_list)
    if len(namespace_list) > 1:
        namespace = '::'.join(namespace_list[:-1]) + '::'
    else:
        namespace = ''
    code_parts['namespace'] = namespace
    return code_parts

def generate_array(element, schema):
    length = schema.get('maxItems', None)
    code_parts = {'declarations': [], 'definitions': []}
    # predefines
    element_typename = element.get('typename', '{typename}Element')
    element_ns = element.get('namespace', '')
    code_parts['predefine'] = cu.rewrite(element['predefine'],
                                         {'typename': element_typename})
    code_parts['predefine'].append('typedef std::vector<' + element_typename
                                   + '> {typename};')
    # copy declarations and add array declarations
    element_format_dict = {'typename': element_typename,
                           'name_array': '{name_array}',
                           'namespace': '{namespace}',
                           'function_prefix': '{function_prefix}',
                           'lb': '{lb}', 'rb': '{rb}'}
    code_parts['declarations'].extend(cu.rewrite(element['declarations'],
                                                 element_format_dict))
    code_parts['declarations'].extend([''] + cpp.init_declaration() 
                                      + cpp.validate_declaration()
                                      + cpp.conversion_declaration())
    # definitions
    code_parts['definitions'].extend(cu.rewrite(element['definitions'],
                                                element_format_dict))
    code_parts['definitions'].extend(
        cpp.array_init_definition(element_typename, length, element_ns)
        + cpp.array_validate_definition(element_typename, schema, element_ns)
        + cpp.array_conversion_definition(element_typename, schema, element_ns))
    return code_parts

_INCLUDES = ['stdint.h', 'string.h', 'stdlib.h', 'string', 'vector', 'cJSON.h']

def generate_files(name_code_dict, filename=None, namespace=None,
                   include_path=None, includes=None):
    namespace = namespace if namespace is not None else []
    filename = filename if filename is not None else 'config'
    include_path = include_path if include_path is not None else ''
    src_includes = includes if includes is not None else []
    assert isinstance(namespace, list) == True, 'Namespace must be a list.'
    header_includes = _INCLUDES
    files = {}
    files['header'] = '\n'.join(generate_header(
        name_code_dict, namespace, header_includes, filename))
    files['source'] = '\n'.join(generate_source(
        name_code_dict, namespace, src_includes, filename, include_path))
    return files

def write_files(code, filename):
    with open(filename + '.h', 'w') as header:
        header.write(code['header'])
    with open(filename + '.cc', 'w') as src:
            src.write(code['source'])
