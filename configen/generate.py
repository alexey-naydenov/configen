"""Generic functions for generating code."""

import json

from configen.generator_cpp import CppGenerator


_LANGUAGE_GENERATORS_DICT = {'c++': CppGenerator}


def convert_json(json_schema, namespace, language, **kwargs):
    """Convert json to dict and call actual generator function."""
    return convert_schema_to_language(
        json.loads(json_schema), namespace, language, **kwargs)


def convert_schema_to_language(schema, namespace, language, **kwargs):
    """Get generators for particular language, start and end processing."""
    generator = _LANGUAGE_GENERATORS_DICT[language](**kwargs)
    generator.start(schema, namespace)
    convert_schema(generator, schema)
    generator.stop(schema, namespace)
    return generator


def convert_schema(generator, schema):
    """Walk schema tree calling appropriate makers for generating code.

    The code and state is stored in a dictionary. Makers is a
    dictionary with functions that are called during schema tree
    walking.

    """
    for variable_name, subschema in schema.items():
        if '$ref' in subschema:
            generator.add_reference(variable_name, subschema, is_array)
            continue
        if subschema['type'] == 'object':
            generator.start_object(variable_name, subschema)
            convert_schema(generator, subschema['properties'])
            generator.end_object(variable_name, subschema)
            continue
        if subschema['type'] == 'array':
            generator.start_array(variable_name, subschema)
            convert_schema(generator, {variable_name: subschema['items']})
            generator.end_array(variable_name, subschema)
            continue
        generator.add_variable(variable_name, subschema)
    return generator
