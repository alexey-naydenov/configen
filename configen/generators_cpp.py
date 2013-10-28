import configen.utils as cu
import configen.parts_cpp as cpc


class CppGenerator:
    def __init__(self):
        self.files = {'header': [], 'src': []}
        self.namespace = []  # real namespace of config class
        self.class_space = []  # list of container classes that hold this one
        self.forward_definitions = []  # will be placed at the top of header
        self.header = [] # header without forward definitions
        self.src = [] # will be dumped into source file
        self.current_indent = 0

    def _to_line_list(self, line_list, new_lines):
        indented_lines = cpc.indent(new_lines, times=self.current_indent)
        if isinstance(indented_lines, list):
            line_list.extend(indented_lines)
        else:
            line_list.append(indented_lines)
    
    def _to_header(self, new_lines):
        self._to_line_list(self.header, new_lines)

    def _to_src(self, new_lines):
        self._to_line_list(self.src, new_lines)

    def _to_forward_definitions(self, new_lines):
        self._to_line_list(self.forward_definitions, new_lines)

    def start(self, schema, namespace):
        self.namespace = namespace
        # header
        self.files['header'].extend(cpc.make_namespace_begin(self.namespace))
        # src
        self.files['src'].extend(cpc.make_namespace_begin(self.namespace))

    def stop(self, schema, namespace):
        # header
        self.files['header'].extend(self.forward_definitions)
        self.files['header'].extend(self.header)
        self.files['header'].extend(cpc.make_namespace_end(self.namespace))
        # src
        self.files['src'].extend(self.src)
        self.files['src'].extend(cpc.make_namespace_end(self.namespace))

    def add_reference(self, name, schema):
        print('ref ')

    def add_variable(self, name, schema):
        if not self.class_space:
            self._to_forward_definitions(
                cpc.TYPE_TYPDEDEF_MAKER_DICT[schema['type']]([name], schema))
            prefix = None
        else:
            self._to_header(
                cpc.TYPE_TYPDEDEF_MAKER_DICT[schema['type']]([name], schema))
            self._to_header(cu.to_camel_case(name) + ' ' + name + ';')
            prefix = 'static'
        self._to_header('')
        self._to_header(cpc.make_init_declaration([name], prefix) + ';')
        self._to_header(cpc.make_validate_declaration([name], prefix) + ';')

    def add_array(self, name, schema):
        print('array ' + name)

    def start_object(self, name, schema):
        # start class in header
        self._to_forward_definitions(
            cpc.make_class_definition(name, self.class_space))
        self._to_header('')
        self._to_header(cpc.make_class_begin(name))
        # enter scope
        self.current_indent += 1
        self.class_space.append(cu.to_camel_case(name))

    def end_object(self, name, schema):
        # header class body
        self._to_header('')
        self._to_header(cpc.make_init_declaration([name], 'static') + ';')
        self._to_header(cpc.make_validate_declaration([name], 'static') + ';')
        self._to_header(cpc.make_constructor_declaration([name]))
        self._to_header(cpc.make_isvalid_declaration([name]))
        # exti scope
        self.class_space.pop()
        self.current_indent -= 1
        self._to_header(cpc.make_class_end(name))
