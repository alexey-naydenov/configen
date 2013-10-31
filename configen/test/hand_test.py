import os.path
import sh
import json
from pprint import pprint

import configen.generate as cg
import configen.generator_cpp as cgc

def main():
    filename = 'my_config'
    include_path = 'inc'
    includes = ['stdint.h', 'vector', 'string']
    # json_schema = open('configen/test/data/test_schema.json', 'r').read()
    string_of_json = open(
        '/home/leha/personal/configen/configen/test/data/test_object_variables.json', 'r').read()
    g=cg.convert_json(string_of_json, language='c++', namespace=['mycfg'],
                      filename=filename, include_path=include_path);
    # write files
    with open(os.path.join(include_path, filename + '.h'), 'w') as header:
        header.write(g['header'])
    with open(os.path.join(filename + '.cc'), 'w') as src:
        src.write(g['source'])
    with open('main.cc', 'w') as main_:
        main_.write("#include <inc/my_config.h>\n"
                    "int main() {\n"
                    "  return 0;\n"
                    "}")

    # schema = {'type': 'integer', 'default': 100, 'minimum': 10, 
    #           'maximum': 1000}
    # variable_code = cgc.generate_variable(schema)
    # pprint(variable_code)
    # # print('\n'.join(cgc.generate_header(
    # #     {'intvar': variable_code}, namespace=['my_cfg'], includes=includes,
    # #     filename=filename)))
    # # print()
    # # print('\n'.join(cgc.generate_source(
    # #     {'intvar': variable_code}, namespace=['my_cfg'], filename=filename,
    # #     include_path=include_path)))
    # files = cgc.generate_files({'intvar': variable_code}, namespace=['my_cfg'],
    #                            filename=filename, include_path=include_path,
    #                            includes=includes)
    # print(files['header'])
    # print()
    # print(files['source'])

if __name__ == '__main__':
    main()
