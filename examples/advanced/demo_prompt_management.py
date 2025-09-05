#!/usr/bin/env python3
"""
统一提示词管理系统演示

展示如何使用新的提示词管理系统来访问和格式化各种提示词模板。
"""

from feynman.agents.prompts import (
    prompt_manager, get_prompt, get_tool_error, get_tool_help, 
    get_api_response, get_role_definition, search_prompts
)

def demo_basic_usage():
    """演示基础使用方法"""
    print("🚀 统一提示词管理系统演示")
    print("=" * 50)
    
    # 1. 获取Agent核心提示词
    print("\n📋 1. Agent核心提示词")
    print("-" * 30)
    
    user_analysis = get_prompt("user_analysis_prompt", 
                              topic="机器学习", 
                              user_explanation="机器学习是让计算机通过数据学习的技术")
    print("用户分析提示词:")
    print(user_analysis[:100] + "...")
    
    # 2. 工具错误消息
    print("\n❌ 2. 工具错误消息")
    print("-" * 30)
    
    error_msg = get_tool_error("api_key_missing", service="OpenAI", key_name="OPENAI_API_KEY")
    print("API密钥缺失错误:")
    print(error_msg)
    
    # 3. 工具帮助信息
    print("\n📚 3. 工具帮助信息")
    print("-" * 30)
    
    help_msg = get_tool_help("web_search")
    print("网络搜索工具帮助:")
    print(help_msg)
    
    # 4. API响应格式化
    print("\n🔍 4. API响应格式化")
    print("-" * 30)
    
    search_response = get_api_response("search_result", 
                                     query="Python基础",
                                     source="Google",
                                     count=5,
                                     results="相关搜索结果...")
    print("搜索结果格式:")
    print(search_response)

def demo_role_definitions():
    """演示角色定义功能"""
    print("\n👤 5. 角色定义")
    print("-" * 30)
    
    student_role = get_role_definition("feynman_student")
    print("费曼学生Agent角色:")
    print(f"名称: {student_role['name']}")
    print(f"身份: {student_role['core_identity']}")
    print(f"主要目标: {student_role['primary_goal']}")
    
    print("\n个性特征:")
    for trait in student_role['personality_traits']:
        print(f"- {trait}")

def demo_template_management():
    """演示模板管理功能"""
    print("\n📂 6. 模板管理")
    print("-" * 30)
    
    # 列出所有Agent相关提示词
    agent_prompts = prompt_manager.list_prompts("agent")
    print("Agent相关提示词:")
    for prompt in agent_prompts:
        print(f"- {prompt}")
    
    # 搜索提示词
    search_results = search_prompts("错误")
    print(f"\n包含'错误'的提示词 ({len(search_results)} 个):")
    for result in search_results[:5]:  # 只显示前5个
        print(f"- {result}")

def demo_metadata():
    """演示元数据功能"""
    print("\n📊 7. 系统元数据")
    print("-" * 30)
    
    metadata = prompt_manager.get_metadata()
    print("提示词管理器信息:")
    print(f"版本: {metadata['version']}")
    print(f"总提示词数: {metadata['total_prompts']}")
    print(f"最后加载: {metadata['last_loaded']}")
    
    categories = metadata['categories']
    print("\n分类统计:")
    print(f"- Agent提示词: {categories.get('agent_prompts', 0)} 个")
    print(f"- 工具提示词: {categories.get('tool_prompts', 0)} 个") 
    print(f"- 系统提示词: {categories.get('system_prompts', 0)} 个")

def demo_advanced_features():
    """演示高级功能"""
    print("\n⚙️ 8. 高级功能")
    print("-" * 30)
    
    # 输出格式模板
    output_format = prompt_manager.get_output_format("structured_analysis")
    print("结构化分析格式:")
    print(f"名称: {output_format['name']}")
    print(f"描述: {output_format['description']}")
    print("必需字段:", output_format['required_fields'])
    
    # 评估标准
    evaluation = prompt_manager.get_evaluation_criteria("explanation_quality")
    print(f"\n解释质量评估标准:")
    for dimension, criteria in evaluation.items():
        print(f"\n{dimension.upper()}:")
        for level, description in criteria.items():
            print(f"  {level}: {description}")
        break  # 只显示第一个维度

def demo_conversation_templates():
    """演示对话模板"""
    print("\n💬 9. 对话流程模板")
    print("-" * 30)
    
    session_start = prompt_manager.get_conversation_template("session_start")
    print("会话开始模板:")
    print(f"问候语: {session_start['greeting']}")
    print(f"主题请求: {session_start['topic_request']}")

def main():
    """主演示函数"""
    try:
        demo_basic_usage()
        demo_role_definitions()
        demo_template_management()
        demo_metadata()
        demo_advanced_features()
        demo_conversation_templates()
        
        print(f"\n🎉 演示完成！")
        print("\n📝 使用说明:")
        print("1. 导入: from feynman.agents.prompts import prompt_manager, get_prompt, get_tool_error")
        print("2. 获取提示词: get_prompt('prompt_key', **params)")
        print("3. 工具错误: get_tool_error('error_type', **params)")
        print("4. 搜索: search_prompts('keyword')")
        print("5. 查看帮助: prompt_manager.get_metadata()")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("请确保提示词模块正确安装和配置")

if __name__ == "__main__":
    main()
