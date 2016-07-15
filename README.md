# configen

Converts configuration description into class definitions that support
serialization/deserialization from/into JSON and validation.

The project was started because there was a need to read/write JSON
configs. There are a few c++ JSON libraries but they usually give
access only to simple primitives. So in order to read some complex
configuration one has to write tree traversal functions by hand. This
utility takes config description in JSON (config schema) and produce
classes that correspond to entities in JSON. It has the following
features:

- JSON names converted into class and member names;
- c++ objects receive functions for serialization and deserialization;
- objects can be checked against rules from schema (min, max, array length, etc.);
- constructors initialize values to defaults from schema;
- uses c++98, no exceptions, uses cJSON library.

Schema examples can be found in configen/test/data.

### Implementations details:

- for each encountered object a class is created;
- arrays are mapped to vectors;
- if object is inside an object a subclass is created;
- for each reference to an object or an internal object a member is
  created;
- name of classes is camel cased version of JSON object name;
- name of members are the same as names of JSON objects;
- if min/max is not specified then integer type represented by int, if
  min and max are present smallest int is chosen;
- list with current scope, used to properly define source code;
- dict for scope accessible names, JSON name -> c++ scoped type;
- source file is just a dump where source code is added as parsing
  process;
- declaration lists for header: subclasses, variables, methods,
  functions, member init satements, member verify satements;
- full class declaration is assembled at the end of JSON object
  definition;
- declarations of non-member functions are inserted after class
  declaration;
- parent class takes full declaration of subclass and inserts into its
  declaration verbatim;
  

## Sample JSON schemes and what they should produce

### Simple variable:
```json
"small_int": {
  "type": "integer",
  "default": 100,
  "minimum": 10,
  "maximum": 1000
}
```
Header:
```c++
typedef uint16_t SmallInt;
void InitSmallInt(SmallInt *val);
bool ValidateSmallInt(const SmallInt &val);
```
Source:
```c++
void InitSmallInt(SmallInt *val) {*val = 100;}
bool ValidateSmallInt(const SmallInt &val) {
  return val >= 10 && val <= 1000;
} 
```

### Object that contains simple variables:
```json
"sub_module": {
  "type": "object",
  "properties": {
    "small_val": {"$ref": "small_int"},
    "big_val": {
      "type": "number",
      "default": 1.0
    }
  }
}
```
Header:
```c++
class SubModule {
 public:
  typedef double BigVal;
  inline void InitBigVal(BigVal *val);
  inline bool ValidateBigVal(const BigVal &val);

  SmallInt small_val;
  BigVal big_val;

  SubModule();
  bool IsValid();
};

void InitSubModule(SubModule *val);
bool ValidateSubModule(cosnt SubModule &val);
```
Source:
```c++
void SubModule::InitBigVal(SubModule::BigVal *val) {val = 1.0;}
bool SubModule::ValidateBigVal(const SubModule::BigVal &val) {return true;}

SubModule::SubModule() {
  InitSubModule(this);
}
bool SubModule::IsValid() {
  ValidateSubModule(*this);
}

void InitSubModule(SubModule *val) {
  InitSmallInt(&val->small_val);
  SubModule::InitBigVal(&val->big_val);
}
bool ValidateSubModule(cosnt SubModule &val) {
  ValidateSmallInt(val->small_val);
  SubModule::ValidateBigVal(val->big_val);
}
```

### Array of objects

```json
"config": {
  "modules": {
    "type": "array",
	"items": {"$ref": "sub_module"}	
  }
}
```

Header:
```c++
class Config {
 public:
  std::vector<SubModule> modules;
};
void InitModule(Module *val);
bool ValidateModule(const Module &val);
```

Source:
```c++
void InitModule(Module *val) {
  // vector is empty nothing to init, will be different if length is given
}
bool VerifyModule(const Module &val) {
  for (std::vector<SubModule> it = val->submodules.begin();
       it != val->submodules.end(); ++it) {
	if (!VerifySubModule(*it)) {
	  return false;
	}
  }
}
```
