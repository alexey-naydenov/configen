#include <cassert>
#include <inc/my_config.h>

int main() {
  config::AnObject cfg;
  assert(cfg.an_array.size() == 0);
  cfg.an_array.push_back(10);
  assert(cfg.an_array.size() == 1);
  assert(cfg.an_array[0] == 10);

  return 0;
}
