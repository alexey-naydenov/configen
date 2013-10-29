import os.path
import sh
from pprint import pprint

import configen.generate as cg

def main():
    filename = 'my_config'
    include_path = 'inc'
    # json_schema = open('configen/test/data/test_schema.json', 'r').read()
    json_schema = open('test_schema.json', 'r').read()
    g=cg.convert_json(json_schema, ['mycfg'], 'c++', filename=filename,
                      location=include_path, includes = ['stdint.h', 'vector']);
    # write files
    with open(os.path.join(include_path, filename + '.h'), 'w') as header:
        header.write('\n'.join(g.files['header']))
    with open(os.path.join(filename + '.cc'), 'w') as src:
        src.write('\n'.join(g.files['src']))
    with open('main.cc', 'w') as main_:
        main_.write("#include <inc/my_config.h>\n"
                    "int main() {\n"
                    "  return 0;\n"
                    "}")

if __name__ == '__main__':
    main()
