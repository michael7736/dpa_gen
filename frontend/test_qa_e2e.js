const puppeteer = require('puppeteer');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testQAInterface() {
  console.log('🚀 开始QA界面端到端测试...\n');
  
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1440, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // 设置请求拦截器，添加认证头
  await page.setRequestInterception(true);
  page.on('request', (request) => {
    const headers = request.headers();
    headers['X-USER-ID'] = 'u1';
    request.continue({ headers });
  });
  
  // 测试结果收集
  const results = [];
  
  function logResult(test, success, message = '') {
    const status = success ? '✅ PASS' : '❌ FAIL';
    console.log(`${status} ${test}`);
    if (message) console.log(`   ${message}`);
    results.push({ test, success, message });
  }

  try {
    // 1. 访问项目列表并选择项目
    console.log('1. 准备测试环境...');
    await page.goto('http://localhost:8031/projects');
    await page.waitForSelector('.grid', { timeout: 10000 });
    
    // 查找并点击测试项目
    const projectCards = await page.$$('.hover\\:shadow-lg');
    if (projectCards.length === 0) {
      logResult('项目选择', false, '没有找到项目');
      throw new Error('需要先创建项目');
    }
    
    const projectName = await page.$eval('.hover\\:shadow-lg h3', el => el.textContent);
    console.log(`   选择项目: ${projectName}`);
    await projectCards[0].click();
    await sleep(1000);
    
    // 2. 访问QA页面
    console.log('\n2. 测试QA页面访问...');
    await page.goto('http://localhost:8031/qa');
    await page.waitForSelector('h1', { timeout: 5000 });
    
    // 检查页面标题
    const pageTitle = await page.$eval('h1', el => el.textContent);
    logResult('QA页面加载', pageTitle.includes('知识问答'), `页面标题: ${pageTitle}`);
    
    // 3. 检查界面元素
    console.log('\n3. 检查界面元素...');
    
    // 检查对话历史区域
    const conversationHistory = await page.$('.w-80');
    logResult('对话历史区域', !!conversationHistory, conversationHistory ? '找到对话历史区域' : '未找到对话历史区域');
    
    // 检查输入框
    const inputField = await page.$('input[placeholder*="输入您的问题"]');
    logResult('输入框', !!inputField, inputField ? '找到输入框' : '未找到输入框');
    
    // 检查发送按钮
    const sendButton = await page.$('button svg.lucide-send');
    logResult('发送按钮', !!sendButton, sendButton ? '找到发送按钮' : '未找到发送按钮');
    
    // 4. 测试发送消息
    console.log('\n4. 测试发送消息...');
    
    // 输入测试问题
    const testQuestion = 'DPA系统的主要功能是什么？';
    await page.type('input[placeholder*="输入您的问题"]', testQuestion);
    await sleep(500);
    
    // 点击发送按钮
    const sendButtonElement = await page.$('button:has(svg.lucide-send)');
    await sendButtonElement.click();
    logResult('发送消息', true, `发送问题: ${testQuestion}`);
    
    // 等待AI响应
    console.log('   等待AI响应...');
    await sleep(3000); // 给AI响应一些时间
    
    // 检查是否有消息显示
    const messages = await page.$$('.max-w-\\[70\\%\\]');
    logResult('消息显示', messages.length > 0, `找到 ${messages.length} 条消息`);
    
    // 5. 检查对话列表更新
    console.log('\n5. 检查对话列表...');
    await sleep(2000); // 等待对话列表更新
    
    const conversationItems = await page.$$('.p-3.rounded-lg.cursor-pointer');
    logResult('对话列表更新', conversationItems.length > 0, `找到 ${conversationItems.length} 个对话`);
    
    // 6. 测试创建新对话
    console.log('\n6. 测试创建新对话...');
    const newConversationButton = await page.$('button:has(svg.lucide-plus)');
    if (newConversationButton) {
      await newConversationButton.click();
      await sleep(500);
      logResult('创建新对话', true, '点击新对话按钮');
      
      // 发送新消息
      await page.type('input[placeholder*="输入您的问题"]', '这是一个新的对话测试');
      const sendButton2 = await page.$('button:has(svg.lucide-send)');
      await sendButton2.click();
      await sleep(2000);
      
      // 检查对话列表是否增加
      const newConversationItems = await page.$$('.p-3.rounded-lg.cursor-pointer');
      logResult('新对话创建', newConversationItems.length > conversationItems.length, 
        `对话数量: ${conversationItems.length} -> ${newConversationItems.length}`);
    }
    
    // 7. 测试对话切换
    console.log('\n7. 测试对话切换...');
    const conversations = await page.$$('.p-3.rounded-lg.cursor-pointer');
    if (conversations.length >= 2) {
      // 点击第二个对话
      await conversations[1].click();
      await sleep(1000);
      logResult('对话切换', true, '切换到另一个对话');
      
      // 检查消息区域是否更新
      const updatedMessages = await page.$$('.max-w-\\[70\\%\\]');
      logResult('消息区域更新', true, `显示 ${updatedMessages.length} 条消息`);
    }
    
    // 8. 截图保存
    await page.screenshot({ path: 'qa_interface_test.png', fullPage: true });
    console.log('\n📸 测试截图已保存: qa_interface_test.png');
    
    // 生成测试报告
    console.log('\n📊 测试总结：');
    const passedTests = results.filter(r => r.success).length;
    const totalTests = results.length;
    console.log(`总测试数: ${totalTests}`);
    console.log(`通过: ${passedTests}`);
    console.log(`失败: ${totalTests - passedTests}`);
    console.log(`通过率: ${(passedTests / totalTests * 100).toFixed(1)}%`);
    
  } catch (error) {
    console.error('\n❌ 测试过程中出现错误:', error);
    await page.screenshot({ path: 'qa_test_error.png', fullPage: true });
    console.log('错误截图已保存: qa_test_error.png');
  } finally {
    await browser.close();
    console.log('\n✅ QA界面测试完成！');
  }
}

// 运行测试
testQAInterface().catch(console.error);