const { creds, cookie, storage, config } = require("../config/config_loader");

module.exports = {
    CREDS :{
        USERNAME: creds.username,
        PASSWORD: creds.password,
    },
    LOCATORS:{
        LOGIN_PAGE: config.locators.login_page,
        AGREEMENT: config.locators.agreement,
        LOGIN_FIELD: config.locators.login_field,
        LOGIN_BTN: config.locators.login_btn,
        PASSWORD_FIELD: config.locators.password_field,
        BUY_NOW: config.locators.buy_now,
        GO_TO_CART: config.locators.go_to_cart,
        CHECKOUT: config.locators.checkout,
        CHECKBOX: config.locators.checkbox,
        PAY: config.locators.pay,
        ORDERING: config.locators.ordering
    },
    TARGET_PRODUCT: config.target_product,
    COOKIE: cookie,
    STORAGE: storage,
}