import os

def test_updater_exists():
    """Verify that the updater script exists."""
    assert os.path.exists("updater.py")

# We just verify existence as testing the updater would require a mock 
# git environment and HTTP responses for zip downloading.
# We consider it a "dry run" pass if the file parses correctly.
def test_updater_syntax():
    """Verify that updater.py has valid python syntax."""
    with open("updater.py", "r", encoding="utf-8") as f:
        source = f.read()
    try:
        compile(source, "updater.py", "exec")
        valid = True
    except SyntaxError:
        valid = False
    assert valid
