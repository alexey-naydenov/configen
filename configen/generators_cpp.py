def _start_generation(state, schema, namespace):
    state['files']['header'] = []
    state['files']['src'] = []
    print('start')
    return state


def _end_generation(state, schema, namespace):
    print('end')
    return state


def _add_reference(state, name, schema):
    print('ref ')
    return state


def _add_variable(state, name, schema):
    print('var ' + name)
    return state


def _start_object(state, name, schema):
    print('obj ' + name)
    return state


def _end_object(state, name, schema):
    print('end ' + name)
    return state


CPP_GENERATORS = {'start': _start_generation, 'end': _end_generation,
                  'reference': _add_reference, 'variable': _add_variable,
                  'object_start': _start_object, 'object_end': _end_object}

