import sys
import os
import glob
import shutil
import time
from distutils import log
from setuptools import setup,Command
from setuptools.command.test import test as TestCommand

results_dir = 'results'
results_timestamp = time.strftime("%s", time.localtime())
default_args = '-v -l --tb=native --junitxml=%s/%s.xml --resultlog=%s/%s.log' % \
    (results_dir, results_timestamp, results_dir, results_timestamp)

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_suite = True
        self.test_args = os.environ.get('PY_ARGS', default_args)

        if not os.path.isdir(results_dir):
            os.mkdir(results_dir)

        if os.environ.has_key('PY_KEYWORDEXPR'):
            self.test_args += ' -k "%s"' % os.environ.get('PY_KEYWORDEXPR')

        self.test_args += " %s" % os.environ.get('PY_TESTS', 'tests')

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded elsewhere
        import pytest
        log.info("Running: pytest %s" % self.test_args)
        sys.path.insert(0, 'lib')
        pytest.main(self.test_args)

class CleanCommand(Command):
    description = "Custom clean command that forcefully removes dist/build directories"
    user_options = []
    def initialize_options(self):
        self.cwd = None
    def finalize_options(self):
        self.cwd = os.getcwd()
    def run(self):
        assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd

        # List of things to remove
        rm_list = list()

        # Find any .pyc files or __pycache__ dirs
        for root, dirs, files in os.walk(self.cwd, topdown=False):
            for fname in files:
                if fname.endswith('.pyc') and os.path.isfile(os.path.join(root, fname)):
                    rm_list.append(os.path.join(root, fname))
            if root.endswith('__pycache__'):
                rm_list.append(root)

        # Find egg's
        for egg_dir in glob.glob('*.egg') + \
                       glob.glob('*egg-info'):
            rm_list.append(egg_dir)

        # Zap!
        for rm in rm_list:
            log.info("Removing '%s'" % rm)
            if os.path.isdir(rm):
                if not self.dry_run: shutil.rmtree(rm)
            else:
                if not self.dry_run: os.remove(rm)

setup(
    name="ansibleworks-qa",
    # tests_require=open('requirements.txt', 'r').readlines(),
    setup_requires=['setuptools-pep8'],
    cmdclass = {'test': PyTest,
                'clean': CleanCommand,
                # 'build_sphinx': BuildSphinx},
               }
    )

