const { exec } = require('child_process');

const { env } = process;

module.exports = {
    before: (client, done) => {
        env.TOWERKIT_USER = client.globals.username;
        env.TOWERKIT_USER_PASSWORD = client.globals.password;
        exec(
            `tkit -xl -t ${client.globals.launch_url} -f scripts/tkit/configure_saml.py`,
            { env },
            (err, stdout, stderr) => {
                process.stdout.write(JSON.stringify(err));
                process.stdout.write(stdout);
                process.stdout.write(stderr);
                done();
            }
        );
        client.waitForAngular();
    },
    after: (client, done) => {
        exec(
            'echo "v2.settings.get().get_setting(\'saml\').delete(); ' +
            'v2.users.get(username=\'saml_user\').results.pop().delete()" ' +
            `| tkit -t ${client.globals.launch_url}`,
            { env },
            (err, stdout, stderr) => {
                process.stdout.write(JSON.stringify(err));
                process.stdout.write(stdout);
                process.stdout.write(stderr);
                done();
            }
        );
    },
    'log into Tower via ipsilon SSO': client => {
        const login = client.page.login().navigate();
        login
            .waitForElementVisible('.icon-saml-02', 5000)
            .click('.icon-saml-02')
            .waitForElementVisible('input[type=text][name=login_name]')
            .setValue('input[type=text][name=login_name]', 'saml_user')
            .setValue('input[type=password][name=login_password]', 'fo0m4nchU')
            .click('button[type=submit][value=login]')
            .waitForAngular();
    },
    'open saml_user info': client => {
        const users = client.page.users();
        const row = '#users_table tbody tr';
        users
            .navigate()
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny')
            .waitForElementVisible('smart-search input')
            .sendKeys('smart-search input', `saml_user${client.Keys.ENTER}`)
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny')
            .waitForElementNotPresent(`${row}:nth-of-type(2)`)
            .expect.element(row).text.contain('saml_user');
        users
            .waitForElementVisible(`${row}:nth-of-type(1) a`)
            .click(`${row}:nth-of-type(1) a`);
    },
    'confirm desired saml_user info': client => {
        client.waitForElementVisible('input[name=first_name]');
        client.expect.element('input[name=first_name]').value.contain('SAML');
        client.expect.element('input[name=last_name]').value.contain('User');
        client.expect.element('input[name=email]').value.contain('saml_user@testing.ansible.com');
        client.expect.element('span[ng-show=external_account]').to.be.visible;
        client.expect.element('span[ng-show=external_account]').text.contain('SOCIAL');
        client.end();
    }
};
