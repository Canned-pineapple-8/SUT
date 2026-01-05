def Type_Error(code, message):
    if message:
        raise RuntimeError(f"Type error №{code}: {message}")
    else:
        raise RuntimeError(f"Type error №{code}")
