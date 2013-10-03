import random
import string
import sys
import uuid

def generate_random_int(max=sys.maxint):
    max = int(max)
    return random.randint(0, max)

def generate_random_string(size=8):
    size = int(size)
    def random_string_generator(size):
        choice_chars = string.letters + string.digits
        for x in xrange(size):
            yield random.choice(choice_chars)
    return ''.join(random_string_generator(size))

def generate_random_uuid_as_str():
    return str(uuid.uuid4())
