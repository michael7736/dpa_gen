const puppeteer = require('puppeteer');
const path = require('path');

async function testDocumentUpload() {
  const browser = await puppeteer.launch({ 
    headless: false,
    defaultViewport: { width: 1280, height: 800 }
  });
  const page = await browser.newPage();

  try {
    console.log('1. 导航到项目页面...');
    await page.goto('http://localhost:3000/projects');
    await page.waitForSelector('[href="/projects/new"]', { visible: true });

    // 检查是否已有项目
    const projectCards = await page.$$('.hover\\:shadow-lg');
    
    if (projectCards.length === 0) {
      console.log('2. 没有找到项目，创建新项目...');
      // 点击新建项目
      await page.click('[href="/projects/new"]');
      await page.waitForNavigation();
      
      // 填写项目信息
      await page.waitForSelector('input[name="name"]');
      await page.type('input[name="name"]', '文档上传测试项目');
      await page.type('textarea[name="description"]', '用于测试文档上传功能的项目');
      await page.type('input[name="keywords"]', '测试, 文档处理, RAG');
      
      // 提交表单
      await page.click('button[type="submit"]');
      await page.waitForNavigation();
      console.log('   ✓ 项目创建成功');
      
      // 返回项目列表
      await page.goto('http://localhost:3000/projects');
      await page.waitForSelector('.hover\\:shadow-lg');
    }

    console.log('3. 选择第一个项目...');
    const projectCard = await page.$('.hover\\:shadow-lg');
    if (!projectCard) {
      throw new Error('未找到任何项目');
    }
    
    // 获取项目信息
    const projectName = await page.$eval('.hover\\:shadow-lg h3', el => el.textContent);
    console.log(`   选中项目: ${projectName}`);
    
    // 点击项目卡片会设置currentProject并导航到项目详情页
    await projectCard.click();
    await page.waitForNavigation();
    
    console.log('4. 导航到文档页面...');
    // 从项目详情页导航到文档页面
    await page.goto('http://localhost:3000/documents');
    await page.waitForSelector('h1');
    
    // 检查是否显示"请先选择一个项目"
    const pageContent = await page.content();
    if (pageContent.includes('请先选择一个项目')) {
      console.log('   ⚠️  文档页面未识别选中的项目，需要修复状态管理');
      
      // 直接通过侧边栏导航
      console.log('5. 通过侧边栏重新选择项目...');
      await page.goto('http://localhost:3000/projects');
      await page.waitForSelector('.hover\\:shadow-lg');
      
      // 点击项目但不跟随链接
      await page.evaluate(() => {
        const card = document.querySelector('.hover\\:shadow-lg');
        const event = new MouseEvent('click', { bubbles: true });
        card.dispatchEvent(event);
      });
      
      // 等待状态更新
      await page.waitForTimeout(500);
      
      // 再次导航到文档页面
      await page.goto('http://localhost:3000/documents');
      await page.waitForSelector('h1');
    }
    
    // 再次检查
    const hasUploadSection = await page.$('input[type="file"]');
    if (!hasUploadSection) {
      console.log('   ❌ 文档页面仍显示"请先选择一个项目"');
      console.log('   需要修复项目状态管理逻辑');
      return;
    }
    
    console.log('6. 测试文档上传...');
    // 创建测试文档
    const fs = require('fs');
    const testDocPath = path.join(__dirname, 'test_document.md');
    const testDocContent = `# 测试文档

这是一个用于测试文档上传功能的Markdown文档。

## 第一章：介绍

本文档包含以下内容：
- 测试内容1
- 测试内容2
- 测试内容3

## 第二章：详细内容

这里是一些详细的测试内容，用于验证文档处理功能是否正常工作。

### 2.1 子章节

更多测试内容...`;
    
    fs.writeFileSync(testDocPath, testDocContent);
    
    // 上传文件
    const fileInput = await page.$('input[type="file"]');
    await fileInput.uploadFile(testDocPath);
    
    // 等待文件名显示
    await page.waitForSelector('.text-muted-foreground', { text: /已选择/ });
    console.log('   ✓ 文件已选择');
    
    // 点击上传按钮
    await page.click('button:has-text("上传")');
    
    // 等待上传完成或错误
    await page.waitForSelector('.text-destructive, .text-green-500', { timeout: 30000 });
    
    // 检查结果
    const hasError = await page.$('.text-destructive');
    if (hasError) {
      const errorText = await hasError.evaluate(el => el.textContent);
      console.log(`   ❌ 上传失败: ${errorText}`);
    } else {
      console.log('   ✓ 文档上传成功');
      
      // 等待文档出现在列表中
      await page.waitForSelector('.grid .flex.items-center.justify-between', { timeout: 10000 });
      
      // 检查文档处理状态
      const statusElement = await page.$('.flex.items-center.gap-2 span');
      if (statusElement) {
        const status = await statusElement.evaluate(el => el.textContent);
        console.log(`   文档状态: ${status}`);
      }
    }
    
    // 清理测试文件
    fs.unlinkSync(testDocPath);
    
    console.log('\n测试完成！');
    
  } catch (error) {
    console.error('测试失败:', error);
    
    // 截图保存错误状态
    await page.screenshot({ path: 'test_error.png', fullPage: true });
    console.log('错误截图已保存到 test_error.png');
  } finally {
    await browser.close();
  }
}

// 运行测试
testDocumentUpload().catch(console.error);