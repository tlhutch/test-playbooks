import path from 'path';

const resolve = location => path.resolve(__dirname, location);

const AWX_E2E_LAUNCH_URL = process.env.AWX_E2E_LAUNCH_URL
const AWX_E2E_PASSWORD = process.env.AWX_E2E_PASSWORD 
const AWX_E2E_USERNAME = process.env.AWX_E2E_USERNAME;
const AWX_E2E_TIMEOUT_ASYNC = 30000;
const AWX_E2E_TIMEOUT_LONG = 10000;
const AWX_E2E_TIMEOUT_MEDIUM = 5000;
const AWX_E2E_TIMEOUT_SHORT = 1000;

module.exports = {
    custom_commands_path: resolve('./awx/awx/ui/test/e2e/commands'),
    page_objects_path: resolve('./awx/awx/ui/test/e2e/objects'),
    src_folders: ["tests"],
    output_folder: "reports",
    globals_path: "",
    selenium: {
        start_process: true,
        server_path: "./bin/selenium-server-standalone.jar",
        log_path: "",
        port: 4444,
        cli_args: {
            "webdriver.chrome.driver": "./awx/awx/ui/node_modules/chromedriver/bin/chromedriver"
        }
    },
    test_settings: {
        default: {
            globals: {
                launch_url: AWX_E2E_LAUNCH_URL,
                AWX_E2E_TIMEOUT_LONG: AWX_E2E_TIMEOUT_LONG,
                AWX_E2E_TIMEOUT_MEDIUM: AWX_E2E_TIMEOUT_MEDIUM,
                AWX_E2E_TIMEOUT_SHORT: AWX_E2E_TIMEOUT_SHORT,
                waitForConditionTimeout: AWX_E2E_TIMEOUT_MEDIUM
            },
            selenium_port: 4444,
            selenium_host: "localhost",
            silent: true,
            screenshots: {
                enabled: false,
                path: ""
            },
            desiredCapabilities: {
                browserName: "chrome"
            }
        }
    }
};

