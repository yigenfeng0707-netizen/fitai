"""
输入消毒与安全检查
- SQL 注入预防审计
- XSS 预防（剥离 HTML 标签）
- 路径遍历预防
"""
import os
import re
from html import escape, unescape


# ── XSS 预防 ──

# 匹配 HTML 标签的正则
_HTML_TAG_RE = re.compile(r"<[^>]*>")
# 匹配 HTML 实体
_HTML_ENTITY_RE = re.compile(r"&[#a-zA-Z0-9]+;")

# 危险 HTML 属性（事件处理器、javascript: 协议等）
_DANGEROUS_ATTR_RE = re.compile(
    r"""on\w+\s*=|javascript\s*:|vbscript\s*:|data\s*:\s*text/html""",
    re.IGNORECASE,
)


def strip_html(text: str) -> str:
    """
    剥离字符串中的 HTML 标签和危险内容。
    保留纯文本，将 HTML 实体解码后重新转义。
    """
    if not isinstance(text, str):
        return text
    # 先解码 HTML 实体，再剥离标签，最后转义
    text = unescape(text)
    text = _HTML_TAG_RE.sub("", text)
    text = _DANGEROUS_ATTR_RE.sub("", text)
    return text.strip()


def sanitize_string(text: str) -> str:
    """
    对字符串输入进行消毒：剥离 HTML 并转义特殊字符。
    """
    if not isinstance(text, str):
        return text
    cleaned = strip_html(text)
    return escape(cleaned)


def sanitize_dict(data: dict) -> dict:
    """递归消毒字典中的所有字符串值"""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [sanitize_string(v) if isinstance(v, str) else v for v in value]
        else:
            result[key] = value
    return result


# ── 路径遍历预防 ──

_PATH_TRAVERSAL_RE = re.compile(r"\.\.[/\\]")
_ILLEGAL_PATH_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

BASE_ALLOWED_DIR = "/tmp"  # 上传等操作的根目录


def is_safe_path(file_path: str, base_dir: str = BASE_ALLOWED_DIR) -> bool:
    """
    检查文件路径是否安全（防止路径遍历攻击）。
    """
    if not file_path or not isinstance(file_path, str):
        return False

    # 检查路径遍历模式
    if _PATH_TRAVERSAL_RE.search(file_path):
        return False

    # 检查非法字符
    if _ILLEGAL_PATH_CHARS_RE.search(file_path):
        return False

    # 规范化路径并确保在允许的目录内
    try:
        normalized = os.path.normpath(file_path)
        abs_path = os.path.abspath(normalized)
        abs_base = os.path.abspath(base_dir)
        return abs_path.startswith(abs_base + os.sep) or abs_path == abs_base
    except (OSError, ValueError):
        return False


# ── SQL 注入预防审计 ──

_SQL_INJECTION_PATTERNS = re.compile(
    r"""(?i)
    (\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|EXECUTE)\b
     .*(\b(FROM|INTO|WHERE|SET|TABLE|DATABASE)\b))
    |(\b(OR|AND)\s+\d+\s*=\s*\d+)
    |(--|;|/\*|\*/)
    |('(\s)*(OR|AND)(\s)*')
    """,
    re.VERBOSE,
)


def check_sql_injection_risk(text: str) -> bool:
    """
    检查字符串是否包含潜在的 SQL 注入模式。
    注意：这是辅助审计工具，不能替代 ORM 参数化查询。
    """
    if not isinstance(text, str):
        return False
    return bool(_SQL_INJECTION_PATTERNS.search(text))
