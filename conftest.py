"""
Top-level pytest configuration used to ignore non-Python 'test_output' files left in the repo.
"""

def pytest_ignore_collect(path, config):
    # Ignore text files named test_output* (binary or log files)
    try:
        name = path.name
    except Exception:
        return False
    if name.startswith('test_output') and not name.endswith('.py'):
        return True
    return False
