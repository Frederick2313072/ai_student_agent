"""
下载真实数据用于知识图谱大规模测试

从多个数据源下载文本数据：
1. 维基百科文章
2. 新闻文章  
3. 学术论文摘要
4. 技术文档
"""

import os
import requests
import json
import time
from typing import List, Dict
import urllib.parse


def download_wikipedia_articles(topics: List[str], lang: str = "zh") -> List[Dict[str, str]]:
    """下载维基百科文章"""
    articles = []
    
    print(f"📚 正在下载 {len(topics)} 个维基百科主题...")
    
    for topic in topics:
        try:
            # 维基百科API
            wiki_api = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
            
            response = requests.get(wiki_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 获取完整文章内容
                if data.get("extract"):
                    articles.append({
                        "title": data.get("title", topic),
                        "content": data.get("extract", ""),
                        "source": f"wikipedia_{lang}",
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    })
                    print(f"  ✅ {topic}")
                else:
                    print(f"  ⚠️ {topic} - 内容为空")
            else:
                print(f"  ❌ {topic} - HTTP {response.status_code}")
            
            time.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"  ❌ {topic} - 错误: {e}")
    
    return articles


def download_tech_articles() -> List[Dict[str, str]]:
    """下载技术文章内容"""
    articles = []
    
    # 一些技术概念的预定义内容
    tech_content = {
        "人工智能": """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
        人工智能包含多个子领域，如机器学习、深度学习、自然语言处理、计算机视觉等。
        机器学习是人工智能的核心技术，通过算法让计算机从数据中学习模式。
        深度学习是机器学习的一个子集，使用神经网络模拟人脑的工作方式。
        自然语言处理使计算机能够理解和生成人类语言。
        计算机视觉让机器能够识别和分析图像和视频内容。
        """,
        "区块链技术": """
        区块链是一种分布式数据库技术，通过密码学确保数据的安全性和不可篡改性。
        区块链由多个区块组成，每个区块包含交易记录和前一个区块的哈希值。
        比特币是第一个成功应用区块链技术的加密货币。
        以太坊在比特币基础上增加了智能合约功能。
        智能合约是自动执行的合约，其条款直接写入代码中。
        去中心化金融（DeFi）是基于区块链的金融服务。
        """,
        "云计算": """
        云计算是通过互联网提供计算资源和服务的技术模式。
        云计算服务模型包括基础设施即服务（IaaS）、平台即服务（PaaS）和软件即服务（SaaS）。
        Amazon Web Services（AWS）是全球最大的云服务提供商。
        Microsoft Azure和Google Cloud Platform是AWS的主要竞争对手。
        容器化技术如Docker改变了应用程序的部署方式。
        Kubernetes是容器编排的事实标准。
        微服务架构将应用拆分为多个小型服务。
        """,
        "数据科学": """
        数据科学是利用统计学、机器学习和编程技能从数据中提取洞察的跨学科领域。
        Python和R是数据科学中最流行的编程语言。
        Pandas是Python中最重要的数据处理库。
        NumPy为Python提供了高效的数组计算功能。
        Matplotlib和Seaborn用于数据可视化。
        Jupyter Notebook是数据科学家常用的交互式开发环境。
        机器学习模型可以分为监督学习、无监督学习和强化学习。
        """,
        "网络安全": """
        网络安全是保护计算机系统、网络和数据免受攻击的实践。
        防火墙是网络安全的第一道防线，控制网络流量。
        加密技术保护数据在传输和存储过程中的安全。
        入侵检测系统（IDS）监控网络异常活动。
        渗透测试通过模拟攻击来发现安全漏洞。
        恶意软件包括病毒、蠕虫、特洛伊木马和勒索软件。
        身份认证和访问控制确保只有授权用户能访问系统。
        """
    }
    
    print("📖 准备技术文章内容...")
    
    for title, content in tech_content.items():
        articles.append({
            "title": title,
            "content": content.strip(),
            "source": "tech_articles",
            "url": ""
        })
        print(f"  ✅ {title}")
    
    return articles


def download_news_articles() -> List[Dict[str, str]]:
    """下载新闻文章（模拟数据）"""
    articles = []
    
    # 科技新闻模拟内容
    news_content = {
        "ChatGPT推动AI革命": """
        OpenAI发布的ChatGPT标志着人工智能技术的重大突破。
        ChatGPT基于Transformer架构的大语言模型技术。
        大语言模型通过海量文本数据训练获得语言理解能力。
        GPT-4是OpenAI最新的多模态大模型。
        Google推出了Bard作为ChatGPT的竞争对手。
        百度发布了文心一言参与大模型竞赛。
        """,
        "元宇宙技术发展": """
        元宇宙是虚拟现实和增强现实技术的融合应用。
        Meta（原Facebook）大力投资元宇宙基础设施建设。
        虚拟现实（VR）提供沉浸式的三维体验。
        增强现实（AR）将虚拟信息叠加到现实世界。
        区块链技术为元宇宙提供数字资产确权。
        NFT（非同质化代币）成为数字艺术品的新载体。
        """,
        "量子计算进展": """
        量子计算利用量子力学原理进行信息处理。
        量子比特（qubit）是量子计算的基本单位。
        IBM、Google和中科院都在量子计算领域取得重要进展。
        量子优势是指量子计算机在特定问题上超越经典计算机。
        量子纠缠和量子叠加是量子计算的核心原理。
        量子算法如Shor算法可以威胁现有的加密系统。
        """
    }
    
    print("📰 准备新闻文章内容...")
    
    for title, content in news_content.items():
        articles.append({
            "title": title,
            "content": content.strip(),
            "source": "news",
            "url": ""
        })
        print(f"  ✅ {title}")
    
    return articles


def save_articles_to_files(articles: List[Dict[str, str]], data_dir: str = "data/test_corpus"):
    """保存文章到文件"""
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"💾 保存 {len(articles)} 篇文章到 {data_dir}...")
    
    # 保存元数据
    metadata = {
        "total_articles": len(articles),
        "sources": list(set(article["source"] for article in articles)),
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(os.path.join(data_dir, "metadata.json"), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 保存每篇文章
    for i, article in enumerate(articles):
        filename = f"{i:03d}_{article['title'].replace('/', '_')[:50]}.txt"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"标题: {article['title']}\n")
            f.write(f"来源: {article['source']}\n")
            f.write(f"URL: {article['url']}\n")
            f.write(f"{'='*50}\n\n")
            f.write(article['content'])
        
        print(f"  💾 {filename}")
    
    print(f"✅ 数据保存完成！")
    return data_dir


def create_combined_corpus(data_dir: str) -> str:
    """创建合并的语料库文件"""
    corpus_file = os.path.join(data_dir, "combined_corpus.txt")
    
    print("📖 创建合并语料库...")
    
    with open(corpus_file, 'w', encoding='utf-8') as outfile:
        for filename in sorted(os.listdir(data_dir)):
            if filename.endswith('.txt') and filename != 'combined_corpus.txt':
                filepath = os.path.join(data_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n" + "="*80 + "\n\n")
    
    # 获取文件大小
    file_size = os.path.getsize(corpus_file)
    print(f"✅ 合并语料库创建完成: {corpus_file}")
    print(f"   文件大小: {file_size / 1024:.1f} KB")
    
    return corpus_file


def main():
    """主函数"""
    print("🚀 知识图谱测试数据下载器")
    print("=" * 60)
    
    # 下载数据
    all_articles = []
    
    # 1. 技术文章
    tech_articles = download_tech_articles()
    all_articles.extend(tech_articles)
    
    # 2. 新闻文章
    news_articles = download_news_articles()
    all_articles.extend(news_articles)
    
    # 3. 维基百科文章（可选）
    wiki_topics = [
        "人工智能", "机器学习", "深度学习", "神经网络",
        "Python", "JavaScript", "数据库", "算法",
        "操作系统", "计算机网络", "软件工程", "云计算"
    ]
    
    try:
        wiki_articles = download_wikipedia_articles(wiki_topics[:5])  # 限制数量避免过多请求
        all_articles.extend(wiki_articles)
    except Exception as e:
        print(f"⚠️ 维基百科下载失败: {e}")
    
    print(f"\n📊 数据下载汇总:")
    print(f"   总文章数: {len(all_articles)}")
    
    source_counts = {}
    for article in all_articles:
        source = article["source"]
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in source_counts.items():
        print(f"   {source}: {count} 篇")
    
    # 保存文章
    data_dir = save_articles_to_files(all_articles)
    
    # 创建合并语料库
    corpus_file = create_combined_corpus(data_dir)
    
    print(f"\n🎯 测试数据准备完成！")
    print(f"   数据目录: {data_dir}")
    print(f"   合并语料库: {corpus_file}")
    print(f"\n📝 下一步:")
    print(f"   运行大规模测试: python scripts/test_large_scale_kg.py")
    
    return data_dir, corpus_file


if __name__ == "__main__":
    main()

