

def check_identical_fields(original, replica, fields):
    for field in fields:
        assert original.json[field] == replica.json[field]


def check_unequal_fields(original, replica, fields):
    for field in fields:
        assert original.json[field] != replica.json[field]
