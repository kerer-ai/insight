# -*- coding: utf-8 -*-
"""
GitCode Insight - GitCode 平台代码洞察工具
"""

__version__ = "0.1.2"
__author__ = "GitCode Insight Team"

from .community import GitCodeCommunityStats
from .issue import GitCodeIssueInsight
from .pr import GitCodePRInsight
from .dashboard import generate_dashboard, generate_markdown_file
from .repo_stats import GitCodeRepoStats
from .report import GitCodeReport

__all__ = [
    "GitCodeCommunityStats",
    "GitCodeIssueInsight",
    "GitCodePRInsight",
    "generate_dashboard",
    "generate_markdown_file",
    "GitCodeRepoStats",
    "GitCodeReport",
]