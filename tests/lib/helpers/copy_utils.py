def check_fields(original, replica, identical_fields, unequal_fields, no_assert=False):
    try:
        errors = ''
        try:
            for field in identical_fields:
                assert original.json[field] == replica.json[field], field
        except AssertionError as e:
            errors += str(e.value)

        try:
            for field in unequal_fields:
                assert original.json[field] != replica.json[field], field
        except AssertionError as e:
            errors += str(e.value)

        if errors:
            raise AssertionError(errors)

    except AssertionError:
        if no_assert:
            return False
        else:
            raise
    except:
        raise

    return True
