import os.path
from glob import glob
import sh
import json
from pprint import pprint

import configen.generate as cg
import configen.generator_cpp as cgc

def main():
    compile_cpp = sh.Command('/usr/bin/g++')
    filename = 'my_config'
    include_path = 'inc'
    includes = ['stdint.h', 'vector', 'string']
    test_path = '/home/leha/personal/configen/configen/test/data'
    # iterate over all files in test directory
    for test_filename in glob(os.path.join(test_path, '*.json')):
        print('Test file: ' + os.path.basename(test_filename))
        string_of_json = open(test_filename, 'r').read()
        code = cg.convert_json(string_of_json, language='c++',
                               namespace=['mycfg'], filename=filename,
                               include_path=include_path);
        # write header, source and main
        with open(os.path.join(include_path, filename + '.h'), 'w') as header:
            header.write(code['header'])
        with open(os.path.join(filename + '.cc'), 'w') as src:
            src.write(code['source'])
        with open('main.cc', 'w') as main_:
            main_.write('\n'.join([
                '#include <inc/{0}.h>'.format(filename),
                'int main() {',
                '  return 0;',
                '}']))
        compile_cpp('-I' + str(sh.pwd())[:-1], 'main.cc', filename + '.cc')
if __name__ == '__main__':
    main()
