# Python Traceroute - 非管理员版本

一个**无需管理员权限**的 Python traceroute 工具，提供路由追踪 + TCP 端口检测双重功能。

## ✨ 核心特性

- 🔓 **无需管理员权限** - 普通用户即可运行
- 🔍 **路由追踪** - 使用系统 traceroute/tracert (ICMP)
- 🔌 **TCP 端口检测** - 对每一跳测试 TCP 连通性
- 🎬 **实时输出** - 每一跳结果立即显示
- 🌍 **跨平台** - Windows / Linux / macOS
- 📦 **单文件** - 仅依赖 Python 标准库

## 🚀 快速开始

### 基本用法

```bash
# 最简单的方式
python3 trace.py www.baidu.com

# 指定 HTTPS 端口检测
python3 trace.py www.google.com -p 443

# 仅路由追踪（不测试 TCP）
python3 trace.py example.com --no-tcp
```

### 完整示例

```bash
# 追踪到百度，检测 HTTP 端口
python3 trace.py www.baidu.com -p 80

# 追踪到 GitHub，检测 HTTPS 端口
python3 trace.py github.com -p 443 -m 20

# 追踪到服务器，检测 SSH 端口
python3 trace.py server.example.com -p 22 -t 3
```

## 📖 命令行参数

```
python3 trace.py <目标主机> [选项]

必需:
  <目标>              目标主机名或 IP 地址

选项:
  -p, --port <端口>   TCP 检测端口 (默认: 80)
  -m, --max-hops <数> 最大跳数 (默认: 30)
  -t, --timeout <秒>  超时时间 (默认: 2)
  --no-tcp            禁用 TCP 端口检测
  -h, --help          显示帮助信息
```

## 💡 工作原理

### 1. 路由追踪（ICMP）

使用系统命令进行标准的 traceroute：
- **Windows**: 调用 `tracert` 命令
- **Linux/macOS**: 调用 `traceroute` 命令
- **协议**: ICMP Echo Request
- **权限**: 无需管理员（系统命令已有权限）

### 2. TCP 端口检测

对每一跳的路由器进行 TCP 连接测试：
- 使用标准 TCP socket（无需特殊权限）
- 测试指定端口的连通性
- 返回连接状态：开放 / 关闭 / 超时

### 3. 合并显示

实时显示两种检测结果：
```
1  192.168.1.1      1.2 ms  1.1 ms  1.0 ms  | TCP:80 ✗ 关闭
2  10.255.255.1     8.4 ms  7.9 ms  8.1 ms  | TCP:80 - 超时
3  61.148.143.1    12.3 ms 12.0 ms 12.1 ms  | TCP:80 ✓ 45.2ms
```

## 📊 输出示例

```
================================================================================
  Python Traceroute - 非管理员模式
  路由追踪 + TCP 端口检测
================================================================================

🔍 开始路由追踪: www.baidu.com (110.242.68.66)
📊 最大跳数: 30, 超时: 2秒
🔌 TCP 端口检测: 80
================================================================================

执行: traceroute -m 30 -w 2 -q 3 www.baidu.com

 1  192.168.1.1      1.234 ms  1.123 ms  1.056 ms  | TCP:80 ✗ 关闭
 2  10.255.255.1     8.456 ms  7.890 ms  8.123 ms  | TCP:80 - 超时
 3  61.148.143.1    12.345 ms 11.987 ms 12.101 ms  | TCP:80 - 超时
 4  202.97.33.106   15.678 ms 15.234 ms 16.012 ms  | TCP:80 - 超时
 5  202.97.50.118   28.456 ms 28.123 ms 27.987 ms  | TCP:80 - 超时
 ...
12  110.242.68.66   35.234 ms 34.890 ms 35.012 ms  | TCP:80 ✓ 35.5ms

================================================================================

🎯 目标主机 TCP 端口测试:
   主机: www.baidu.com (110.242.68.66)
   端口: 80
   状态: ✅ 端口开放
   响应时间: 35.23 ms
```

## 🎯 使用场景

### 场景 1: 网络诊断

```bash
# 检查到服务器的网络路径
python3 trace.py your-server.com

# 检查每一跳的延迟
python3 trace.py 8.8.8.8
```

### 场景 2: Web 服务检测

```bash
# 检测 HTTP 服务路径
python3 trace.py www.example.com -p 80

# 检测 HTTPS 服务路径
python3 trace.py www.example.com -p 443
```

### 场景 3: 服务器端口检测

```bash
# 检测 SSH 端口
python3 trace.py server.com -p 22

# 检测数据库端口
python3 trace.py db.server.com -p 3306

# 检测多个端口（多次运行）
python3 trace.py server.com -p 80
python3 trace.py server.com -p 443
python3 trace.py server.com -p 22
```

### 场景 4: 快速测试

```bash
# 限制 10 跳快速测试
python3 trace.py target.com -m 10

# 仅路由追踪，不测 TCP
python3 trace.py target.com --no-tcp
```

## 🔍 TCP 检测结果说明

| 状态 | 说明 | 显示 |
|------|------|------|
| **✓ 开放** | TCP 端口开放，连接成功 | `TCP:80 ✓ 35.5ms` |
| **✗ 关闭** | 主机可达，但端口关闭 | `TCP:80 ✗ 关闭` |
| **超时** | 连接超时，可能被防火墙阻止 | `TCP:80 - 超时` |
| **不可达** | 主机不可达 | `TCP:80 - 不可达` |

## 📌 常用端口

| 端口 | 服务 | 用途 |
|------|------|------|
| 80 | HTTP | Web 服务（默认） |
| 443 | HTTPS | 加密 Web 服务 |
| 22 | SSH | 远程登录 |
| 21 | FTP | 文件传输 |
| 25 | SMTP | 邮件发送 |
| 3306 | MySQL | 数据库 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存数据库 |
| 27017 | MongoDB | 文档数据库 |

## ❓ 常见问题

### Q: 需要管理员权限吗？
**A**: 不需要！程序使用系统命令进行路由追踪，TCP 检测使用标准 socket，都无需特殊权限。

### Q: 可以同时测试多个端口吗？
**A**: 当前版本一次只能测试一个端口，可以多次运行测试不同端口：
```bash
python3 trace.py target.com -p 80
python3 trace.py target.com -p 443
python3 trace.py target.com -p 22
```

### Q: 为什么有些跳的 TCP 显示超时？
**A**: 原因可能是：
1. 中间路由器不响应 TCP 连接（正常）
2. 防火墙屏蔽了该端口
3. 路由器不提供该服务

这是正常现象，只要目标主机能测试成功即可。

### Q: 如何只进行路由追踪？
**A**: 使用 `--no-tcp` 参数：
```bash
python3 trace.py target.com --no-tcp
```

### Q: Windows 上如何使用？
**A**: 完全相同的命令：
```bash
python trace.py target.com -p 80
```

### Q: 找不到 traceroute 命令？
**A**: 
- **Windows**: 系统自带 `tracert`，无需安装
- **Linux**: `sudo apt-get install traceroute` 或 `yum install traceroute`
- **macOS**: 系统自带

## 🔧 系统要求

- **Python**: 3.6+ (推荐 3.12+)
- **操作系统**: Windows 10+ / Linux / macOS
- **权限**: 普通用户权限
- **依赖**: 仅 Python 标准库
- **系统命令**: 
  - Windows: `tracert` (系统自带)
  - Linux/macOS: `traceroute` (可能需要安装)

## 📁 项目结构

```
pytracer/
├── trace.py              # 主程序（唯一核心文件）
├── README.md             # 本文档
├── requirements.txt      # 依赖说明（仅标准库）
└── examples.sh          # 使用示例（Linux/macOS）
```

## 🎨 技术特点

### 1. 无需权限方案

- **路由追踪**: 使用系统命令（已有权限）
- **TCP 检测**: 使用标准 socket.connect()（无需权限）
- **实时解析**: 解析系统命令输出

### 2. 双重检测

- **ICMP 层**: 网络层路径追踪
- **TCP 层**: 传输层端口连通性
- **合并显示**: 一目了然的结果

### 3. 实时输出

- 逐行解析 traceroute 输出
- 实时进行 TCP 检测
- 立即显示结果

## 💡 最佳实践

### 日常使用

```bash
# 推荐：自动测试常用端口
python3 trace.py target.com          # HTTP (80)
python3 trace.py target.com -p 443   # HTTPS
```

### 服务器诊断

```bash
# 完整检测
python3 trace.py server.com -p 22 -m 20 -t 3
```

### 批量测试脚本

```bash
#!/bin/bash
TARGET="your-server.com"

echo "测试 HTTP..."
python3 trace.py $TARGET -p 80 -m 15

echo ""
echo "测试 HTTPS..."
python3 trace.py $TARGET -p 443 -m 15

echo ""
echo "测试 SSH..."
python3 trace.py $TARGET -p 22 -m 15
```

## 🎉 快速开始

```bash
# 1. 测试百度
python3 trace.py www.baidu.com

# 2. 测试 GitHub (HTTPS)
python3 trace.py github.com -p 443

# 3. 测试 Google DNS
python3 trace.py 8.8.8.8

# 4. 查看帮助
python3 trace.py -h
```

## 🔒 安全提示

⚠️ **仅供合法用途**:
- ✅ 网络诊断和故障排查
- ✅ 自己服务器的连通性测试
- ✅ 学习和教育
- ❌ 未授权的网络扫描
- ❌ 端口扫描攻击

**请遵守当地法律法规！**

## 📝 许可证

MIT License - 可自由使用和修改

---

**立即开始！** 🚀

```bash
python3 trace.py www.google.com -p 443
```
