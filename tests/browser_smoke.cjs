// Optional real-browser checks. Install Playwright to rerun; core tests use stdlib.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.RELAYTRACE_PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const root = path.resolve(__dirname, '..');
  const demo = path.resolve(process.argv[2] || path.join(root, 'artifacts/RelayTrace_demo.html'));
  const output = path.join(root, 'artifacts/browser-checks');
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({headless:true, executablePath:process.env.RELAYTRACE_BROWSER_PATH || undefined, args:['--no-sandbox']});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors = [], requests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => {if(/^https?:/.test(r.url())) requests.push(r.url());});
  const checks = [];
  try {
    await page.goto(pathToFileURL(demo).href);
    await page.waitForFunction(() => document.querySelector('#event-count').textContent === '10');
    assert.equal(await page.locator('#edge-count').textContent(), '6');
    assert.equal(await page.locator('.result-card').count(), 6);
    checks.push('Real snapshot initializes with ten records and six relations');
    await page.selectOption('#episode-select', 'grocery-answer-relay');
    assert.equal(await page.locator('.result-card').count(), 3);
    await page.selectOption('#status-select', 'observed');
    assert.equal(await page.locator('.result-card').count(), 1);
    assert.match(await page.locator('#detail-panel').textContent(), /89 seconds/);
    assert.match(await page.locator('#detail-panel').textContent(), /±2 seconds/);
    checks.push('Episode and status filters preserve the 89 ± 2 second evidence relation');
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    await page.click('#reset-button');
    await page.selectOption('#status-select','unknown');
    const unknown = await page.locator('#detail-panel').textContent();
    assert.match(unknown,/Order unresolved/);
    assert.match(unknown,/Record A/);
    assert.doesNotMatch(unknown,/Earlier \/ source record|Later \/ target record/);
    checks.push('Unknown association has no asserted transfer direction');
    await page.click('#reset-button');
    await page.click('#posts-tab');
    assert.equal(await page.locator('.result-card').count(),10);
    await page.fill('#search-input','34,770');
    assert.equal(await page.locator('.result-card').count(),2);
    checks.push('Record view and phrase search return the cited contributions');
    await page.click('#theme-button');
    assert.ok(['dark','light'].includes(await page.locator('html').getAttribute('data-theme')));
    await page.setViewportSize({width:390,height:844});
    await page.click('#reset-button');
    await page.click('#relations-tab');
    const sizes = await page.evaluate(() => ({width:window.innerWidth, scroll:document.documentElement.scrollWidth}));
    assert.ok(sizes.scroll <= sizes.width + 2,JSON.stringify(sizes));
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    checks.push('Mobile layout fits a 390px viewport without horizontal overflow');

    const payload = '</script><img src="https://example.invalid/injected" onerror="window.INJECTED=true"><script>window.INJECTED=true</script>';
    const fixture = {dataset:{id:'synthetic-browser-test',title:payload,synthetic:true},events:[{id:'a',timestamp:'invalid',actor_handle:payload,page:payload,text:payload,source_url:'javascript:window.INJECTED=true'}],edges:[],episodes:[]};
    await page.setInputFiles('#file-input',{name:'adversarial.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(fixture))});
    await page.waitForFunction(() => document.querySelector('#event-count').textContent === '1');
    await page.click('#posts-tab');
    assert.match(await page.locator('#detail-panel').textContent(),/onerror/);
    assert.equal(await page.evaluate(() => window.INJECTED),undefined);
    assert.equal(await page.locator('img,iframe,object,embed').count(),0);
    assert.equal(await page.locator('a[href^="javascript:"]').count(),0);
    assert.match(await page.locator('#detail-panel').textContent(),/Time unknown/);
    checks.push('Malicious imported text stays literal; source script links and guessed dates are excluded');
    await page.setInputFiles('#file-input',{name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{broken')});
    await page.waitForFunction(() => document.querySelector('#notice').textContent.startsWith('Could not open this file:'));
    assert.equal(await page.locator('#event-count').textContent(),'1');
    checks.push('Malformed JSON shows an error and retains the prior dataset');
    assert.deepEqual(errors,[]);
    assert.deepEqual(requests,[]);
    checks.push('No page errors or HTTP requests occurred during the offline checks');
    const result = {browser:await browser.version(),checks,passed:checks.length,errors,network_requests:requests};
    fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));
  } finally {await browser.close();}
}
main().catch(error => {console.error(error.stack);process.exit(1);});
