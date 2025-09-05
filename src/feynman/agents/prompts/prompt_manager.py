"""
提示词管理器

提供统一的接口来访问、管理和版本控制所有提示词模板。
支持动态加载、缓存、格式化和验证功能。
"""

import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from .agent_prompts import (
    react_system_prompt_template, user_analysis_prompt_template,
    memory_summary_prompt_template, question_generation_templates,
    explanation_evaluation_template, role_definitions
)
from .tool_prompts import (
    tool_error_messages, tool_help_messages, 
    mindmap_output_templates, flowchart_output_templates,
    api_response_templates, tool_status_messages
)
from .system_prompts import (
    system_role_definitions, output_format_templates,
    evaluation_criteria, conversation_flow_templates,
    error_handling_templates, learning_scenario_templates
)

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        """初始化提示词管理器"""
        self._prompts_cache = {}
        self._templates_cache = {}
        self._metadata = {
            "version": "3.2.0",
            "last_loaded": datetime.now().isoformat(),
            "total_prompts": 0
        }
        
        # 加载所有提示词
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """加载所有提示词到缓存"""
        
        # Agent核心提示词
        self._prompts_cache.update({
            "react_system_prompt": react_system_prompt_template,
            "user_analysis_prompt": user_analysis_prompt_template,
            "memory_summary_prompt": memory_summary_prompt_template,
            "question_templates": question_generation_templates,
            "explanation_evaluation": explanation_evaluation_template,
            "role_definitions": role_definitions
        })
        
        # 工具相关提示词
        self._prompts_cache.update({
            "tool_errors": tool_error_messages,
            "tool_help": tool_help_messages,
            "mindmap_templates": mindmap_output_templates,
            "flowchart_templates": flowchart_output_templates,
            "api_responses": api_response_templates,
            "tool_status": tool_status_messages
        })
        
        # 系统级提示词
        self._prompts_cache.update({
            "system_roles": system_role_definitions,
            "output_formats": output_format_templates,
            "evaluation_criteria": evaluation_criteria,
            "conversation_flows": conversation_flow_templates,
            "error_handling": error_handling_templates,
            "learning_scenarios": learning_scenario_templates
        })
        
        self._metadata["total_prompts"] = len(self._prompts_cache)
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        获取格式化的提示词
        
        Args:
            prompt_key: 提示词键名
            **kwargs: 格式化参数
            
        Returns:
            格式化后的提示词字符串
        """
        if prompt_key not in self._prompts_cache:
            raise KeyError(f"提示词 '{prompt_key}' 不存在")
        
        template = self._prompts_cache[prompt_key]
        
        if isinstance(template, str):
            try:
                return template.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"提示词 '{prompt_key}' 缺少必需参数: {e}")
        elif isinstance(template, dict):
            return template
        else:
            return str(template)
    
    def get_template(self, category: str, template_name: str) -> Any:
        """
        获取特定类别的模板
        
        Args:
            category: 模板类别 (agent, tool, system)
            template_name: 模板名称
            
        Returns:
            模板内容
        """
        category_map = {
            "agent": ["react_system_prompt", "user_analysis_prompt", "memory_summary_prompt", 
                     "question_templates", "explanation_evaluation", "role_definitions"],
            "tool": ["tool_errors", "tool_help", "mindmap_templates", "flowchart_templates",
                    "api_responses", "tool_status"],
            "system": ["system_roles", "output_formats", "evaluation_criteria", 
                      "conversation_flows", "error_handling", "learning_scenarios"]
        }
        
        if category not in category_map:
            raise ValueError(f"不支持的模板类别: {category}")
        
        if template_name not in category_map[category]:
            raise ValueError(f"模板 '{template_name}' 不在类别 '{category}' 中")
        
        return self._prompts_cache[template_name]
    
    def format_tool_error(self, error_type: str, **kwargs) -> str:
        """格式化工具错误消息"""
        if error_type not in tool_error_messages:
            return f"未知错误类型: {error_type}"
        
        try:
            return tool_error_messages[error_type].format(**kwargs)
        except KeyError as e:
            return f"错误消息格式化失败，缺少参数: {e}"
    
    def format_tool_help(self, tool_name: str) -> str:
        """获取工具帮助信息"""
        if tool_name not in tool_help_messages:
            return f"工具 '{tool_name}' 的帮助信息不存在"
        
        help_info = tool_help_messages[tool_name]
        return f"""
**{tool_name}**

{help_info['description']}

**用法**: {help_info['usage']}

**示例**: 
{chr(10).join(f"- {example}" for example in help_info.get('examples', []))}
"""
    
    def format_api_response(self, response_type: str, **kwargs) -> str:
        """格式化API响应"""
        if response_type not in api_response_templates:
            return f"未知响应类型: {response_type}"
        
        try:
            return api_response_templates[response_type].format(**kwargs)
        except KeyError as e:
            return f"响应格式化失败，缺少参数: {e}"
    
    def get_role_definition(self, role_name: str) -> Dict[str, Any]:
        """获取角色定义"""
        if role_name in system_role_definitions:
            return system_role_definitions[role_name]
        elif role_name in role_definitions:
            return role_definitions[role_name]
        else:
            raise ValueError(f"角色 '{role_name}' 不存在")
    
    def get_output_format(self, format_name: str) -> Dict[str, Any]:
        """获取输出格式模板"""
        if format_name not in output_format_templates:
            raise ValueError(f"输出格式 '{format_name}' 不存在")
        
        return output_format_templates[format_name]
    
    def get_evaluation_criteria(self, criteria_type: str) -> Dict[str, Any]:
        """获取评估标准"""
        if criteria_type not in evaluation_criteria:
            raise ValueError(f"评估标准 '{criteria_type}' 不存在")
        
        return evaluation_criteria[criteria_type]
    
    def get_conversation_template(self, phase: str) -> Dict[str, str]:
        """获取对话阶段模板"""
        if phase not in conversation_flow_templates:
            raise ValueError(f"对话阶段 '{phase}' 不存在")
        
        return conversation_flow_templates[phase]
    
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """列出所有可用的提示词"""
        if category is None:
            return list(self._prompts_cache.keys())
        
        category_prefixes = {
            "agent": ["react_", "user_", "memory_", "question_", "explanation_", "role_"],
            "tool": ["tool_", "mindmap_", "flowchart_", "api_"],
            "system": ["system_", "output_", "evaluation_", "conversation_", "error_", "learning_"]
        }
        
        if category not in category_prefixes:
            return []
        
        return [key for key in self._prompts_cache.keys() 
                if any(key.startswith(prefix) for prefix in category_prefixes[category])]
    
    def search_prompts(self, keyword: str) -> List[str]:
        """搜索包含关键词的提示词"""
        results = []
        keyword_lower = keyword.lower()
        
        for key, value in self._prompts_cache.items():
            if keyword_lower in key.lower():
                results.append(key)
            elif isinstance(value, str) and keyword_lower in value.lower():
                results.append(key)
            elif isinstance(value, dict):
                if any(keyword_lower in str(v).lower() for v in value.values()):
                    results.append(key)
        
        return results
    
    def validate_prompt_parameters(self, prompt_key: str, parameters: Dict[str, Any]) -> bool:
        """验证提示词参数是否完整"""
        if prompt_key not in self._prompts_cache:
            return False
        
        template = self._prompts_cache[prompt_key]
        if not isinstance(template, str):
            return True
        
        try:
            template.format(**parameters)
            return True
        except KeyError:
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取提示词管理器元数据"""
        return {
            **self._metadata,
            "categories": {
                "agent_prompts": len(self.list_prompts("agent")),
                "tool_prompts": len(self.list_prompts("tool")),
                "system_prompts": len(self.list_prompts("system"))
            }
        }
    
    def export_prompts(self, filepath: Optional[str] = None) -> str:
        """导出所有提示词到JSON文件"""
        export_data = {
            "metadata": self.get_metadata(),
            "prompts": {}
        }
        
        # 处理不可序列化的对象
        for key, value in self._prompts_cache.items():
            if isinstance(value, (str, dict, list)):
                export_data["prompts"][key] = value
            else:
                export_data["prompts"][key] = str(value)
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def reload_prompts(self):
        """重新加载所有提示词"""
        self._prompts_cache.clear()
        self._templates_cache.clear()
        self._load_all_prompts()
        self._metadata["last_loaded"] = datetime.now().isoformat()

# 全局提示词管理器实例
prompt_manager = PromptManager()

# 便捷函数
def get_prompt(prompt_key: str, **kwargs) -> str:
    """获取格式化的提示词"""
    return prompt_manager.get_prompt(prompt_key, **kwargs)

def get_tool_error(error_type: str, **kwargs) -> str:
    """获取格式化的工具错误消息"""
    return prompt_manager.format_tool_error(error_type, **kwargs)

def get_tool_help(tool_name: str) -> str:
    """获取工具帮助信息"""
    return prompt_manager.format_tool_help(tool_name)

def get_api_response(response_type: str, **kwargs) -> str:
    """获取格式化的API响应"""
    return prompt_manager.format_api_response(response_type, **kwargs)

def get_role_definition(role_name: str) -> Dict[str, Any]:
    """获取角色定义"""
    return prompt_manager.get_role_definition(role_name)

def search_prompts(keyword: str) -> List[str]:
    """搜索提示词"""
    return prompt_manager.search_prompts(keyword)
