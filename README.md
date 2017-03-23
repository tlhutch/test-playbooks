## Tower Integration Tests

```bash
# install dependencies
pip install -r requirements.txt

# decrypt credentials
ansible-vault decrypt config/credentials.vault --output=config/credentials.yml

# run api tests
py.test -c config/api.cfg --base-url='https://ec2-tower.com'

# run ui tests
py.test -c config/ui.cfg --base-url='https://ec2-tower.com' tests/ui
```
