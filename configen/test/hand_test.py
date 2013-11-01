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
        '/home/leha/personal/configen/configen/test/data/test_object_object.json', 'r').read()
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

if __name__ == '__main__':
    main()
