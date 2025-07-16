// 测试copilot页面的脚本
const puppeteer = require('puppeteer');

async function testCopilotPage() {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('正在访问copilot页面...');
  await page.goto('http://localhost:8230/copilot', { waitUntil: 'networkidle2' });
  
  // 等待页面加载
  await page.waitForTimeout(3000);
  
  // 检查页面标题
  const title = await page.title();
  console.log('页面标题:', title);
  
  // 检查是否有copilot组件
  const hasSidebar = await page.$('[class*="Sidebar"]') !== null;
  const hasWorkspace = await page.$('[class*="WorkSpace"]') !== null;
  const hasCopilot = await page.$('[class*="Copilot"]') !== null;
  
  console.log('组件检查:');
  console.log('- Sidebar:', hasSidebar);
  console.log('- WorkSpace:', hasWorkspace);
  console.log('- Copilot:', hasCopilot);
  
  // 获取页面内容
  const bodyText = await page.$eval('body', el => el.innerText.substring(0, 200));
  console.log('\n页面内容预览:');
  console.log(bodyText);
  
  // 检查控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('控制台错误:', msg.text());
    }
  });
  
  // 截图
  await page.screenshot({ path: 'copilot_test.png', fullPage: true });
  console.log('\n截图已保存为 copilot_test.png');
  
  await browser.close();
}

testCopilotPage().catch(console.error);