from datetime import datetime
import configen.utils as cu
import configen.parts_cpp as cpp
from pprint import pprint


class CppGenerator:
    def __init__(self, filename=None, location=None, includes=None):
        self.files = {'header': [], 'src': []}
        self.namespace = []  # namespace of top level config objects
        self.class_space = []  # list of container classes that hold current one
        self.forward_definitions = []  # will be placed at the top of header
        self.header = [] # header without forward definitions
        self.src = [] # will be dumped into source file
        self.current_indent = 0
        self.members_lists = []
        self.filename = filename if filename else 'config'
        self.location = location
        self.includes = includes if includes else []
        self.guard = [self.filename, datetime.now().strftime('%y_%m_%d_%H_%M')]
        self.array_properties = []
            

    def _to_line_list(self, line_list, new_lines):
        if isinstance(new_lines, list):
            line_list.extend(new_lines)
        else:
            line_list.append(new_lines)
    
    def _to_header(self, new_lines):
        new_lines = cpp.indent(new_lines, times=self.current_indent)
        self._to_line_list(self.header, new_lines)

    def _to_src(self, new_lines):
        self._to_line_list(self.src, new_lines)

    def _to_forward_definitions(self, new_lines):
        new_lines = cpp.indent(new_lines, times=self.current_indent)
        self._to_line_list(self.forward_definitions, new_lines)

    def _to_members(self, type_, name):
        if not self.members_lists:
            return
        self.members_lists[-1].append([type_, name])

    def start(self, schema, namespace):
        self.namespace = namespace
        # header
        self.files['header'].extend(cpp.header_guard_front(self.guard))
        for include_file in self.includes:
            self.files['header'].extend(cpp.include(include_file))
        self.files['header'].extend(cpp.namespace_begin(self.namespace))
        # src
        self.files['src'].extend(cpp.include(self.filename + '.h', 
                                             self.location))
        self.files['src'].extend(cpp.namespace_begin(self.namespace))

    def stop(self, schema, namespace):
        # header
        self.files['header'].extend(self.forward_definitions)
        self.files['header'].extend(self.header)
        self.files['header'].extend(cpp.namespace_end(self.namespace))
        self.files['header'].extend(cpp.header_guard_back(self.guard))
        # src
        self.files['src'].extend(self.src)
        self.files['src'].extend(cpp.namespace_end(self.namespace))

    def add_reference(self, name, schema):
        namespace = schema['$ref'].split('.')
        self._to_members(namespace, name)

    def add_variable(self, name, schema):
        # header stuff
        if not self.class_space:
            self._to_forward_definitions(
                cpp.TYPE_TYPDEDEF_MAKER_DICT[schema['type']](
                    [name], schema, self.array_properties))
            prefix = None
        else:
            self._to_header(
                cpp.TYPE_TYPDEDEF_MAKER_DICT[schema['type']](
                    [name], schema, self.array_properties))
            self._to_header(cu.to_camel_case(name) + ' ' + name + ';')
            prefix = 'static'
            self._to_members(self.class_space + [name], name)
        self._to_header('')
        self._to_header(cpp.init_declaration([name], prefix) + ';')
        self._to_header(cpp.validate_declaration([name], prefix) + ';')
        # src stuff
        self._to_src(cpp.init_definition(
            self.class_space + [name], schema, 
            array_properties = self.array_properties))
        self._to_src(cpp.validate_definition(self.class_space + [name], schema))

    def start_object(self, name, schema):
        # add class to higher up class member list
        if self.class_space:
            self._to_members(self.class_space + [name], name)
        # add self init and validate functions to higher up
        if self.class_space:
            prefix = 'static'
        else:
            prefix = None
        self._to_header('')
        self._to_header(cpp.init_declaration([name], prefix) + ';')
        self._to_header(cpp.validate_declaration([name], prefix) + ';')
        # start class in header
        self._to_forward_definitions(
            cpp.class_definition(name, self.class_space))
        self._to_header('')
        self._to_header(cpp.class_begin(name))
        # enter scope
        self.current_indent += 1
        self.class_space.append(name)
        self.members_lists.append([])

    def end_object(self, name, schema):
        # header class body
        self._to_header('')
        self._to_header(cpp.constructor_declaration([name]))
        self._to_header(cpp.isvalid_declaration([name]))
        # src class stuff
        members = self.members_lists[-1]
        self._to_src(cpp.init_definition(self.class_space, {}, members))
        self._to_src(cpp.validate_definition(self.class_space, {}, members))
        # exit scope
        self.class_space.pop()
        self.current_indent -= 1
        self._to_header(cpp.class_end(name))
        self.members_lists.pop()
        # add variable to holding class if it exists
        if self.class_space:
            self._to_header(cu.to_camel_case(name) + ' ' + name + ';')

    def start_array(self, name, schema):
        """Store array info on stack so that later vector is created.

        Stack like structure is required to handle array of arrays.
        It is not implemented but maxItems is used to set vector size
        during init, minItems and maxItems are used during validation.

        """
        array_properties = {k: v for k, v in schema.items() 
                            if k in ['minItems', 'maxItems']}
        self.array_properties.append(array_properties)

    def end_array(self, name, schema):
        """Remove one array description from the stack."""
        self.array_properties.pop()

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
    header.extend(cpp.namespace_begin(namespace))
    # header typedefs and 
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
        header.extend([p.format_map(format_dict) for p in code['predefine']])
    # header declarations
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
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
    for include_file in includes:
        source.extend(cpp.include(include_file))
    source.extend(cpp.include(filename + '.h', include_path))
    source.extend(cpp.namespace_begin(namespace))
    # definitions
    for name, code in name_code_dict.items():
        format_dict = {}
        format_dict.update(_FILE_FORMAT_DICT)
        format_dict['typename'] = cu.to_camel_case(name)
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
                  'declarations': (cpp.init_declaration() 
                                   + cpp.validate_declaration()
                                   + [''] + ['struct {typename} {lb}']),
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
            'namespace': '{namespace}{typename}::', 'function_prefix': 'static ', 
            'typename': member_type, 'lb': '{lb}', 'rb': '{rb}'}
        # member predefines
        member_defines.extend([p.format_map(member_format_dict) 
                               for p in member_code['predefine']])
        # member variables
        member_declarations.append('{0} {1};'.format(member_type, member_name))
        # member declarations for init and validate
        function_declarations.extend(
            [member_declaration.format_map(member_format_dict)
             for member_declaration in member_code['declarations']])
        # member definitions for init and validate
        function_definitions.extend(
            [member_definition.format_map(member_format_dict)
             for member_definition in member_code['definitions']])
        # accumulate necessary member info to init and validate them
        calls_format_dict = {'name': member_name, 'typename': member_type,
                             'namespace': '{typename}::'}
        member_init.extend(cu.rewrite(cpp.init_call(member_code),
                                      calls_format_dict))
        member_validate.extend(cu.rewrite(cpp.validate_call(member_code),
                               calls_format_dict))
    # constructor and validate
    function_declarations.extend(
        [''] + cpp.constructor_declaration() + cpp.isvalid_declaration())
    function_definitions.extend(cpp.object_init_definition(member_init))
    function_definitions.extend(cpp.object_validate_definition(member_validate))
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
        cpp.array_init_definition(element_typename, length, element_ns))
    code_parts['definitions'].extend(
        cpp.array_validate_definition(element_typename, schema, element_ns))
    return code_parts

_INCLUDES = ['stdint.h', 'string', 'vector', 'cJSON.h']

def generate_files(name_code_dict, filename=None, namespace=None,
                   include_path=None):
    namespace = namespace if namespace is not None else []
    filename = filename if filename is not None else 'config'
    include_path = include_path if include_path is not None else ''
    assert isinstance(namespace, list) == True, 'Namespace must be a list.'
    includes = _INCLUDES
    files = {}
    files['header'] = '\n'.join(generate_header(
        name_code_dict, namespace, includes, filename))
    files['source'] = '\n'.join(generate_source(
        name_code_dict, namespace, [], filename, include_path))
    return files
