#!/usr/bin/env python3
"""
Python Traceroute - 非管理员版本
无需管理员权限，使用系统命令 + TCP 端口检测
同时显示路由跟踪和端口连通性
"""

import socket
import subprocess
import sys
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class TracerouteNoAdmin:
    """非管理员权限的 Traceroute 实现"""
    
    def __init__(self, destination, max_hops=30, timeout=2, tcp_port=80, 
                 enable_tcp_check=True):
        """
        初始化
        
        Args:
            destination: 目标主机
            max_hops: 最大跳数
            timeout: 超时时间
            tcp_port: TCP 端口
            enable_tcp_check: 是否启用 TCP 连通性检测
        """
        self.destination = destination
        self.max_hops = max_hops
        self.timeout = timeout
        self.tcp_port = tcp_port
        self.enable_tcp_check = enable_tcp_check
        self.dest_ip = None
        self.route_hops = {}  # 存储路由信息
        self.is_windows = sys.platform.startswith('win')
        
    def resolve_destination(self):
        """解析目标主机"""
        try:
            self.dest_ip = socket.gethostbyname(self.destination)
            return True
        except socket.gaierror as e:
            print(f"错误: 无法解析主机名 '{self.destination}': {e}")
            return False
    
    def test_tcp_port(self, ip, port=None):
        """
        测试 TCP 端口连通性
        
        Args:
            ip: 目标 IP
            port: 端口（默认使用 self.tcp_port）
            
        Returns:
            (是否可达, 响应时间ms, 状态描述)
        """
        if port is None:
            port = self.tcp_port
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            start_time = time.time()
            result = sock.connect_ex((ip, port))
            end_time = time.time()
            
            sock.close()
            
            rtt = (end_time - start_time) * 1000
            
            if result == 0:
                return True, rtt, "开放"
            else:
                # 连接被拒绝也说明主机可达
                if rtt < self.timeout * 1000:
                    return False, rtt, "关闭"
                else:
                    return False, None, "超时"
        except socket.timeout:
            return False, None, "超时"
        except Exception as e:
            return False, None, "不可达"
    
    def parse_traceroute_line(self, line):
        """
        解析 traceroute 输出行
        
        Returns:
            (hop_number, ip_addresses, rtts) 或 None
        """
        line = line.strip()
        
        if self.is_windows:
            # Windows tracert 格式: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
            match = re.match(r'\s*(\d+)\s+(.+)', line)
            if match:
                hop_num = int(match.group(1))
                rest = match.group(2)
                
                # 提取 IP 地址
                ip_match = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', rest)
                
                # 提取时间
                time_matches = re.findall(r'(\d+)\s*ms', rest)
                
                # 检查超时
                if '*' in rest or 'Request timed out' in rest or '请求超时' in rest:
                    return hop_num, [], []
                
                return hop_num, ip_match, time_matches
        else:
            # Unix traceroute 格式: " 1  192.168.1.1 (192.168.1.1)  1.234 ms  1.123 ms  1.056 ms"
            match = re.match(r'\s*(\d+)\s+(.+)', line)
            if match:
                hop_num = int(match.group(1))
                rest = match.group(2)
                
                # 提取 IP 地址
                ip_match = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', rest)
                
                # 提取时间
                time_matches = re.findall(r'([\d.]+)\s*ms', rest)
                
                # 检查超时
                if '*' in rest:
                    return hop_num, [], []
                
                return hop_num, ip_match, time_matches
        
        return None
    
    def run_traceroute(self):
        """运行 traceroute 命令并实时解析"""
        print(f"🔍 开始路由追踪: {self.destination} ({self.dest_ip})")
        print(f"📊 最大跳数: {self.max_hops}, 超时: {self.timeout}秒")
        
        if self.enable_tcp_check:
            print(f"🔌 TCP 端口检测: {self.tcp_port}")
        
        print("=" * 80)
        print()
        
        # 构建命令
        if self.is_windows:
            cmd = ['tracert', '-h', str(self.max_hops), 
                   '-w', str(int(self.timeout * 1000)), self.destination]
        else:
            cmd = ['traceroute', '-m', str(self.max_hops), 
                   '-w', str(self.timeout), '-q', '3', self.destination]
        
        print(f"执行: {' '.join(cmd)}\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时读取输出
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                parsed = self.parse_traceroute_line(line)
                if parsed:
                    hop_num, ips, rtts = parsed
                    
                    if ips:
                        # 存储路由信息
                        self.route_hops[hop_num] = {
                            'ip': ips[0] if ips else None,
                            'rtts': rtts
                        }
                        
                        # 显示路由信息
                        print(f"{hop_num:2d}  ", end='', flush=True)
                        
                        if ips:
                            print(f"{ips[0]:15s}  ", end='', flush=True)
                            
                            # 显示 RTT
                            if rtts:
                                rtt_str = '  '.join([f"{r} ms" for r in rtts[:3]])
                                print(f"{rtt_str:30s}", end='', flush=True)
                            
                            # TCP 端口检测
                            if self.enable_tcp_check:
                                reachable, tcp_rtt, status = self.test_tcp_port(ips[0])
                                
                                if reachable:
                                    print(f"  | TCP:{self.tcp_port} ✓ {tcp_rtt:.1f}ms", end='')
                                elif status == "关闭":
                                    print(f"  | TCP:{self.tcp_port} ✗ 关闭", end='')
                                else:
                                    print(f"  | TCP:{self.tcp_port} - {status}", end='')
                            
                            print(flush=True)
                        else:
                            print("*  *  *", flush=True)
                    else:
                        # 超时的跳
                        print(f"{hop_num:2d}  *  *  *  (请求超时)", flush=True)
                else:
                    # 显示其他信息行
                    if line.strip() and not line.startswith('traceroute'):
                        if 'Tracing' in line or '通过' in line or 'traceroute to' in line:
                            continue  # 跳过标题行
                        # print(line.strip())
            
            process.wait()
            
        except FileNotFoundError:
            print("\n❌ 错误: 找不到系统 traceroute 命令")
            if self.is_windows:
                print("Windows 应该自带 tracert 命令")
            else:
                print("请安装 traceroute:")
                print("  Ubuntu/Debian: sudo apt-get install traceroute")
                print("  CentOS/RHEL: sudo yum install traceroute")
                print("  macOS: 系统自带")
            return False
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断操作")
            process.terminate()
            return False
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            return False
        
        print()
        print("=" * 80)
        return True
    
    def run_final_tcp_test(self):
        """对目标主机进行最终的 TCP 端口测试"""
        if not self.enable_tcp_check:
            return
        
        print(f"\n🎯 目标主机 TCP 端口测试:")
        print(f"   主机: {self.destination} ({self.dest_ip})")
        print(f"   端口: {self.tcp_port}")
        
        reachable, rtt, status = self.test_tcp_port(self.dest_ip, self.tcp_port)
        
        if reachable:
            print(f"   状态: ✅ 端口开放")
            print(f"   响应时间: {rtt:.2f} ms")
        elif status == "关闭":
            print(f"   状态: ⚠️  端口关闭（但主机可达）")
        else:
            print(f"   状态: ❌ {status}")
    
    def trace(self):
        """执行完整的追踪"""
        if not self.resolve_destination():
            return False
        
        print("\n" + "=" * 80)
        print("  Python Traceroute - 非管理员模式")
        print("  路由追踪 + TCP 端口检测")
        print("=" * 80)
        print()
        
        # 运行 traceroute
        success = self.run_traceroute()
        
        if success:
            # 最终测试
            self.run_final_tcp_test()
        
        print()
        return success


def print_usage():
    """打印使用说明"""
    print("Python Traceroute - 非管理员版本")
    print("\n用法: python trace.py <目标主机> [选项]")
    print("\n选项:")
    print("  -m, --max-hops <数字>    最大跳数 (默认: 30)")
    print("  -t, --timeout <秒数>     超时时间 (默认: 2)")
    print("  -p, --port <端口>        TCP 检测端口 (默认: 80)")
    print("  --no-tcp                 禁用 TCP 端口检测")
    print("  -h, --help               显示此帮助信息")
    print("\n功能说明:")
    print("  • 使用系统 traceroute/tracert 命令进行路由追踪（ICMP）")
    print("  • 对每一跳进行 TCP 端口连通性检测")
    print("  • 无需管理员权限")
    print("  • 实时显示结果")
    print("\n示例:")
    print("  # 基本用法")
    print("  python trace.py www.baidu.com")
    print()
    print("  # 指定 TCP 端口")
    print("  python trace.py www.google.com -p 443")
    print()
    print("  # 仅路由追踪（不测试 TCP）")
    print("  python trace.py example.com --no-tcp")
    print()
    print("  # 完整参数")
    print("  python trace.py target.com -p 80 -m 20 -t 3")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    destination = None
    max_hops = 30
    timeout = 2
    tcp_port = 80
    enable_tcp = True
    
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
        elif arg in ['-p', '--port']:
            if i + 1 < len(sys.argv):
                try:
                    tcp_port = int(sys.argv[i + 1])
                    if not (1 <= tcp_port <= 65535):
                        raise ValueError
                    i += 2
                except ValueError:
                    print(f"错误: 无效的端口号 '{sys.argv[i + 1]}'")
                    sys.exit(1)
            else:
                print("错误: -p/--port 需要一个参数")
                sys.exit(1)
        elif arg == '--no-tcp':
            enable_tcp = False
            i += 1
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
    
    # 创建并运行 traceroute
    tracer = TracerouteNoAdmin(
        destination=destination,
        max_hops=max_hops,
        timeout=timeout,
        tcp_port=tcp_port,
        enable_tcp_check=enable_tcp
    )
    
    try:
        tracer.trace()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
