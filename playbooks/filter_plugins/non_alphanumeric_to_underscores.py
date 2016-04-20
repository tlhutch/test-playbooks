import re

def non_alphanumeric_to_underscores(string):
    """Converts all non-word characters to underscores, and converts consecutive
    underscores into 1.
    """
    return re.sub(r'[\W_]+', '_', string)


class FilterModule(object):
    def filters(self):
        filter_ = {
            'non_alphanumeric_to_underscores': non_alphanumeric_to_underscores
        }

        return filter_
