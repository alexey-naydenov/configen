"""Generic functions for generating code."""

import json

from  configen.generators_cpp import CPP_GENERATORS


_LANGUAGE_GENERATORS_DICT = {'c++': CPP_GENERATORS}


def convert_json(json_schema, namespace, language):
    """Convert json to dict and call actual generator function."""
    return convert_schema_to_language(
        json.loads(json_schema), namespace, language)


def convert_schema_to_language(schema, namespace, language):
    """Get generators for particular language, start and end processing."""
    generators = _LANGUAGE_GENERATORS_DICT[language]
    state = {'namespace': namespace, 'files': {}}
    state = generators['start'](state, schema, namespace)
    state = convert_schema(state, schema, generators)
    state = generators['end'](state, schema, namespace)
    return state


def convert_schema(state, schema, generators):
    """Walk schema tree calling appropriate makers for generating code.

    The code and state is stored in a dictionary. Makers is a
    dictionary with functions that are called during schema tree
    walking.

    """
    for variable_name, subschema in schema.items():
        if '$ref' in subschema:
            state = generators['reference'](state, variable_name, subschema)
            continue
        if subschema['type'] == 'object':
            state = generators['object_start'](state, variable_name, subschema)
            state = convert_schema(state, subschema['properties'], generators)
            state = generators['object_end'](state, variable_name, subschema)
        else:
            state = generators['variable'](state, variable_name, subschema)
    return state
    

