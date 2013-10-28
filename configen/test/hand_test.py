from pprint import pprint

import configen.generate as cg

def main():
    json_schema = open('configen/test/data/test_schema.json', 'r').read()
    g=cg.convert_json(json_schema, [], 'c++');
    pprint(g.forward_definitions)

if __name__ == '__main__':
    main()
