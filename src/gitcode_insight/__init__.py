# -*- coding: utf-8 -*-
"""
GitCode Insight - GitCode 平台代码洞察工具
"""

__version__ = "0.1.0"
__author__ = "GitCode Insight Team"

from .community import GitCodeCommunityStats
from .issue import GitCodeIssueInsight
from .dashboard import generate_dashboard, generate_markdown_file

__all__ = [
    "GitCodeCommunityStats",
    "GitCodeIssueInsight",
    "generate_dashboard",
    "generate_markdown_file",
]