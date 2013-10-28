from pprint import pprint

import configen.generate as cg

def main():
    json_schema = open('configen/test/data/test_schema.json', 'r').read()
    g=cg.convert_json(json_schema, ['mycfg'], 'c++');
    #pprint(g.forward_definitions)
    print('========================================')
    print('\n'.join(g.files['header']))
    print('========================================')
    print('\n'.join(g.files['src']))

if __name__ == '__main__':
    main()
