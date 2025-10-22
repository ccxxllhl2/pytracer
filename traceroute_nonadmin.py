#!/usr/bin/env python3
"""
Python Traceroute Implementation (Non-Admin Version)
无需管理员权限的 Traceroute 实现
通过调用系统命令并解析输出来实现跨平台支持
"""

import subprocess
import sys
import re
import platform


class TracerouteNonAdmin:
    """无需管理员权限的 Traceroute 实现"""
    
    def __init__(self, destination, max_hops=30, timeout=2, queries=3):
        """
        初始化 Traceroute
        
        Args:
            destination: 目标主机名或IP地址
            max_hops: 最大跳数，默认30
            timeout: 每次查询超时时间（秒），默认2
            queries: 每一跳的查询次数，默认3
        """
        self.destination = destination
        self.max_hops = max_hops
        self.timeout = timeout
        self.queries = queries
        self.os_type = platform.system().lower()
        
    def build_command(self):
        """
        根据操作系统构建 traceroute 命令
        
        Returns:
            命令列表
        """
        if self.os_type == 'windows':
            # Windows: tracert
            cmd = ['tracert']
            cmd.extend(['-h', str(self.max_hops)])  # 最大跳数
            cmd.extend(['-w', str(self.timeout * 1000)])  # 超时（毫秒）
            cmd.append(self.destination)
            return cmd
        
        elif self.os_type in ['linux', 'darwin']:
            # Linux/macOS: traceroute
            cmd = ['traceroute']
            cmd.extend(['-m', str(self.max_hops)])  # 最大跳数
            cmd.extend(['-w', str(self.timeout)])  # 超时（秒）
            cmd.extend(['-q', str(self.queries)])  # 查询次数
            cmd.append(self.destination)
            return cmd
        
        else:
            raise OSError(f"不支持的操作系统: {self.os_type}")
    
    def process_line_realtime(self, line, is_first_line):
        """
        实时处理输出行
        
        Args:
            line: 输出行
            is_first_line: 是否是第一行
        """
        line = line.strip()
        
        # 跳过空行
        if not line:
            return
        
        if self.os_type == 'windows':
            # Windows tracert 输出处理
            if line.startswith('Tracing') or line.startswith('通过') or line.startswith('跟踪'):
                # 显示目标信息
                print(line)
                print("=" * 70)
            elif line.startswith('over') or line.startswith('最多') or '跃点' in line:
                # 跳过 "over a maximum of" 行
                return
            elif line.startswith('Trace complete') or line.startswith('跟踪完成'):
                # 完成信息
                print("=" * 70)
                print(line)
            else:
                # 解析跳数行
                # 格式: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
                # 或: "  2     *        *        *     Request timed out."
                hop_match = re.match(r'\s*(\d+)', line)
                if hop_match:
                    print(line)
        else:
            # Unix traceroute 输出处理
            if is_first_line:
                print("=" * 70)
            print(line)
    
    def trace(self):
        """执行 traceroute（实时输出）"""
        try:
            # 构建命令
            cmd = self.build_command()
            
            print(f"\n执行命令: {' '.join(cmd)}")
            print(f"目标: {self.destination}")
            print(f"最大跳数: {self.max_hops}, 超时: {self.timeout}秒")
            print()
            
            # 使用 Popen 实现实时输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8' if self.os_type == 'windows' else None,
                errors='ignore',  # 忽略编码错误
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            
            is_first_line = True
            
            # 实时读取并显示输出
            while True:
                line = process.stdout.readline()
                
                if not line:
                    # 没有更多输出，检查进程是否结束
                    if process.poll() is not None:
                        break
                    continue
                
                # 实时处理并显示每一行
                self.process_line_realtime(line, is_first_line)
                is_first_line = False
            
            # 等待进程结束
            process.wait()
            
            # 如果没有 stdout 输出，检查 stderr
            if is_first_line:
                stderr_output = process.stderr.read()
                if stderr_output:
                    print("错误输出:")
                    print(stderr_output)
                else:
                    print("错误: 没有收到输出")
                return
            
            # Unix 系统在最后添加分隔线
            if self.os_type != 'windows':
                print("=" * 70)
            
            # 检查返回码
            if process.returncode not in [0, 1]:
                print(f"\n警告: 命令返回码 {process.returncode}")
            
        except FileNotFoundError:
            print(f"\n错误: 找不到 traceroute 命令")
            if self.os_type == 'windows':
                print("请确保系统已安装 tracert 命令（Windows 自带）")
            else:
                print("请安装 traceroute:")
                print("  Ubuntu/Debian: sudo apt-get install traceroute")
                print("  CentOS/RHEL: sudo yum install traceroute")
                print("  macOS: 系统自带，如缺失请使用 brew install traceroute")
        
        except KeyboardInterrupt:
            print("\n\n用户中断操作")
            if 'process' in locals():
                process.terminate()
                process.wait()
        
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()


def print_usage():
    """打印使用说明"""
    print("用法: python traceroute_nonadmin.py <目标主机> [选项]")
    print("\n选项:")
    print("  -m, --max-hops <数字>    最大跳数 (默认: 30)")
    print("  -t, --timeout <秒数>     超时时间 (默认: 2)")
    print("  -q, --queries <数字>     每跳查询次数 (默认: 3, 仅Unix)")
    print("  -h, --help               显示此帮助信息")
    print("\n示例:")
    print("  python traceroute_nonadmin.py www.google.com")
    print("  python traceroute_nonadmin.py 8.8.8.8 -m 20 -t 3")
    print("  python traceroute_nonadmin.py baidu.com --max-hops 15")
    print("\n说明:")
    print("  本工具无需管理员权限，通过调用系统 tracert/traceroute 命令实现")
    print("  Windows: 使用 tracert 命令")
    print("  Linux/macOS: 使用 traceroute 命令")


def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    destination = None
    max_hops = 30
    timeout = 2
    queries = 3
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg in ['-h', '--help']:
            print_usage()
            sys.exit(0)
        elif arg in ['-m', '--max-hops']:
            if i + 1 < len(sys.argv):
                try:
                    max_hops = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f"错误: 无效的最大跳数值 '{sys.argv[i + 1]}'")
                    sys.exit(1)
            else:
                print("错误: -m/--max-hops 需要一个参数")
                sys.exit(1)
        elif arg in ['-t', '--timeout']:
            if i + 1 < len(sys.argv):
                try:
                    timeout = float(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f"错误: 无效的超时值 '{sys.argv[i + 1]}'")
                    sys.exit(1)
            else:
                print("错误: -t/--timeout 需要一个参数")
                sys.exit(1)
        elif arg in ['-q', '--queries']:
            if i + 1 < len(sys.argv):
                try:
                    queries = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f"错误: 无效的查询次数值 '{sys.argv[i + 1]}'")
                    sys.exit(1)
            else:
                print("错误: -q/--queries 需要一个参数")
                sys.exit(1)
        elif arg.startswith('-'):
            print(f"错误: 未知选项 '{arg}'")
            print_usage()
            sys.exit(1)
        else:
            if destination is None:
                destination = arg
                i += 1
            else:
                print(f"错误: 多余的参数 '{arg}'")
                print_usage()
                sys.exit(1)
    
    if destination is None:
        print("错误: 未指定目标主机")
        print_usage()
        sys.exit(1)
    
    # 系统信息
    os_type = platform.system()
    print(f"\n检测到操作系统: {os_type}")
    print(f"✓ 本工具无需管理员权限")
    
    # 创建并运行 traceroute
    tracer = TracerouteNonAdmin(destination, max_hops=max_hops, 
                                timeout=timeout, queries=queries)
    
    try:
        tracer.trace()
    except KeyboardInterrupt:
        print("\n\n中断: 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

