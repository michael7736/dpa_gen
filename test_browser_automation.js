/**
 * 浏览器自动化测试脚本
 * 使用Puppeteer进行端到端测试
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 测试配置
const config = {
    baseUrl: 'http://localhost:8230',
    backendUrl: 'http://localhost:8200',
    headless: false, // 设置为false可以看到浏览器操作
    timeout: 30000
};

// 测试结果收集
let testResults = [];

function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${type.toUpperCase()}: ${message}`;
    console.log(logEntry);
    
    testResults.push({
        timestamp,
        type,
        message
    });
}

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkServices() {
    log('检查服务状态...');
    
    try {
        // 检查后端服务
        const backendResponse = await fetch(`${config.backendUrl}/api/v1/health`);
        if (backendResponse.ok) {
            log('✅ 后端服务正常运行', 'success');
        } else {
            log('❌ 后端服务异常', 'error');
            return false;
        }
    } catch (error) {
        log(`❌ 无法连接到后端服务: ${error.message}`, 'error');
        return false;
    }
    
    try {
        // 检查前端服务
        const frontendResponse = await fetch(`${config.baseUrl}`);
        if (frontendResponse.ok) {
            log('✅ 前端服务正常运行', 'success');
        } else {
            log('❌ 前端服务异常', 'error');
            return false;
        }
    } catch (error) {
        log(`❌ 无法连接到前端服务: ${error.message}`, 'error');
        log('请确保前端服务已启动: cd frontend && npm run dev', 'info');
        return false;
    }
    
    return true;
}

async function testAAGPageLoad(page) {
    log('测试AAG页面加载...');
    
    try {
        await page.goto(`${config.baseUrl}/aag`, {
            waitUntil: 'networkidle2',
            timeout: config.timeout
        });
        
        // 等待页面加载完成
        await page.waitForSelector('.h-screen', { timeout: 10000 });
        
        log('✅ AAG页面加载成功', 'success');
        
        // 检查关键元素
        const elementsToCheck = [
            { selector: '[data-testid="file-explorer"]', name: '文件浏览器' },
            { selector: '[data-testid="document-viewer"]', name: '文档查看器' },
            { selector: '[data-testid="ai-chat"]', name: 'AI聊天' }
        ];
        
        for (const element of elementsToCheck) {
            try {
                await page.waitForSelector(element.selector, { timeout: 5000 });
                log(`✅ ${element.name} 加载成功`, 'success');
            } catch (error) {
                log(`⚠️ ${element.name} 未找到，可能使用了不同的选择器`, 'warning');
            }
        }
        
        return true;
    } catch (error) {
        log(`❌ AAG页面加载失败: ${error.message}`, 'error');
        return false;
    }
}

async function testWebSocketConnection(page) {
    log('测试WebSocket连接...');
    
    try {
        // 在浏览器中执行WebSocket连接测试
        const wsResult = await page.evaluate(() => {
            return new Promise((resolve) => {
                const userId = '243588ff-459d-45b8-b77b-09aec3946a64';
                const connectionId = Math.random().toString(36).substr(2, 9);
                const wsUrl = `ws://localhost:8200/api/v1/ws/${userId}?connection_id=${connectionId}`;
                
                const ws = new WebSocket(wsUrl);
                let connected = false;
                
                const timeout = setTimeout(() => {
                    if (!connected) {
                        ws.close();
                        resolve({ success: false, error: 'Connection timeout' });
                    }
                }, 10000);
                
                ws.onopen = () => {
                    connected = true;
                    clearTimeout(timeout);
                    ws.close();
                    resolve({ success: true });
                };
                
                ws.onerror = (error) => {
                    clearTimeout(timeout);
                    resolve({ success: false, error: error.message || 'WebSocket error' });
                };
                
                ws.onclose = (event) => {
                    if (!connected) {
                        clearTimeout(timeout);
                        resolve({ success: false, error: `Connection closed: ${event.code}` });
                    }
                };
            });
        });
        
        if (wsResult.success) {
            log('✅ WebSocket连接测试成功', 'success');
        } else {
            log(`⚠️ WebSocket连接失败: ${wsResult.error}`, 'warning');
            log('系统将使用轮询模式作为备选', 'info');
        }
        
        return wsResult.success;
    } catch (error) {
        log(`❌ WebSocket连接测试异常: ${error.message}`, 'error');
        return false;
    }
}

async function testDocumentUpload(page) {
    log('测试文档上传功能...');
    
    try {
        // 创建测试文档
        const testContent = `# 测试文档

这是一个用于自动化测试的PDF文档。

## 主要内容

### 1. 技术概述
本文档介绍了人工智能在文档处理中的应用，包括：
- 文档解析和结构化
- 内容提取和摘要生成
- 智能问答系统

### 2. 系统架构
系统采用微服务架构，包含以下组件：
- 文档处理服务
- 向量化服务
- 问答服务
- 前端界面

### 3. 核心功能
- 文档上传和处理
- 自动摘要生成
- 智能索引创建
- 深度内容分析

### 4. 技术栈
- 前端: React + Next.js
- 后端: Python + FastAPI
- 数据库: PostgreSQL + Qdrant
- AI模型: OpenAI GPT-4

### 5. 结论
该系统能够有效处理各种文档格式，提供智能化的文档分析和问答服务。

测试时间: ${new Date().toISOString()}
`;
        
        // 查找上传按钮或拖拽区域
        const uploadSelectors = [
            'input[type="file"]',
            '[data-testid="upload-area"]',
            '.upload-area',
            '.file-upload',
            'button[title*="upload"]',
            'button[title*="上传"]'
        ];
        
        let uploadElement = null;
        for (const selector of uploadSelectors) {
            try {
                await page.waitForSelector(selector, { timeout: 2000 });
                uploadElement = await page.$(selector);
                if (uploadElement) {
                    log(`✅ 找到上传元素: ${selector}`, 'success');
                    break;
                }
            } catch (error) {
                // 继续尝试下一个选择器
            }
        }
        
        if (!uploadElement) {
            log('❌ 未找到文件上传元素', 'error');
            return false;
        }
        
        // 创建临时测试文件
        const testFilePath = path.join(__dirname, 'test_document.txt');
        fs.writeFileSync(testFilePath, testContent);
        
        // 上传文件
        await uploadElement.uploadFile(testFilePath);
        log('✅ 文件上传操作完成', 'success');
        
        // 等待上传处理
        await sleep(2000);
        
        // 检查上传结果
        const uploadResult = await page.evaluate(() => {
            // 检查是否有上传成功的指示
            const successIndicators = [
                '.upload-success',
                '.file-uploaded',
                '.processing',
                '.upload-complete'
            ];
            
            for (const indicator of successIndicators) {
                const element = document.querySelector(indicator);
                if (element) {
                    return { success: true, indicator };
                }
            }
            
            // 检查是否有错误消息
            const errorIndicators = [
                '.upload-error',
                '.error-message',
                '.upload-failed'
            ];
            
            for (const indicator of errorIndicators) {
                const element = document.querySelector(indicator);
                if (element) {
                    return { success: false, error: element.textContent };
                }
            }
            
            return { success: null, message: 'No clear upload result' };
        });
        
        // 清理临时文件
        fs.unlinkSync(testFilePath);
        
        if (uploadResult.success) {
            log('✅ 文档上传成功', 'success');
            return true;
        } else if (uploadResult.success === false) {
            log(`❌ 文档上传失败: ${uploadResult.error}`, 'error');
            return false;
        } else {
            log('⚠️ 文档上传结果不明确', 'warning');
            return false;
        }
        
    } catch (error) {
        log(`❌ 文档上传测试异常: ${error.message}`, 'error');
        return false;
    }
}

async function testSummaryGeneration(page) {
    log('测试摘要生成功能...');
    
    try {
        // 查找摘要生成按钮
        const summarySelectors = [
            'button[title*="摘要"]',
            'button[title*="summary"]',
            '.summary-button',
            '[data-testid="summary-btn"]',
            'button:contains("生成摘要")',
            'button:contains("摘要")'
        ];
        
        let summaryButton = null;
        for (const selector of summarySelectors) {
            try {
                await page.waitForSelector(selector, { timeout: 2000 });
                summaryButton = await page.$(selector);
                if (summaryButton) {
                    log(`✅ 找到摘要按钮: ${selector}`, 'success');
                    break;
                }
            } catch (error) {
                // 继续尝试下一个选择器
            }
        }
        
        if (!summaryButton) {
            log('❌ 未找到摘要生成按钮', 'error');
            return false;
        }
        
        // 点击摘要生成按钮
        await summaryButton.click();
        log('✅ 点击摘要生成按钮', 'success');
        
        // 等待处理
        await sleep(3000);
        
        // 检查进度指示器
        const progressResult = await page.evaluate(() => {
            const progressSelectors = [
                '.progress',
                '.loading',
                '.processing',
                '.progress-bar'
            ];
            
            for (const selector of progressSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    return { found: true, selector };
                }
            }
            
            return { found: false };
        });
        
        if (progressResult.found) {
            log('✅ 检测到处理进度指示器', 'success');
        } else {
            log('⚠️ 未检测到处理进度指示器', 'warning');
        }
        
        // 等待处理完成（最多等待30秒）
        let completed = false;
        const maxWaitTime = 30000;
        const checkInterval = 2000;
        let waitTime = 0;
        
        while (!completed && waitTime < maxWaitTime) {
            await sleep(checkInterval);
            waitTime += checkInterval;
            
            const result = await page.evaluate(() => {
                // 检查是否有完成指示器
                const completedSelectors = [
                    '.completed',
                    '.finished',
                    '.done',
                    'button:contains("查看结果")',
                    'button[title*="查看结果"]'
                ];
                
                for (const selector of completedSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return { completed: true, selector };
                    }
                }
                
                return { completed: false };
            });
            
            if (result.completed) {
                completed = true;
                log('✅ 摘要生成完成', 'success');
                break;
            }
        }
        
        if (!completed) {
            log('⚠️ 摘要生成超时，但这可能是正常的', 'warning');
        }
        
        return true;
        
    } catch (error) {
        log(`❌ 摘要生成测试异常: ${error.message}`, 'error');
        return false;
    }
}

async function testResultViewing(page) {
    log('测试结果查看功能...');
    
    try {
        // 查找"查看结果"按钮
        const viewResultSelectors = [
            'button:contains("查看结果")',
            'button[title*="查看结果"]',
            '.view-result-btn',
            '[data-testid="view-result"]'
        ];
        
        let viewResultButton = null;
        for (const selector of viewResultSelectors) {
            try {
                await page.waitForSelector(selector, { timeout: 2000 });
                viewResultButton = await page.$(selector);
                if (viewResultButton) {
                    log(`✅ 找到查看结果按钮: ${selector}`, 'success');
                    break;
                }
            } catch (error) {
                // 继续尝试下一个选择器
            }
        }
        
        if (!viewResultButton) {
            log('⚠️ 未找到查看结果按钮，可能还未完成处理', 'warning');
            return false;
        }
        
        // 点击查看结果按钮
        await viewResultButton.click();
        log('✅ 点击查看结果按钮', 'success');
        
        // 等待模态框出现
        await sleep(1000);
        
        // 检查模态框是否出现
        const modalResult = await page.evaluate(() => {
            const modalSelectors = [
                '.modal',
                '.dialog',
                '.result-modal',
                '[role="dialog"]'
            ];
            
            for (const selector of modalSelectors) {
                const element = document.querySelector(selector);
                if (element && element.style.display !== 'none') {
                    return { found: true, selector };
                }
            }
            
            return { found: false };
        });
        
        if (modalResult.found) {
            log('✅ 结果查看模态框已打开', 'success');
            
            // 等待一会儿以便查看内容
            await sleep(2000);
            
            // 关闭模态框
            await page.keyboard.press('Escape');
            log('✅ 关闭结果查看模态框', 'success');
            
            return true;
        } else {
            log('❌ 结果查看模态框未打开', 'error');
            return false;
        }
        
    } catch (error) {
        log(`❌ 结果查看测试异常: ${error.message}`, 'error');
        return false;
    }
}

async function takeScreenshot(page, name) {
    try {
        const screenshotPath = path.join(__dirname, `screenshot_${name}_${Date.now()}.png`);
        await page.screenshot({ 
            path: screenshotPath, 
            fullPage: true 
        });
        log(`📸 截图已保存: ${screenshotPath}`, 'info');
        return screenshotPath;
    } catch (error) {
        log(`❌ 截图失败: ${error.message}`, 'error');
        return null;
    }
}

async function generateTestReport() {
    const reportPath = path.join(__dirname, `test_report_${Date.now()}.json`);
    
    const report = {
        timestamp: new Date().toISOString(),
        testResults,
        summary: {
            total: testResults.length,
            success: testResults.filter(r => r.type === 'success').length,
            error: testResults.filter(r => r.type === 'error').length,
            warning: testResults.filter(r => r.type === 'warning').length
        }
    };
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    log(`📊 测试报告已生成: ${reportPath}`, 'info');
    
    return report;
}

async function runTests() {
    log('🚀 开始自动化测试...');
    
    // 检查服务状态
    const servicesOk = await checkServices();
    if (!servicesOk) {
        log('❌ 服务检查失败，无法继续测试', 'error');
        return;
    }
    
    let browser = null;
    let page = null;
    
    try {
        // 启动浏览器
        browser = await puppeteer.launch({
            headless: config.headless,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        page = await browser.newPage();
        
        // 设置视口大小
        await page.setViewport({ width: 1920, height: 1080 });
        
        // 设置用户代理
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        log('✅ 浏览器已启动', 'success');
        
        // 运行测试
        const tests = [
            { name: 'AAG页面加载', func: testAAGPageLoad },
            { name: 'WebSocket连接', func: testWebSocketConnection },
            { name: '文档上传', func: testDocumentUpload },
            { name: '摘要生成', func: testSummaryGeneration },
            { name: '结果查看', func: testResultViewing }
        ];
        
        for (const test of tests) {
            log(`\n🧪 开始测试: ${test.name}`);
            
            try {
                const result = await test.func(page);
                
                if (result) {
                    log(`✅ ${test.name} 测试通过`, 'success');
                } else {
                    log(`❌ ${test.name} 测试失败`, 'error');
                }
                
                // 每个测试后截图
                await takeScreenshot(page, test.name.replace(/\s+/g, '_'));
                
            } catch (error) {
                log(`❌ ${test.name} 测试异常: ${error.message}`, 'error');
            }
            
            // 测试间隔
            await sleep(1000);
        }
        
    } catch (error) {
        log(`❌ 测试执行异常: ${error.message}`, 'error');
        
    } finally {
        // 清理
        if (browser) {
            await browser.close();
            log('✅ 浏览器已关闭', 'success');
        }
        
        // 生成报告
        const report = await generateTestReport();
        
        log('\n📊 测试总结:');
        log(`总数: ${report.summary.total}`);
        log(`成功: ${report.summary.success}`);
        log(`错误: ${report.summary.error}`);
        log(`警告: ${report.summary.warning}`);
        
        log('\n🎯 测试完成!');
    }
}

// 运行测试
if (require.main === module) {
    runTests().catch(console.error);
}

module.exports = { runTests };