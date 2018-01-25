const { exec } = require('child_process');

module.exports = {
    before: (client, done) => {
        process.stdout.write('IN BEGIN!');
        let env = process.env;
        env.TOWERKIT_USER = client.globals.username;
        env.TOWERKIT_USER_PASSWORD = client.globals.password;
        exec(
            `tkit -l -t ${client.globals.launch_url} -f ../scripts/tkit/configure_saml.py --saml-user saml_user --saml-password fo0m4nchU -x `,
            { env },
            (err, stdout, stderr) => {
                process.stdout.write(JSON.stringify(err));
                process.stdout.write(stdout);
                process.stdout.write(stderr);
                done(30000);
            });
    },
    'open ipsilon SSO': client => {
        const loginPage = client.page.login().navigate();
        loginPage.waitForAngular();
        client
            .waitForElementVisible('.icon-saml-02', 5000)
            .click('.icon-saml-02')
            .setValue('input[type=text][name=login_name]', 'test')
            .setValue('input[type=password][name=login_password]', 'fo0m4nchU')
            .click('button[type=submit][value=login]')
            .waitForAngular()
            .pause()
    },
    'open inventories': client => {
        const inventories = client.page.inventories();
        inventories.section.navigation.waitForElementVisible('@inventories');
        inventories.section.navigation.expect.element('@inventories').enabled;
        inventories.section.navigation.click('@inventories');
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');
    },
    'finish test': client => {
        client.end();
    }
};
