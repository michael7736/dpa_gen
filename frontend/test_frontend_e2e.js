const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testFrontendE2E() {
  console.log('🚀 开始前端端到端测试...\n');
  
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1280, height: 800 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // 测试结果收集
  const results = [];
  
  function logResult(test, success, message = '') {
    const status = success ? '✅ PASS' : '❌ FAIL';
    console.log(`${status} ${test}`);
    if (message) console.log(`   ${message}`);
    results.push({ test, success, message });
  }

  try {
    // 1. 测试首页访问
    console.log('1. 测试首页访问...');
    await page.goto('http://localhost:8031');
    await page.waitForSelector('h1', { timeout: 5000 });
    const title = await page.$eval('h1', el => el.textContent);
    logResult('首页加载', title.includes('项目'), `标题: ${title}`);
    
    // 2. 测试项目列表
    console.log('\n2. 测试项目列表...');
    await page.goto('http://localhost:8031/projects');
    await page.waitForSelector('.grid', { timeout: 5000 });
    const projectCards = await page.$$('.hover\\:shadow-lg');
    logResult('项目列表加载', projectCards.length > 0, `找到 ${projectCards.length} 个项目`);
    
    // 3. 测试项目详情
    if (projectCards.length > 0) {
      console.log('\n3. 测试项目详情页...');
      
      // 获取第一个项目的信息
      const projectName = await page.$eval('.hover\\:shadow-lg h3', el => el.textContent);
      console.log(`   选择项目: ${projectName}`);
      
      // 点击项目卡片
      await projectCards[0].click();
      await page.waitForNavigation({ waitUntil: 'networkidle0' });
      
      // 检查URL是否变化
      const currentUrl = page.url();
      const isProjectDetailPage = currentUrl.includes('/projects/') && currentUrl.split('/').length > 4;
      logResult('项目详情页导航', isProjectDetailPage, `URL: ${currentUrl}`);
      
      // 检查页面内容
      if (isProjectDetailPage) {
        await page.waitForSelector('h1', { timeout: 5000 });
        const detailTitle = await page.$eval('h1', el => el.textContent);
        logResult('项目详情加载', detailTitle === projectName, `项目名称: ${detailTitle}`);
        
        // 检查标签页
        const tabs = await page.$$('[role="tab"]');
        logResult('标签页显示', tabs.length > 0, `找到 ${tabs.length} 个标签`);
      }
    }
    
    // 4. 测试文档页面
    console.log('\n4. 测试文档管理页...');
    await page.goto('http://localhost:8031/documents');
    await page.waitForSelector('h1', { timeout: 5000 });
    
    // 检查是否需要选择项目
    const pageContent = await page.content();
    if (pageContent.includes('请先选择一个项目')) {
      logResult('文档页面状态检查', false, '需要先选择项目');
      
      // 返回项目列表选择项目
      await page.goto('http://localhost:8031/projects');
      await page.waitForSelector('.hover\\:shadow-lg');
      await page.click('.hover\\:shadow-lg');
      await sleep(1000);
      
      // 再次访问文档页面
      await page.goto('http://localhost:8031/documents');
      await page.waitForSelector('h1', { timeout: 5000 });
    }
    
    // 检查文档上传区域
    const fileInput = await page.$('input[type="file"]');
    logResult('文档上传组件', !!fileInput, fileInput ? '找到文件上传输入框' : '未找到文件上传输入框');
    
    // 5. 测试侧边栏
    console.log('\n5. 测试侧边栏功能...');
    const menuButton = await page.$('button[aria-label*="菜单"]');
    if (menuButton) {
      await menuButton.click();
      await sleep(500);
      
      // 检查侧边栏是否显示
      const sidebar = await page.$('aside');
      const isVisible = await sidebar.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.transform === 'translateX(0px)' || style.transform === 'none';
      });
      logResult('侧边栏切换', isVisible, isVisible ? '侧边栏已显示' : '侧边栏未显示');
    }
    
    // 生成测试报告
    console.log('\n📊 测试总结：');
    const passedTests = results.filter(r => r.success).length;
    const totalTests = results.length;
    console.log(`总测试数: ${totalTests}`);
    console.log(`通过: ${passedTests}`);
    console.log(`失败: ${totalTests - passedTests}`);
    console.log(`通过率: ${(passedTests / totalTests * 100).toFixed(1)}%`);
    
    // 如果有失败的测试，截图保存
    if (passedTests < totalTests) {
      await page.screenshot({ path: 'test_failure_screenshot.png', fullPage: true });
      console.log('\n❌ 测试失败截图已保存: test_failure_screenshot.png');
    }
    
  } catch (error) {
    console.error('\n❌ 测试过程中出现错误:', error);
    await page.screenshot({ path: 'test_error_screenshot.png', fullPage: true });
    console.log('错误截图已保存: test_error_screenshot.png');
  } finally {
    await browser.close();
    console.log('\n✅ 前端端到端测试完成！');
  }
}

// 检查Puppeteer是否安装
try {
  require.resolve('puppeteer');
  testFrontendE2E().catch(console.error);
} catch (e) {
  console.error('❌ 需要先安装Puppeteer:');
  console.log('   cd frontend && npm install puppeteer');
}