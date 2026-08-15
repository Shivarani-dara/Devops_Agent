from  test_project.app import add_numbers


def test_add_numbers():
    assert add_numbers(10, "900") == 910