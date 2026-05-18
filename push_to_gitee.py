import subprocess
import os

os.chdir(r'd:\fyglx')

print("=" * 60)
print("FitAI - Git推送工具")
print("=" * 60)

# 检查Git状态
print("\n[1] 检查Git配置...")
result = subprocess.run(['git', 'config', '--list'], capture_output=True, text=True)
if 'user.name' in result.stdout:
    print("Git配置正常")
else:
    print("配置Git用户...")
    subprocess.run(['git', 'config', '--global', 'user.name', 'FitAI'])
    subprocess.run(['git', 'config', '--global', 'user.email', 'fitai@example.com'])

# 检查远程仓库
print("\n[2] 检查远程仓库...")
result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
print(result.stdout)

# 添加文件
print("\n[3] 添加文件到暂存区...")
result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
print("已添加所有文件")

# 提交
print("\n[4] 提交代码...")
commit_msg = "FitAI商用级健身管理系统 v1.0"
result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
if result.returncode == 0:
    print(f"已提交: {commit_msg}")
else:
    print("提交失败或没有新内容")

# 推送
print("\n[5] 推送到Gitee...")
print("正在推送，请稍候...")
result = subprocess.run(
    ['git', 'push', '-u', 'origin', 'master', '--force'],
    capture_output=True,
    text=True,
    timeout=60
)

print("\n" + "=" * 60)
if result.returncode == 0:
    print("✓ 推送成功！")
    print("\n访问你的仓库: https://gitee.com/fengyigen/fitai")
else:
    print("✗ 推送失败！")
    print("\n错误信息:")
    print(result.stderr)
    print("\n可能的原因:")
    print("1. 仓库不存在或路径错误")
    print("2. 需要Gitee登录认证")
    print("3. 网络连接问题")
print("=" * 60)

input("\n按回车键退出...")
