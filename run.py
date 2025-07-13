#!/usr/bin/env python3
"""
StudyHelper 启动脚本
"""

import sys
import os
import subprocess

def main():
    """主函数"""
    print("🚀 StudyHelper v2.0 启动器")
    print("=" * 40)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 检查依赖
    try:
        import streamlit
        print("✅ Streamlit 已安装")
    except ImportError:
        print("❌ 错误: 未安装Streamlit")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 选择应用版本
    print("\n请选择要运行的应用版本:")
    print("1. app_v2.py (推荐 - 角色化仪表盘)")
    print("2. app.py (原始版本)")
    
    choice = input("\n请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        app_path = "apps/app_v2.py"
        print("\n🎯 启动 app_v2.py (角色化仪表盘)...")
    elif choice == "2":
        app_path = "apps/app.py"
        print("\n🎯 启动 app.py (原始版本)...")
    else:
        print("❌ 无效选择，默认启动 app_v2.py")
        app_path = "apps/app_v2.py"
    
    # 检查文件是否存在
    if not os.path.exists(app_path):
        print(f"❌ 错误: 文件 {app_path} 不存在")
        sys.exit(1)
    
    # 启动应用
    try:
        print(f"🌐 启动Streamlit应用: {app_path}")
        print("📱 应用将在浏览器中打开")
        print("⏹️  按 Ctrl+C 停止应用")
        print("-" * 40)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            app_path, "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 