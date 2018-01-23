module.exports = {
    'log into tower': client => {
        client.login();
        client.resizeWindow(1200, 1200);
        client.waitForAngular();
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
