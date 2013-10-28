import configen.utils as cu
import configen.parts_cpp as cpc


class CppGenerator:
    def __init__(self):
        self.files = {'header': [], 'src': []}
        self.namespace = []  # real namespace of config class
        self.class_space = []  # list of container classes that hold this one
        self.forward_definitions = []  # will be placed at the top of header

    def start(self, schema, namespace):
        self.namespace = namespace

    def stop(self, schema, namespace):
        print('stop')

    def add_reference(self, name, schema):
        print('ref ')

    def add_variable(self, name, schema):
        self.forward_definitions.append(
            cpc.TYPE_TYPDEDEF_MAKER_DICT[schema['type']](
                self.class_space + [name], schema))

    def add_array(self, name, schema):
        print('array ' + name)

    def start_object(self, name, schema):
        self.class_space.append(cu.to_camel_case(name))

    def end_object(self, name, schema):
        self.class_space.pop()
