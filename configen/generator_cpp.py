from datetime import datetime
import configen.utils as cu
import configen.parts_cpp as cpp


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
                cpp.TYPE_TYPDEDEF_MAKER_DICT[schema['type']]([name], schema))
            prefix = None
        else:
            self._to_header(
                cpp.TYPE_TYPDEDEF_MAKER_DICT[schema['type']]([name], schema))
            self._to_header(cu.to_camel_case(name) + ' ' + name + ';')
            prefix = 'static'
            self._to_members(self.class_space + [name], name)
        self._to_header('')
        self._to_header(cpp.init_declaration([name], prefix) + ';')
        self._to_header(cpp.validate_declaration([name], prefix) + ';')
        # src stuff
        self._to_src(cpp.init_definition(self.class_space + [name], schema))
        self._to_src(cpp.validate_definition(self.class_space + [name], schema))

    def add_array(self, name, schema):
        print('array ' + name)

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
