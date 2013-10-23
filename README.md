# configen

Code generator for configuration handling.

Map JSON tree onto C++ object hierarchy.

### Features/Restrictions:

- takes schema and produce class (C++) representing it;
- the class can be initialized from JSON string that satisfy the
  schema;
- the class or its part can be serialized to JSON;
- each JSON simple type corresponds to a class member of POD type,
  internal JSON objects are represented by members of members;
- all objects can be freely copied;
- during initialization values can be verified to satisfy schema (min,
  max, etc.);
- input is parsed once no forward references.

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
  "small_val": {"$ref": "small_int"},
  "big_val": {
    "type": "number",
    "default": 1.0
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
