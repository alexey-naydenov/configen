#include <cassert>
#include <vector>
#include <iostream>
#include <serialization_tests.h>
#include <inc/my_config.h>

bool was_called = false;
bool can_change = false;

bool fake_pre_update(const config::SubModule &current_value,
                     const config::SubModule &new_value) {
  was_called = true;
  return can_change;
}

int main() {
  const char json_submodule[] =
      "{\"sub_module\":{\"small_val\":100,\"big_val\":2}}";
  config::SubModule cfg;
  CheckStringSerialization<config::SubModule>();
  assert(cfg.big_val == 1);
  // change through json
  cfg.FromString(json_submodule);
  assert(cfg.big_val == 2);
  // add pre update and test
  cfg.pre_update = fake_pre_update;
  cfg.big_val = 1;
  was_called = false;
  can_change = false;
  assert(cfg.FromString(json_submodule) == false);
  assert(was_called == true);
  assert(cfg.big_val == 1);
  // allow change
  cfg.big_val = 1;
  was_called = false;
  can_change = true;
  assert(cfg.FromString(json_submodule) == true);
  assert(was_called == true);
  assert(cfg.big_val == 2);

  return 0;
}
