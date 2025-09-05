# 统一提示词管理系统指南

## 📖 概述

费曼学习系统现在采用了统一的提示词管理架构，将所有提示词模板集中管理，提供了标准化的访问接口和版本控制功能。

## 🏗️ 架构设计

### 目录结构

```
prompts/
├── __init__.py              # 统一导出接口
├── agent_prompts.py         # Agent核心提示词
├── tool_prompts.py          # 工具相关提示词  
├── system_prompts.py        # 系统级提示词
└── prompt_manager.py        # 提示词管理器
```

### 分类说明

| 分类 | 文件 | 内容 |
|------|------|------|
| **Agent提示词** | `agent_prompts.py` | ReAct系统提示、用户分析、记忆摘要、问题生成等 |
| **工具提示词** | `tool_prompts.py` | 工具错误消息、帮助信息、输出格式模板等 |
| **系统提示词** | `system_prompts.py` | 角色定义、评估标准、对话流程等 |

## 🚀 基础使用

### 快速开始

```python
# 导入统一接口
from prompts import get_prompt, get_tool_error, get_tool_help, prompt_manager

# 获取格式化提示词
user_prompt = get_prompt("user_analysis_prompt", 
                        topic="机器学习", 
                        user_explanation="用户的解释内容")

# 获取工具错误消息
error_msg = get_tool_error("api_key_missing", 
                          service="OpenAI", 
                          key_name="OPENAI_API_KEY")

# 获取工具帮助信息
help_text = get_tool_help("web_search")
```

### 核心API

#### 1. 基础提示词获取

```python
# 获取格式化提示词
prompt = get_prompt(prompt_key, **format_params)

# 示例
analysis_prompt = get_prompt("user_analysis_prompt", 
                           topic="Python", 
                           user_explanation="Python是一种编程语言")
```

#### 2. 工具相关功能

```python
# 工具错误消息
error = get_tool_error("rag_db_not_found", directory="/path/to/db")

# 工具帮助信息  
help_info = get_tool_help("knowledge_retriever")

# API响应格式化
response = get_api_response("search_result",
                           query="搜索词",
                           source="Google", 
                           count=5,
                           results="结果内容")
```

#### 3. 角色和模板管理

```python
# 获取角色定义
role = get_role_definition("feynman_student")

# 获取输出格式模板
format_template = prompt_manager.get_output_format("structured_analysis")

# 获取评估标准
criteria = prompt_manager.get_evaluation_criteria("explanation_quality")
```

## 🔍 高级功能

### 1. 提示词搜索

```python
# 搜索包含关键词的提示词
results = search_prompts("错误")
print(f"找到 {len(results)} 个相关提示词")

# 列出特定分类的提示词
agent_prompts = prompt_manager.list_prompts("agent")
tool_prompts = prompt_manager.list_prompts("tool") 
system_prompts = prompt_manager.list_prompts("system")
```

### 2. 模板验证

```python
# 验证提示词参数
is_valid = prompt_manager.validate_prompt_parameters(
    "user_analysis_prompt",
    {"topic": "Python", "user_explanation": "内容"}
)
```

### 3. 元数据获取

```python
# 获取系统元数据
metadata = prompt_manager.get_metadata()
print(f"版本: {metadata['version']}")
print(f"总提示词数: {metadata['total_prompts']}")
print(f"分类统计: {metadata['categories']}")
```

### 4. 批量导出

```python
# 导出所有提示词到JSON文件
json_data = prompt_manager.export_prompts("prompts_backup.json")
```

## 📋 提示词分类详解

### Agent核心提示词

| 提示词 | 用途 | 参数 |
|--------|------|------|
| `react_system_prompt` | ReAct Agent核心系统提示 | `tools` |
| `user_analysis_prompt` | 用户输入分析 | `topic`, `user_explanation` |
| `memory_summary_prompt` | 记忆摘要生成 | `conversation_str` |
| `question_templates` | 问题生成模板集 | `point`, `concept`, 等 |

### 工具提示词

| 类别 | 用途 | 示例 |
|------|------|------|
| `tool_errors` | 工具错误消息 | `api_key_missing`, `file_operation_failed` |
| `tool_help` | 工具帮助信息 | `knowledge_retriever`, `web_search` |
| `api_responses` | API响应格式 | `search_result`, `calculation_result` |
| `tool_status` | 工具状态消息 | `initializing`, `processing`, `success` |

### 系统级提示词

| 模板组 | 内容 | 用途 |
|--------|------|------|
| `system_roles` | 角色定义 | 定义AI助手的身份和行为 |
| `output_formats` | 输出格式 | 标准化响应结构 |
| `evaluation_criteria` | 评估标准 | 质量评估和打分标准 |
| `conversation_flows` | 对话流程 | 不同阶段的对话模板 |

## 🛠️ 在Agent中的集成

### 更新前的代码

```python
# 旧方式：硬编码提示词
prompt_text = f"这是用户对主题'{topic}'的解释，请分析: {user_explanation}"

# 旧方式：分散的错误消息
if not api_key:
    return "API密钥未设置，请配置后重试"
```

### 更新后的代码

```python
# 新方式：统一管理
from prompts import get_prompt, get_tool_error

# 使用统一的提示词模板
prompt_text = get_prompt("user_analysis_prompt", 
                        topic=topic, 
                        user_explanation=user_explanation)

# 使用标准化的错误消息
if not api_key:
    return get_tool_error("api_key_missing", 
                         service="OpenAI", 
                         key_name="OPENAI_API_KEY")
```

## 📝 最佳实践

### 1. 命名约定

- **提示词键名**: 使用下划线分隔的小写字母，如 `user_analysis_prompt`
- **错误类型**: 使用描述性名称，如 `api_key_missing`, `file_operation_failed`
- **模板参数**: 使用清晰的参数名，如 `topic`, `user_explanation`

### 2. 参数验证

```python
# 在使用提示词前验证参数
if not prompt_manager.validate_prompt_parameters(prompt_key, params):
    raise ValueError(f"提示词 {prompt_key} 参数不完整")
```

### 3. 错误处理

```python
# 优雅处理提示词获取错误
try:
    prompt = get_prompt("user_analysis_prompt", **params)
except KeyError as e:
    logger.error(f"提示词键名不存在: {e}")
    prompt = "默认提示词内容"
except ValueError as e:
    logger.error(f"提示词参数错误: {e}")
    prompt = "参数格式化失败"
```

### 4. 版本控制

```python
# 检查提示词版本
metadata = prompt_manager.get_metadata()
if metadata['version'] != expected_version:
    logger.warning("提示词版本不匹配，请更新")
```

## 🔧 自定义和扩展

### 添加新的提示词

1. **选择合适的分类文件** (agent_prompts.py, tool_prompts.py, system_prompts.py)
2. **添加提示词模板**:

```python
# 在 agent_prompts.py 中添加
new_prompt_template = """
这是一个新的提示词模板，参数: {param1}, {param2}
"""

new_prompt = PromptTemplate.from_template(new_prompt_template)
```

3. **更新导出列表**:

```python
# 在 __init__.py 中添加
from .agent_prompts import new_prompt

__all__ = [
    # ... 现有导出
    'new_prompt',
]
```

### 添加新的工具错误类型

```python
# 在 tool_prompts.py 中添加
tool_error_messages.update({
    "new_error_type": "这是新的错误消息模板: {error_detail}"
})
```

### 创建自定义管理器

```python
from prompts.prompt_manager import PromptManager

class CustomPromptManager(PromptManager):
    def __init__(self):
        super().__init__()
        self._load_custom_prompts()
    
    def _load_custom_prompts(self):
        # 加载自定义提示词
        self._prompts_cache.update({
            "custom_prompt": "自定义提示词内容"
        })
```

## 🧪 测试和验证

### 运行演示脚本

```bash
# 运行提示词管理演示
python demo_prompt_management.py
```

### 单元测试示例

```python
import pytest
from prompts import get_prompt, get_tool_error, prompt_manager

def test_user_analysis_prompt():
    """测试用户分析提示词"""
    prompt = get_prompt("user_analysis_prompt",
                       topic="测试主题",
                       user_explanation="测试解释")
    assert "测试主题" in prompt
    assert "测试解释" in prompt

def test_tool_error_formatting():
    """测试工具错误消息格式化"""
    error = get_tool_error("api_key_missing", 
                          service="TestService",
                          key_name="TEST_API_KEY") 
    assert "TestService" in error
    assert "TEST_API_KEY" in error

def test_prompt_manager_metadata():
    """测试提示词管理器元数据"""
    metadata = prompt_manager.get_metadata()
    assert "version" in metadata
    assert "total_prompts" in metadata
    assert metadata["total_prompts"] > 0
```

## 🚨 故障排除

### 常见问题

1. **导入错误**
   ```python
   ModuleNotFoundError: No module named 'prompts'
   ```
   **解决方案**: 确保 prompts 目录在 Python 路径中，或使用绝对导入

2. **提示词键名不存在**
   ```python
   KeyError: '提示词键名不存在'
   ```
   **解决方案**: 检查键名拼写，或使用 `prompt_manager.list_prompts()` 查看可用键名

3. **格式化参数缺失**
   ```python
   ValueError: 提示词参数不完整
   ```
   **解决方案**: 使用 `validate_prompt_parameters` 验证参数完整性

### 调试技巧

```python
# 1. 查看所有可用的提示词
all_prompts = prompt_manager.list_prompts()
print("可用提示词:", all_prompts)

# 2. 搜索相关提示词
results = search_prompts("关键词")
print("搜索结果:", results)

# 3. 检查提示词内容
prompt_content = prompt_manager._prompts_cache.get("prompt_key")
print("提示词内容:", prompt_content)

# 4. 验证参数
is_valid = prompt_manager.validate_prompt_parameters(
    "prompt_key", {"param1": "value1"}
)
print("参数有效:", is_valid)
```

## 📈 性能优化

### 缓存机制

- 所有提示词在初始化时加载到内存缓存
- 避免重复文件读取和模板解析
- 支持动态重新加载：`prompt_manager.reload_prompts()`

### 内存使用

- 当前提示词总数: ~50个模板
- 内存占用: <1MB
- 加载时间: <100ms

## 📚 相关文档

- [Agent工作流文档](agent_workflow_guide.md)
- [工具系统指南](tools_guide.md)  
- [监控运维指南](monitoring_operations_guide.md)
- [API参考文档](../README.md)

## 🤝 贡献指南

### 提交新提示词

1. Fork项目并创建功能分支
2. 在合适的分类文件中添加提示词
3. 更新 `__init__.py` 导出列表
4. 添加单元测试
5. 更新文档
6. 提交PR

### 代码规范

- 遵循PEP8代码规范
- 提示词使用三引号字符串
- 参数使用大括号格式化: `{param_name}`
- 添加详细的docstring

---

**版本**: 3.2.0  
**最后更新**: 2024-08-20  
**维护者**: AI Student Agent Team

