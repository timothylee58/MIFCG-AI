from mifcg_ai import greet


def test_greet_returns_expected_message() -> None:
    assert greet("MIFCG") == "Hello, MIFCG!"
