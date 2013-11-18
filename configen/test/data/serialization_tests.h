#include <cassert>
#include <string>

template <class T> void CheckStringSerialization() {
  T object;
  std::string serialized = object.ToString();
  assert(serialized.size() > 0);
  T deserialized;
  assert(deserialized == object);
  assert(deserialized.FromString(serialized));
  assert(deserialized.FromString(object.ToString()));
  assert(serialized == deserialized.ToString());
}
