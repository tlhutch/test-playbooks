import path from 'path';

import {
    AWX_E2E_LAUNCH_URL,
    AWX_E2E_USERNAME,
    AWX_E2E_PASSWORD,
    AWX_E2E_TIMEOUT_LONG,
    AWX_E2E_TIMEOUT_MEDIUM,
    AWX_E2E_TIMEOUT_SHORT
} from './awx/awx/ui/test/e2e/settings';

const resolve = location => path.resolve(__dirname, location);

module.exports = {
    custom_commands_path: resolve('./awx/awx/ui/test/e2e/commands'),
    page_objects_path: resolve('./awx/awx/ui/test/e2e/objects'),
    src_folders: ['tests'],
    output_folder: 'reports',
    globals_path: '',
    selenium: {
        start_process: true,
        server_path: './bin/selenium-server-standalone.jar',
        log_path: '',
        port: 4444,
        cli_args: {
            'webdriver.chrome.driver': './awx/awx/ui/node_modules/chromedriver/bin/chromedriver'
        }
    },
    test_settings: {
        default: {
            exclude: ['tests/node_modules/*'],
            globals: {
                waitForConditionTimeout: AWX_E2E_TIMEOUT_MEDIUM,
                launch_url: AWX_E2E_LAUNCH_URL,
                username: AWX_E2E_USERNAME,
                password: AWX_E2E_PASSWORD,
                AWX_E2E_TIMEOUT_LONG,
                AWX_E2E_TIMEOUT_MEDIUM,
                AWX_E2E_TIMEOUT_SHORT
            },
            selenium_port: 4444,
            selenium_host: 'localhost',
            silent: true,
            screenshots: {
                enabled: false,
                path: ''
            },
            desiredCapabilities: {
                browserName: 'chrome'
            }
        }
    }
};

