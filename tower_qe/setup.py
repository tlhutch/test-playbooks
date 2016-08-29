from setuptools import setup, find_packages

version = '0.1.0'
setup(name='tower_qe',
      version=version,
      description='Ansible Tower QE Libraries',
      packages=find_packages(exclude=['test']),
      include_package_data=True)
