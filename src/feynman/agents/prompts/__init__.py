"""
费曼学习系统统一提示词管理模块

此模块集中管理所有的提示词模板，提供统一的访问接口。
将各种提示词按功能分类，便于维护和版本控制。
"""

from .agent_prompts import (
    react_system_prompt_template,
    react_prompt,
    user_analysis_prompt_template,
    memory_summary_prompt_template,
    question_generation_template
)

from .tool_prompts import (
    tool_error_messages,
    tool_help_messages,
    mindmap_output_templates,
    flowchart_output_templates
)

from .system_prompts import (
    system_role_definitions,
    output_format_templates,
    evaluation_criteria
)

__all__ = [
    # Agent核心提示词
    'react_system_prompt_template',
    'react_prompt', 
    'user_analysis_prompt_template',
    'memory_summary_prompt_template',
    'question_generation_template',
    
    # 工具相关提示词
    'tool_error_messages',
    'tool_help_messages',
    'mindmap_output_templates',
    'flowchart_output_templates',
    
    # 系统级提示词
    'system_role_definitions',
    'output_format_templates', 
    'evaluation_criteria'
]

# 版本信息
PROMPTS_VERSION = "3.2.0"
LAST_UPDATED = "2024-08-20"
