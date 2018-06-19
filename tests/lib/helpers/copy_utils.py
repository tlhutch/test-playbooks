def check_fields(original, replica, identical_fields, unequal_fields, no_assert=False):
    try:
        for field in identical_fields:
            assert original.json[field] == replica.json[field]

        for field in unequal_fields:
            assert original.json[field] != replica.json[field]
    except AssertionError:
        if no_assert:
            return False
        else:
            raise
    except:
        raise

    return True
