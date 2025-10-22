#!/usr/bin/env python3
"""
Python Traceroute - 智能入口
自动选择合适的实现方式（管理员模式或普通用户模式）
"""

import sys
import os
import ctypes
import platform


def is_admin():
    """
    检查是否有管理员/root权限
    
    Returns:
        True if admin, False otherwise
    """
    try:
        if platform.system().lower() == 'windows':
            # Windows: 检查是否是管理员
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix: 检查是否是 root (uid=0)
            return os.getuid() == 0
    except:
        return False


def can_create_raw_socket():
    """
    尝试创建原始套接字以测试权限
    
    Returns:
        True if can create, False otherwise
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.close()
        return True
    except (PermissionError, OSError):
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("Python Traceroute - 智能启动")
    print("=" * 70)
    
    # 检查权限
    has_admin = is_admin()
    can_use_raw = can_create_raw_socket()
    
    print(f"\n系统: {platform.system()} {platform.release()}")
    print(f"管理员权限: {'✓ 是' if has_admin else '✗ 否'}")
    print(f"原始套接字权限: {'✓ 可用' if can_use_raw else '✗ 不可用'}")
    
    # 决定使用哪个实现
    if can_use_raw:
        print("\n→ 使用高性能模式（原始套接字实现）")
        print("-" * 70)
        
        # 导入并运行原始套接字版本
        try:
            from traceroute import main as traceroute_main
            traceroute_main()
        except ImportError:
            print("\n错误: 找不到 traceroute.py 模块")
            print("请确保 traceroute.py 文件存在")
            sys.exit(1)
    else:
        print("\n→ 使用兼容模式（系统命令封装）")
        print("  提示: 以管理员身份运行可获得更好的性能和功能")
        print("-" * 70)
        
        # 导入并运行系统命令版本
        try:
            from traceroute_nonadmin import main as traceroute_nonadmin_main
            traceroute_nonadmin_main()
        except ImportError:
            print("\n错误: 找不到 traceroute_nonadmin.py 模块")
            print("请确保 traceroute_nonadmin.py 文件存在")
            sys.exit(1)


if __name__ == "__main__":
    main()

