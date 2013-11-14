#include <cassert>
#include <vector>
#include <iostream>
#include <inc/my_config.h>

int main() {
  config::Config cfg;

  std::vector<uint16_t> vec;
  for (int i = 0; i < 5; ++i) {
    vec.push_back(i);
  }
  std::vector<std::vector<uint16_t> > mat;
  for (int i = 0; i < 5; ++i) {
    mat.push_back(vec);
  }
  cfg.modules = mat;
  for (std::size_t i = 0; i != 5; ++i) {
    for (std::size_t j = 0; j != 5; ++j) {
      assert(cfg.modules[i][j] == j);
    } // loop j
  } // loop i
  // to json
  assert(cfg.FromString("{\"modules\":[[10,11,12,13,14],[10,11,12,13,14],"
                        "[10,11,12,13,14],[10,11,12,13,14],"
                        "[10,11,12,13,14]]}"));
  for (std::size_t i = 0; i != 5; ++i) {
    for (std::size_t j = 0; j != 5; ++j) {
      assert(cfg.modules[i][j] == 10 + j);
    } // loop j
  } // loop i
  return 0;
}
