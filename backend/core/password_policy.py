"""
密码强度策略
- 最少 8 个字符
- 必须包含大写、小写、数字
- 禁止常见弱密码
"""
import re

# 常见弱密码列表
COMMON_PASSWORDS = frozenset({
    "password", "12345678", "123456789", "qwerty", "abc123",
    "password1", "iloveyou", "admin123", "welcome1", "1234567",
    "letmein", "1234567890", "monkey", "dragon", "master",
    "login", "princess", "qwerty123", "trustno1", "sunshine",
    "00000000", "11111111", "aaaaaaaa", "abcdefgh", "password123",
    "admin", "root", "test", "guest", "passw0rd",
    "123123123", "654321", "superman", "qazwsx", "michael",
    "000000", "111111", "123456", "123321", "666666",
    "888888", "abcdefg", "a1b2c3d4", "admin888", "password!",
})


class PasswordPolicyError(Exception):
    """密码不符合策略要求"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def validate_password_strength(password: str) -> list[str]:
    """
    验证密码强度，返回错误列表。
    空列表表示密码通过所有检查。
    """
    errors = []

    if not password or len(password) < 8:
        errors.append("密码长度不能少于8个字符")

    if not re.search(r"[A-Z]", password):
        errors.append("密码必须包含至少一个大写字母")

    if not re.search(r"[a-z]", password):
        errors.append("密码必须包含至少一个小写字母")

    if not re.search(r"\d", password):
        errors.append("密码必须包含至少一个数字")

    if password.lower() in COMMON_PASSWORDS:
        errors.append("密码过于常见，请使用更复杂的密码")

    # 检查是否为纯数字或纯字母
    if password.isdigit():
        errors.append("密码不能为纯数字")
    elif password.isalpha():
        errors.append("密码不能为纯字母")

    # 检查连续重复字符
    if len(password) >= 3:
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                errors.append("密码不能包含3个以上连续重复字符")
                break

    return errors


def enforce_password_policy(password: str) -> None:
    """
    强制执行密码策略，不符合则抛出异常。
    用于注册和修改密码端点。
    """
    errors = validate_password_strength(password)
    if errors:
        raise PasswordPolicyError("; ".join(errors))
