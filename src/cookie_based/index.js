const puppeteer = require('puppeteer');
const CONSTANTS = require('../utils/constant');
const { delay, log, banner } = require('../utils/util');
banner()

async function run() {
  const start = performance.now()
  try {

    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();
  
    await page.goto(CONSTANTS.TARGET_PRODUCT)
    log.info('[+] Open login page')
  
    await page.setViewport({width: 1080, height: 1024});
    log.info('[+] setViewport to 1080x1024')
  
    await page.locator(CONSTANTS.LOCATORS.AGREEMENT).click()
    log.info('[+] accepted agreement')
  
    // const cookiesPath = path.join(__dirname, 'www.popmart.com.cookies.json');
    // const cookiesJson = fs.readFileSync(cookiesPath, 'utf-8');
    // const cookies = JSON.parse(cookiesJson);
    // log.info('[+] load cookie')
  
    await page.setCookie(...CONSTANTS.COOKIE);
    log.info('[+] set cookie')
  
    // const storagePath = path.join(__dirname, 'www.popmart.com.storage.json');
    // const storageJson = fs.readFileSync(storagePath, 'utf-8');
    // const storage = JSON.parse(storageJson);
    // log.info('[+] load local storage')
    const storage = CONSTANTS.STORAGE;
  
    await page.evaluate((storage) => {
      for (let key in storage) {
        localStorage.setItem(key, JSON.stringify(storage[key]));
      }
    }, storage);
    log.info('[+] set local storage')
  
    await page.reload();
    log.info('[+] reload web page')
  

    let found = false;
    while (!found) {
    try {
        await page.waitForSelector(CONSTANTS.LOCATORS.BUY_NOW, { timeout: 3000 });
        log.info('[+] ADD_TO_CART button found!');
        found = true; // Exit loop when found
    } catch (error) {
        log.warn('[-] ADD_TO_CART not available, retrying...');
    }
                    }

    await page.locator(CONSTANTS.LOCATORS.BUY_NOW).click()
  
    log.info('[+] ADD_TO_CART clicked') 

    await page.evaluate(selector => {
      const btn = document.querySelector(selector);
      if (btn) {
          btn.style.position = 'fixed';  // Keep it in place
          btn.style.zIndex = '9999';     // Keep it on top
          btn.style.opacity = '1';       // Make sure it stays visible
          btn.style.display = 'block';   // Ensure it's displayed
      }
  }, CONSTANTS.LOCATORS.GO_TO_CART);

    try {
      await page.waitForSelector(CONSTANTS.LOCATORS.GO_TO_CART, { state: 'attached', timeout: 5000 });
      await page.locator(CONSTANTS.LOCATORS.GO_TO_CART).click({ force: true });
      
      log.info('[+] GO_TO_CART button found and clicked!');
  } catch (error) {
      log.warn('[-] GO_TO_CART not available, retrying...');
  }

    await page.waitForNavigation();
    await page.waitForSelector(CONSTANTS.LOCATORS.CHECKBOX)
    await page.locator(CONSTANTS.LOCATORS.CHECKBOX).click()
    log.info("[+] CHECKBOX found and and clicked!")
    
    await page.waitForSelector(CONSTANTS.LOCATORS.CHECKOUT, {timeout: 1000})
    log.info("[+] CHECKOUT button found")
    await page.locator(CONSTANTS.LOCATORS.CHECKOUT).click()
    log.info("[+] Proceeding to checkout")


    await page.waitForNavigation({ waitUntil: 'networkidle2' })
    await delay(5000)
    log.info("[+] waiting for page to load")

    await page.waitForSelector(CONSTANTS.LOCATORS.PAY, {visible: true, timeout: 8000})
    log.info("[+] found PAY button")
    try{
      await page.locator(CONSTANTS.LOCATORS.PAY).click({force: true})
    log.info("[+] PAY button clicked")
    }
    catch(error) {
      log.warn("[-] pay button not clicked")
    }
    
  
    await page.hover(CONSTANTS.LOCATORS.ORDERING)
    log.info("[+] BUY!!")

    await page.waitForNavigation();
    log.info('[+] QR URL: ' + page.url())
  
    log.info("[+] ALL THING DONE! LET'S PAY!")
    log.warn("[!] CTRL+C When Everything Done!")
    log.warn(`[!] Total processing time: ${performance.now()-start} ms`)
    log.info('[+] QR URL: ' + page.url())
    await delay(999999)
    await browser.close();
  } catch (error) {
    log.error('[-] Error: ' + error)
  }

}

run();
