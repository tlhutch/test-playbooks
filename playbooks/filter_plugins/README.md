Files in this directory are used for extending the template system.

For more info, see:

- <https://groups.google.com/forum/#!msg/ansible-project/A7fGX-7X-ks/Saszv6cmXH8J>
- <http://docs.ansible.com/ansible/intro_configuration.html#filter-plugins>

Basic example:

```python
def uppercase_all(arg):
    return arg.upper()


class FilterModule(object):
    def filters(self):
        return {'uppercase_all': uppercase_all}
```
