const puppeteer = require('puppeteer');

async function testQAComplete() {
  console.log('🚀 开始完整QA测试...\n');
  
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1440, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // 1. 先测试后端API
    console.log('1. 测试后端API...');
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8001/api/v1/qa/answer', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-USER-ID': 'u1'
          },
          body: JSON.stringify({
            project_id: '4d5988c4-24c5-44cd-aaa3-c3f842edbdab',
            question: 'DPA系统测试问题',
            include_sources: true
          })
        });
        const data = await response.json();
        return { success: response.ok, status: response.status, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    console.log('API测试结果:', apiResponse);
    
    // 2. 访问QA页面
    console.log('\n2. 访问QA页面...');
    await page.goto('http://localhost:8031/qa');
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // 3. 检查页面状态
    const pageState = await page.evaluate(() => {
      const hasInput = !!document.querySelector('input[placeholder*="输入您的问题"]');
      const hasSendButton = !!document.querySelector('button:has(svg.lucide-send)');
      const hasConversationArea = !!document.querySelector('.w-80');
      const currentProject = localStorage.getItem('dpa-storage');
      
      return {
        hasInput,
        hasSendButton,
        hasConversationArea,
        hasProject: currentProject && currentProject.includes('currentProject')
      };
    });
    console.log('页面状态:', pageState);
    
    // 4. 如果没有项目，先选择项目
    if (!pageState.hasProject) {
      console.log('\n需要先选择项目...');
      await page.goto('http://localhost:8031/projects');
      await page.waitForSelector('.grid', { timeout: 5000 });
      
      const hasProjects = await page.$$('.hover\\:shadow-lg');
      if (hasProjects.length > 0) {
        await hasProjects[0].click();
        await page.waitForTimeout(1000);
        await page.goto('http://localhost:8031/qa');
        await page.waitForSelector('h1', { timeout: 5000 });
      }
    }
    
    // 5. 测试消息发送
    console.log('\n3. 测试消息发送...');
    
    // 监听网络请求
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers()
        });
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        console.log(`API响应: ${response.url()} - ${response.status()}`);
      }
    });
    
    // 输入问题
    await page.type('input[placeholder*="输入您的问题"]', 'DPA系统的核心功能是什么？');
    await page.waitForTimeout(500);
    
    // 点击发送
    await page.click('button:has(svg.lucide-send)');
    console.log('已点击发送按钮');
    
    // 等待响应
    await page.waitForTimeout(8000);
    
    // 6. 检查结果
    console.log('\n4. 检查消息显示...');
    const messages = await page.evaluate(() => {
      const msgs = [];
      document.querySelectorAll('.max-w-\\[70\\%\\]').forEach(el => {
        const isUser = el.innerHTML.includes('lucide-user');
        const content = el.querySelector('p')?.textContent;
        if (content) {
          msgs.push({
            role: isUser ? 'user' : 'assistant',
            content: content.substring(0, 100)
          });
        }
      });
      return msgs;
    });
    
    console.log('找到消息数:', messages.length);
    messages.forEach((msg, i) => {
      console.log(`消息${i + 1} [${msg.role}]:`, msg.content);
    });
    
    // 7. 截图
    await page.screenshot({ path: 'qa_complete_test.png', fullPage: true });
    console.log('\n✅ 测试截图已保存: qa_complete_test.png');
    
    // 8. 检查发送的请求
    console.log('\n发送的API请求:');
    requests.forEach(req => {
      console.log(`- ${req.method} ${req.url}`);
    });
    
  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    await page.screenshot({ path: 'qa_error_test.png', fullPage: true });
  } finally {
    await browser.close();
    console.log('\n测试完成！');
  }
}

testQAComplete().catch(console.error);