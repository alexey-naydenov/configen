#include <cassert>
#include <inc/my_config.h>

int main() {
  config::AnInt i;
  config::InitAnInt(&i);
  assert(i == 100);
  assert(config::ValidateAnInt(i));
  i = 2000;
  assert(config::ValidateAnInt(i) == false);
  return 0;
}
