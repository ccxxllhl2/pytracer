#!/usr/bin/env python3
"""
Python Traceroute Implementation
支持 Windows/Linux/macOS 跨平台
使用标准库实现完整的 traceroute 功能
"""

import socket
import struct
import time
import sys
import os
import select


class Traceroute:
    """Traceroute 实现类"""
    
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
        self.dest_ip = None
        self.identifier = os.getpid() & 0xFFFF  # 使用进程ID作为ICMP标识符
        
    def checksum(self, data):
        """
        计算 ICMP 校验和
        
        Args:
            data: 要计算校验和的数据
            
        Returns:
            16位校验和
        """
        # 确保数据长度为偶数
        if len(data) % 2 != 0:
            data += b'\x00'
        
        # 按16位分组求和
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word
        
        # 处理进位
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)
        
        # 取反
        return ~checksum & 0xFFFF
    
    def create_icmp_packet(self, sequence):
        """
        创建 ICMP Echo Request 数据包
        
        Args:
            sequence: 序列号
            
        Returns:
            ICMP数据包（bytes）
        """
        # ICMP Echo Request: Type=8, Code=0
        icmp_type = 8
        icmp_code = 0
        icmp_checksum = 0
        
        # ICMP Header: Type(1) + Code(1) + Checksum(2) + ID(2) + Sequence(2) = 8 bytes
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, 
                            self.identifier, sequence)
        
        # 添加时间戳作为数据部分
        data = struct.pack('!d', time.time())
        
        # 计算校验和
        icmp_checksum = self.checksum(header + data)
        
        # 重新打包，包含正确的校验和
        header = struct.pack('!BBHHH', icmp_type, icmp_code, 
                            socket.htons(icmp_checksum), self.identifier, sequence)
        
        return header + data
    
    def parse_icmp_header(self, data):
        """
        解析 ICMP 头部
        
        Args:
            data: 接收到的数据包
            
        Returns:
            (icmp_type, icmp_code, icmp_id, icmp_seq) 或 None
        """
        # IP头部至少20字节
        if len(data) < 28:  # IP header(20) + ICMP header(8)
            return None
        
        # 跳过IP头部（20字节）
        icmp_header = data[20:28]
        
        icmp_type, icmp_code, checksum, packet_id, sequence = struct.unpack(
            '!BBHHH', icmp_header
        )
        
        return icmp_type, icmp_code, packet_id, sequence
    
    def get_hostname(self, ip_address):
        """
        获取IP地址的主机名（反向DNS查询）
        
        Args:
            ip_address: IP地址字符串
            
        Returns:
            主机名或IP地址
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return f"{hostname} ({ip_address})"
        except socket.herror:
            return ip_address
    
    def resolve_destination(self):
        """解析目标主机名为IP地址"""
        try:
            self.dest_ip = socket.gethostbyname(self.destination)
            print(f"traceroute to {self.destination} ({self.dest_ip}), "
                  f"{self.max_hops} hops max\n")
            return True
        except socket.gaierror as e:
            print(f"错误: 无法解析主机名 '{self.destination}': {e}")
            return False
    
    def send_probe(self, ttl, sequence):
        """
        发送一个探测包
        
        Args:
            ttl: Time To Live 值
            sequence: 序列号
            
        Returns:
            (响应时间(ms), 响应IP地址, 是否到达目标) 或 (None, None, False)
        """
        # 创建发送和接收socket
        try:
            # Windows使用IPPROTO_ICMP，Linux/Mac使用IPPROTO_ICMP也可以
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 
                                       socket.IPPROTO_ICMP)
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 
                                       socket.IPPROTO_ICMP)
        except PermissionError:
            print("\n错误: 需要管理员/root权限来创建原始套接字")
            print("Windows: 请以管理员身份运行")
            print("Linux/Mac: 请使用 sudo 运行")
            sys.exit(1)
        except OSError as e:
            print(f"\n错误: 无法创建套接字: {e}")
            sys.exit(1)
        
        # 设置TTL
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        
        # 设置接收超时
        recv_socket.settimeout(self.timeout)
        
        # 创建并发送ICMP包
        packet = self.create_icmp_packet(sequence)
        send_time = time.time()
        
        try:
            send_socket.sendto(packet, (self.dest_ip, 1))
        except Exception as e:
            send_socket.close()
            recv_socket.close()
            return None, None, False
        
        # 等待响应
        try:
            # 使用select进行超时控制（跨平台）
            ready = select.select([recv_socket], [], [], self.timeout)
            
            if ready[0]:
                data, addr = recv_socket.recvfrom(1024)
                recv_time = time.time()
                
                # 解析ICMP响应
                icmp_info = self.parse_icmp_header(data)
                
                if icmp_info:
                    icmp_type, icmp_code, packet_id, packet_seq = icmp_info
                    
                    # ICMP Echo Reply (Type 0) - 到达目标
                    if icmp_type == 0 and packet_id == self.identifier:
                        rtt = (recv_time - send_time) * 1000  # 转换为毫秒
                        send_socket.close()
                        recv_socket.close()
                        return rtt, addr[0], True
                    
                    # ICMP Time Exceeded (Type 11) - 中间路由器
                    elif icmp_type == 11:
                        rtt = (recv_time - send_time) * 1000
                        send_socket.close()
                        recv_socket.close()
                        return rtt, addr[0], False
                
                # 收到响应但不是我们期望的包
                send_socket.close()
                recv_socket.close()
                return None, None, False
            else:
                # 超时
                send_socket.close()
                recv_socket.close()
                return None, None, False
                
        except socket.timeout:
            send_socket.close()
            recv_socket.close()
            return None, None, False
        except Exception as e:
            send_socket.close()
            recv_socket.close()
            return None, None, False
    
    def trace(self):
        """执行 traceroute"""
        if not self.resolve_destination():
            return
        
        reached_destination = False
        
        for ttl in range(1, self.max_hops + 1):
            # 打印跳数
            print(f"{ttl:2d}  ", end='', flush=True)
            
            responses = []
            current_ip = None
            
            # 发送多次查询
            for query in range(self.queries):
                sequence = ttl * 1000 + query
                rtt, ip_addr, is_destination = self.send_probe(ttl, sequence)
                
                if rtt is not None and ip_addr is not None:
                    responses.append(rtt)
                    if current_ip is None:
                        current_ip = ip_addr
                    
                    if is_destination:
                        reached_destination = True
                else:
                    responses.append(None)
            
            # 输出结果
            if current_ip:
                hostname = self.get_hostname(current_ip)
                print(f"{hostname}  ", end='')
                
                for rtt in responses:
                    if rtt is not None:
                        print(f"{rtt:.2f} ms  ", end='')
                    else:
                        print("*  ", end='')
                print()
                
                if reached_destination:
                    print(f"\n到达目标: {self.destination} ({self.dest_ip})")
                    break
            else:
                # 所有查询都超时
                print("*  *  *  (请求超时)")
        
        if not reached_destination:
            print(f"\n未能在 {self.max_hops} 跳内到达目标")


def print_usage():
    """打印使用说明"""
    print("用法: python traceroute.py <目标主机> [选项]")
    print("\n选项:")
    print("  -m, --max-hops <数字>    最大跳数 (默认: 30)")
    print("  -t, --timeout <秒数>     超时时间 (默认: 2)")
    print("  -q, --queries <数字>     每跳查询次数 (默认: 3)")
    print("  -h, --help               显示此帮助信息")
    print("\n示例:")
    print("  python traceroute.py www.google.com")
    print("  python traceroute.py 8.8.8.8 -m 20 -t 3")
    print("  python traceroute.py baidu.com --max-hops 15 --queries 2")


def main():
    """主函数"""
    # 检查是否为Windows系统
    is_windows = sys.platform.startswith('win')
    
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
    
    # Windows权限提示
    if is_windows:
        print("提示: 在Windows上运行需要管理员权限")
        print("如果出现权限错误，请以管理员身份运行命令提示符\n")
    
    # 创建并运行 traceroute
    tracer = Traceroute(destination, max_hops=max_hops, 
                       timeout=timeout, queries=queries)
    
    try:
        tracer.trace()
    except KeyboardInterrupt:
        print("\n\n中断: 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

