'use client'

export default function DocumentViewer() {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 文档头部信息 */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">量子计算在医疗中的应用.pdf</h2>
            <p className="text-sm text-gray-400 mt-1">45页 • 上传于2小时前 • 质量评分 ⭐⭐⭐⭐</p>
          </div>
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
              全屏阅读
            </button>
            <button className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700">
              下载
            </button>
          </div>
        </div>
      </div>

      {/* PDF预览区域 */}
      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg">
          {/* 模拟PDF内容 */}
          <div className="p-8 text-gray-900">
            <h1 className="text-2xl font-bold mb-6 text-center">
              量子计算在医疗诊断中的应用研究
            </h1>
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 text-blue-600">摘要</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                本研究探讨了量子计算技术在医疗诊断领域的应用现状和未来发展趋势。通过对2018-2023年间发表的150篇相关文献进行系统综述，我们发现量子计算在医学影像诊断、病理分析和临床决策支持等方面取得了显著进展。
              </p>
              <div className="bg-yellow-100 border-l-4 border-yellow-500 p-3 my-4">
                <p className="text-sm text-yellow-700">
                  💡 <strong>AI洞察</strong>：这段摘要提到了150篇文献，建议深入分析文献质量分布
                </p>
              </div>
            </div>

            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 text-blue-600">1. 引言</h2>
              <p className="text-gray-700 leading-relaxed mb-4">
                量子计算技术的快速发展为医疗诊断带来了革命性的变化。传统的医疗诊断依赖于医生的经验和知识，存在主观性强、效率低下等问题。
                <mark className="bg-blue-200">量子计算的引入不仅可以提高诊断的准确性和效率，还能够帮助解决医疗资源分布不均的问题。</mark>
              </p>
            </div>

            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 text-blue-600">2. 量子计算在医疗诊断中的主要应用</h2>
              
              <h3 className="text-lg font-medium mb-2 text-gray-800">2.1 医学影像诊断</h3>
              <p className="text-gray-700 leading-relaxed mb-4">
                深度学习，特别是卷积神经网络（CNN）在医学影像分析中表现出色。例如，Google的研究团队开发的AI系统在检测糖尿病视网膜病变方面的准确率达到了90.3%，超过了许多眼科专家。
              </p>
              <div className="bg-green-100 border-l-4 border-green-500 p-3 my-4">
                <p className="text-sm text-green-700">
                  🎯 <strong>关键数据</strong>：90.3%的准确率是一个重要指标，建议与最新研究对比
                </p>
              </div>

              <h3 className="text-lg font-medium mb-2 text-gray-800">2.2 病理分析</h3>
              <p className="text-gray-700 leading-relaxed mb-4">
                AI在病理切片分析中的应用日益广泛。斯坦福大学的研究人员开发的算法能够以91%的准确率区分皮肤癌和良性病变，这一准确率与21位认证皮肤科医生的平均水平相当。
              </p>
            </div>

            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-3 text-blue-600">3. 挑战与限制</h2>
              <p className="text-gray-700 leading-relaxed">
                高质量的标注数据是训练AI模型的基础。然而，医疗数据的获取和标注成本高昂，且涉及患者隐私保护的法律和伦理问题。
                <mark className="bg-red-200">量子退相干是当前量子计算面临的主要技术挑战。</mark>
              </p>
              <div className="bg-red-100 border-l-4 border-red-500 p-3 my-4">
                <p className="text-sm text-red-700">
                  ⚠️ <strong>技术挑战</strong>：量子退相干问题值得深入分析其解决方案
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 页面导航 */}
      <div className="bg-gray-800 border-t border-gray-700 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700">
              ← 上一页
            </button>
            <span className="text-sm text-gray-300">第 1 页，共 45 页</span>
            <button className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700">
              下一页 →
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">缩放：</span>
            <select className="bg-gray-700 text-gray-200 text-sm px-2 py-1 rounded border border-gray-600">
              <option>100%</option>
              <option>125%</option>
              <option>150%</option>
              <option>200%</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}