#include <cassert>
#include <inc/my_config.h>

int main() {
  config::AnObject cfg;
  assert(cfg.an_int == 100);
  assert(cfg.a_number == 123.123);
  cfg.an_int = 123;
  assert(cfg.an_int == 123);
  return 0;
}
