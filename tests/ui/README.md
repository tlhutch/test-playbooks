tower-qa ui tests
=====

The tower-qa ui tests are [Nightwatch](http://nightwatchjs.org/) tests that consume the [awx/e2e](https://github.com/ansible/awx/tree/devel/awx/ui/test/e2e) page objects and commands while exercising Tower functionality not suitable for exposure via the awx project.
The current, and very early stage, workflow for using them does not support a headless mode.


# Requirements
1. [Node.js 6.x](https://nodejs.org/dist/latest-v6.x/).  This LTS version seems to be required by awx.

# Installation
```
$ cd tower-qa/tests/ui/
$ npm install
$ bin/run -t https://tower.example.com -u username -p password
```
