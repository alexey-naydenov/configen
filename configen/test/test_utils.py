import configen.utils as cu


def test_camel_case():
    assert cu.to_camel_case('') == ''
    assert cu.to_camel_case('t') == 'T'
    assert cu.to_camel_case('test') == 'Test'
    assert cu.to_camel_case('test_var') == 'TestVar'
    assert cu.to_camel_case('Test_Var') == 'TestVar'
    assert cu.to_camel_case('TestVar') == 'TestVar'
