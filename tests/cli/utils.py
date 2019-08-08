def format_error(result):
    """Make pretty error for assertions on CLI result."""
    error = ''
    if hasattr(result, "stdout"):
        error += f'STDOUT: {result.stdout}\n'
    if hasattr(result, "stderr"):
        error += f'STDERR: {result.stderr}\n'
    return error
