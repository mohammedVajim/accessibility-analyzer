// scanner/node_scripts/accessibilityCheck.js
const puppeteer = require('puppeteer');
const { AxePuppeteer } = require('axe-puppeteer');

async function runAccessibilityCheck(url) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setBypassCSP(true);
    await page.goto(url);

    const results = await new AxePuppeteer(page).analyze();
    console.log(JSON.stringify(results));  // Output for Django
    await browser.close();
}

const url = process.argv[2];
// if (!url) {
//     console.error("No URL provided");
//     process.exit(1);
// }
try {
    new URL(url); // throws if invalid
} catch (err) {
    console.error("Invalid URL format");
    process.exit(1);
}

runAccessibilityCheck(url);
