import pytest


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestInput(object):

    @pytest.mark.parametrize('truthy', ['1', 'true', 'yes', 'on'])
    def test_bool_casting_true(self, cli, truthy):
        result_color = cli(['awx', '--conf.color', truthy])

        # Check that the magic characters that cause color exist in result_color
        assert '\x1b[31m' in result_color.result.stdout, f'cli output doesnt contain color text when it should'

    @pytest.mark.parametrize('falsy', ['0', 'false', 'no', 'off'])
    def test_bool_casting_false(self, cli, falsy):
        result_no_color = cli(['awx', '--conf.color', falsy])

        # Check that the magic characters that cause color dont exist result_no_color
        assert '\x1b[31m' not in result_no_color.result.stdout, f'cli output contains color text when it shouldn\'t'
