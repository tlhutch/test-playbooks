from setuptools import setup, find_packages
from pip.req import parse_requirements

requirements = [str(r.req) for r in parse_requirements('requirements.txt', session=False)]

version = '0.1.0'
setup(name='tower_qe',
      version=version,
      description='Ansible Tower QE Libraries',
      packages=find_packages(exclude=['test']),
      include_package_data=True,
      install_requires=requirements)
