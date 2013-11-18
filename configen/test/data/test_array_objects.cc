#include <cassert>
#include <vector>
#include <iostream>
#include <inc/my_config.h>

int main() {
  config::AnObject cfg;

  for (int i = 0; i < 5; ++i) {
    config::AnObject::AnArrayElement element;
    cfg.an_array.push_back(element);
  }
  for (int i = 0; i < cfg.an_array.size(); ++i) {
    cfg.an_array[i].number = i;
  }
  for (int i = 0; i < cfg.an_array.size(); ++i) {
    assert(cfg.an_array[i].an_int == 100);
    assert(cfg.an_array[i].number == i);
  }
  //std::cout << cfg.ToString() << std::endl;
  config::AnObject cfg2;
  assert(cfg2.FromString(
      "{\"an_object\":{\"an_array\":[{\"number\":0,\"an_int\":100},"
      "{\"number\":0,\"an_int\":100},{\"number\":0,\"an_int\":100},"
      "{\"number\":0,\"an_int\":100},{\"number\":0,\"an_int\":100}]}}"));
  config::AnObject cfg3;
  assert(cfg3.FromString(cfg.ToString()));
  for (int i = 0; i < cfg3.an_array.size(); ++i) {
    assert(cfg3.an_array[i].an_int == 100);
    assert(cfg3.an_array[i].number == i);
  }
  return 0;
}
