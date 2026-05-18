import os
import sys
import subprocess

def main():
    print("="*60)
    print("      FitAI - 健身/瑜伽/教培 AI智能管理系统")
    print("="*60)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("\n1. 安装依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt", "-q"], check=True)
    print("   ✅ 依赖安装完成")
    
    print("\n2. 初始化数据库...")
    subprocess.run([sys.executable, "-m", "scripts.init_db"], cwd="backend", check=True)
    print("   ✅ 数据库初始化完成")
    
    print("\n3. 初始化演示数据...")
    subprocess.run([sys.executable, "-m", "scripts.init_demo_data"], cwd="backend", check=True)
    print("   ✅ 演示数据初始化完成")
    
    print("\n4. 启动后端服务...")
    print("   服务地址: http://localhost:8000")
    print("   API文档: http://localhost:8000/docs")
    print("\n   测试账号:")
    print("     - admin / admin123 (超级管理员)")
    print("     - reception / 123456 (前台)")
    print("     - coach001 / 123456 (教练)")
    print("\n   按 Ctrl+C 停止服务")
    print("-"*60)
    
    os.chdir("backend")
    subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)