import sys
import os.path
from glob import glob
import sh
import json
from pprint import pprint

import configen.generate as cg
import configen.generator_cpp as cgc

DEFAULT_MAIN = ['#include <inc/my_config.h>',
                'int main() {',
                '  return 0;',
                '}']

def check_output(output):
    print(output.stdout.decode('utf-8'))
    if output.exit_code != 0:
        print(output.stderr.decode('utf-8'))
        sys.exit(1)

def main():
    filename = 'my_config'
    include_path = 'inc'
    test_path = '/home/leha/personal/configen/configen/test/data'
    test_files = glob(os.path.join(test_path, '*.json'))
    #test_files = [os.path.join(test_path, 'test_array_variables.json')]
    # copy header with helper test functions
    sh.cp(os.path.join(test_path, 'serialization_tests.h'), '.')
    # iterate over all files in test directory
    for test_filename in test_files:
        test_name = os.path.basename(test_filename).split('.')[0]
        print('Test file: ' + test_name)
        string_of_json = open(test_filename, 'r').read()
        code = cg.convert_json(string_of_json, language='c++',
                               namespace=['config'], filename=filename,
                               include_path=include_path);
        # write header, source and main
        with open(os.path.join(include_path, filename + '.h'), 'w') as header:
            header.write(code['header'])
        with open(os.path.join(filename + '.cc'), 'w') as src:
            src.write(code['source'])
        main_filename = os.path.join(test_path, test_name + '.cc')
        if os.path.exists(main_filename):
            sh.cp(main_filename, 'main.cc')
        else:
            print('Default main')
            with open('main.cc', 'w') as main_:
                main_.write('\n'.join(DEFAULT_MAIN))
        sh.make()
        # check c code
        run_main = sh.Command('./configen_test')
        check_output(run_main())
        # try:
        #     sh.valgrind('--error-exitcode=1', '--leak-check=yes',
        #                 '--track-origins=yes',
        #                 '--suppressions=/home/leha/valgrind.supp',
        #                 './configen_test')
        # except sh.ErrorReturnCode as e:
        #     print(e.stderr.decode('utf-8'))
        #     sys.exit(1)
            

if __name__ == '__main__':
    main()
