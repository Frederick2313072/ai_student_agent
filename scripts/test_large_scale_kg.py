"""
大规模知识图谱构建测试

使用真实数据测试知识图谱的性能和质量。
"""

import asyncio
import time
import json
import os
import sys
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feynman.core.graph.service import KnowledgeGraphService
from src.feynman.core.graph.schema import KnowledgeTriple
from mock_extractor import create_mock_kg_service


class KnowledgeGraphBenchmark:
    """知识图谱性能测试"""
    
    def __init__(self, use_mock: bool = True):
        if use_mock:
            print("🎭 使用模拟抽取器进行测试")
            # 这里会在运行时异步创建
            self.kg_service = None
            self.use_mock = True
        else:
            self.kg_service = KnowledgeGraphService()
            self.use_mock = False
        self.results = {}
    
    async def _init_service(self):
        """异步初始化服务"""
        if self.use_mock and self.kg_service is None:
            self.kg_service = await create_mock_kg_service()
    
    async def test_single_file_processing(self, file_path: str) -> Dict[str, Any]:
        """测试单个文件的处理性能"""
        await self._init_service()  # 确保服务已初始化
        
        print(f"📄 测试文件: {os.path.basename(file_path)}")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"   文件大小: {file_size / 1024:.1f} KB")
        print(f"   字符数: {len(content):,}")
        
        # 测试构建过程
        start_time = time.time()
        
        try:
            result = await self.kg_service.build_from_file(file_path)
            
            build_time = time.time() - start_time
            
            if result["success"]:
                stats = result.get("graph_stats", {})
                
                test_result = {
                    "file_path": file_path,
                    "file_size_kb": file_size / 1024,
                    "content_length": len(content),
                    "build_time_seconds": round(build_time, 2),
                    "triples_added": result.get("added_triples", 0),
                    "total_nodes": stats.get("num_nodes", 0),
                    "total_edges": stats.get("num_edges", 0),
                    "processing_speed_kb_per_sec": round((file_size / 1024) / build_time, 2),
                    "success": True
                }
                
                print(f"   ✅ 处理成功")
                print(f"   ⏱️ 耗时: {build_time:.2f}秒")
                print(f"   📊 三元组: {result.get('added_triples', 0)}")
                print(f"   🌐 节点: {stats.get('num_nodes', 0)}, 边: {stats.get('num_edges', 0)}")
                print(f"   🚀 处理速度: {test_result['processing_speed_kb_per_sec']} KB/秒")
                
            else:
                test_result = {
                    "file_path": file_path,
                    "file_size_kb": file_size / 1024,
                    "build_time_seconds": round(build_time, 2),
                    "error": result.get("message", "未知错误"),
                    "success": False
                }
                
                print(f"   ❌ 处理失败: {result.get('message', '未知错误')}")
            
            return test_result
            
        except Exception as e:
            print(f"   💥 异常: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "success": False
            }
    
    async def test_batch_processing(self, data_dir: str) -> Dict[str, Any]:
        """测试批量文件处理"""
        print(f"\n📁 批量测试目录: {data_dir}")
        
        # 获取所有文本文件
        text_files = []
        for filename in os.listdir(data_dir):
            if filename.endswith('.txt') and filename != 'combined_corpus.txt':
                text_files.append(os.path.join(data_dir, filename))
        
        print(f"   发现 {len(text_files)} 个文本文件")
        
        # 批量处理
        batch_start_time = time.time()
        file_results = []
        
        for file_path in text_files[:10]:  # 限制处理数量避免过长
            file_result = await self.test_single_file_processing(file_path)
            file_results.append(file_result)
            
            # 短暂暂停避免API限制
            await asyncio.sleep(1)
        
        total_batch_time = time.time() - batch_start_time
        
        # 统计结果
        successful_files = [r for r in file_results if r.get("success", False)]
        failed_files = [r for r in file_results if not r.get("success", False)]
        
        total_triples = sum(r.get("triples_added", 0) for r in successful_files)
        total_size_kb = sum(r.get("file_size_kb", 0) for r in successful_files)
        avg_processing_time = sum(r.get("build_time_seconds", 0) for r in successful_files) / len(successful_files) if successful_files else 0
        
        batch_result = {
            "total_files": len(text_files),
            "processed_files": len(file_results),
            "successful_files": len(successful_files),
            "failed_files": len(failed_files),
            "total_batch_time_seconds": round(total_batch_time, 2),
            "total_triples_extracted": total_triples,
            "total_size_kb": round(total_size_kb, 2),
            "avg_processing_time_seconds": round(avg_processing_time, 2),
            "overall_speed_kb_per_sec": round(total_size_kb / total_batch_time, 2) if total_batch_time > 0 else 0,
            "file_results": file_results
        }
        
        print(f"\n📊 批量处理结果:")
        print(f"   ✅ 成功: {len(successful_files)}/{len(file_results)}")
        print(f"   ⏱️ 总耗时: {total_batch_time:.2f}秒")
        print(f"   📊 总三元组: {total_triples}")
        print(f"   🚀 平均速度: {batch_result['overall_speed_kb_per_sec']} KB/秒")
        
        return batch_result
    
    async def test_graph_query_performance(self) -> Dict[str, Any]:
        """测试图查询性能"""
        await self._init_service()  # 确保服务已初始化
        
        print(f"\n🔍 测试图查询性能...")
        
        # 获取当前图统计
        stats = self.kg_service.get_stats()
        basic_stats = stats.get("basic", {})
        
        print(f"   当前图规模:")
        print(f"   - 节点数: {basic_stats.get('num_nodes', 0)}")
        print(f"   - 边数: {basic_stats.get('num_edges', 0)}")
        
        query_results = {}
        
        # 1. 测试全图查询
        start_time = time.time()
        full_graph = self.kg_service.storage.get_graph(limit=500)
        query_results["full_graph_query_time"] = time.time() - start_time
        
        print(f"   全图查询(限制500): {query_results['full_graph_query_time']:.3f}秒")
        
        # 2. 测试实体搜索
        if full_graph.nodes:
            start_time = time.time()
            search_results = self.kg_service.search_entities("Python", limit=10)
            query_results["entity_search_time"] = time.time() - start_time
            
            print(f"   实体搜索: {query_results['entity_search_time']:.3f}秒")
            print(f"   搜索结果: {len(search_results)} 个实体")
            
            # 3. 测试子图查询
            if search_results:
                center_entity = search_results[0]['id']
                start_time = time.time()
                subgraph = self.kg_service.storage.get_subgraph(center_entity, radius=2)
                query_results["subgraph_query_time"] = time.time() - start_time
                
                print(f"   子图查询(半径2): {query_results['subgraph_query_time']:.3f}秒")
                print(f"   子图规模: {len(subgraph.nodes)} 节点, {len(subgraph.edges)} 边")
        
        return query_results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合测试"""
        print("🚀 开始大规模知识图谱测试")
        print("=" * 60)
        
        # 1. 下载测试数据
        sys.path.append('scripts')
        from download_test_data import main as download_data
        
        data_dir, corpus_file = download_data()
        
        print("\n" + "=" * 60)
        
        # 2. 批量处理测试
        batch_result = await self.test_batch_processing(data_dir)
        
        # 3. 查询性能测试
        query_result = await self.test_graph_query_performance()
        
        # 4. 最终统计
        final_stats = self.kg_service.get_stats()
        
        comprehensive_result = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": data_dir,
            "batch_processing": batch_result,
            "query_performance": query_result,
            "final_graph_stats": final_stats,
            "test_summary": {
                "total_processing_time": batch_result.get("total_batch_time_seconds", 0),
                "total_triples": batch_result.get("total_triples_extracted", 0),
                "final_nodes": final_stats.get("basic", {}).get("num_nodes", 0),
                "final_edges": final_stats.get("basic", {}).get("num_edges", 0),
                "success_rate": f"{batch_result.get('successful_files', 0)}/{batch_result.get('processed_files', 0)}"
            }
        }
        
        # 保存测试结果
        results_file = "data/kg_benchmark_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 综合测试结果:")
        summary = comprehensive_result["test_summary"]
        print(f"   ⏱️ 总处理时间: {summary['total_processing_time']}秒")
        print(f"   📊 总三元组数: {summary['total_triples']}")
        print(f"   🌐 最终图规模: {summary['final_nodes']} 节点, {summary['final_edges']} 边")
        print(f"   ✅ 成功率: {summary['success_rate']}")
        print(f"   💾 结果已保存到: {results_file}")
        
        return comprehensive_result


async def main():
    """主测试函数"""
    benchmark = KnowledgeGraphBenchmark(use_mock=True)  # 使用模拟抽取器
    
    try:
        results = await benchmark.run_comprehensive_test()
        
        print(f"\n🎉 大规模知识图谱测试完成！")
        
        # 显示性能指标
        summary = results["test_summary"]
        if summary["total_triples"] > 0:
            print(f"\n📈 性能指标:")
            processing_time = summary["total_processing_time"]
            if processing_time > 0:
                print(f"   - 三元组/秒: {summary['total_triples'] / processing_time:.1f}")
                print(f"   - 节点/秒: {summary['final_nodes'] / processing_time:.1f}")
        
        # 检查图谱质量
        final_stats = results["final_graph_stats"]
        basic_stats = final_stats.get("basic", {})
        
        if basic_stats.get("num_nodes", 0) > 0:
            print(f"\n🏆 图谱质量指标:")
            print(f"   - 平均度数: {basic_stats.get('avg_degree', 0):.2f}")
            print(f"   - 最大度数: {basic_stats.get('max_degree', 0)}")
            
            relationships = basic_stats.get("relationships", {})
            if relationships:
                print(f"   - 关系类型数: {len(relationships)}")
                most_common = max(relationships.items(), key=lambda x: x[1])
                print(f"   - 最常见关系: {most_common[0]} ({most_common[1]}次)")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
