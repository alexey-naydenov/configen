"""Generic functions for generating code."""

import json

import configen.generator_cpp as cpp


_LANGUAGE_MODULE_DICT = {'c++': cpp}


def convert_json(json_schema, language, **kwargs):
    """Convert json to dict and call actual generator function."""
    return convert_schema_to_language(
        json.loads(json_schema), language, **kwargs)


def convert_schema_to_language(schema, language, **kwargs):
    """Get generators for particular language, start and end processing."""
    generator_module = _LANGUAGE_MODULE_DICT[language]
    name_code_dict = {}
    for object_name, object_schema in schema.items():
        name_code_dict[object_name] = convert_schema(generator_module, 
                                                     object_schema)
    return generator_module.generate_files(name_code_dict, **kwargs)

_SIMPLE_TYPES = ['bool', 'integer', 'number', 'string']

def convert_schema(generator_module, schema):
    """Walk schema tree calling appropriate makers for generating code.

    The code and state is stored in a dictionary. Makers is a
    dictionary with functions that are called during schema tree
    walking.

    """
    if 'type' in schema:
        if schema['type'] in _SIMPLE_TYPES:
            return generator_module.generate_variable(schema)
        if schema['type'] == 'object':
            members = {
                member_name: convert_schema(generator_module, member_schema)
                       for member_name, member_schema in schema['properties'].items()}
            return generator_module.generate_object(members)
        # unknown type
        return None

