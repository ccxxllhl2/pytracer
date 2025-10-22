# Python Traceroute 实现

一个纯 Python 实现的 traceroute/tracert 工具，使用标准库构建，支持跨平台运行。

> 🎉 **无需管理员权限！** 普通用户即可直接使用 → [快速开始](QUICKSTART.md)

## 特性

✅ **跨平台支持** - Windows、Linux、macOS  
✅ **纯标准库** - 无需安装第三方依赖  
✅ **完整功能** - TTL 递增、ICMP 协议、超时控制  
✅ **可配置** - 最大跳数、超时时间、查询次数可调  
✅ **易用** - 命令行界面友好  
✅ **双模式** - 支持管理员模式和普通用户模式  
✅ **实时输出** - 每一跳结果立即显示，体验流畅  

## 系统要求

- **Python**: 3.12 或更高版本
- **权限**: 
  - **推荐**: 管理员/root权限（原始套接字，性能更好）
  - **支持**: 普通用户权限（调用系统命令）

## 原理说明

本程序实现了标准的 traceroute 功能：

1. **TTL 递增**: 从 TTL=1 开始，逐跳递增发送 ICMP Echo Request 数据包
2. **路由响应**: 当数据包 TTL 归零时，中间路由器返回 ICMP Time Exceeded 消息
3. **路径追踪**: 记录每一跳的 IP 地址、主机名和响应时间（RTT）
4. **到达检测**: 直到收到目标主机的 ICMP Echo Reply 或达到最大跳数

## 使用方法

### 🚀 方式一：智能模式（推荐）

**自动选择最佳实现，普通用户即可运行：**

```bash
# Windows - 直接运行（无需管理员权限）
python trace.py www.google.com

# Linux/macOS - 直接运行
python3 trace.py www.google.com

# 自定义参数
python trace.py baidu.com -m 15 -t 3
```

程序会自动检测权限并选择：
- ✅ 有管理员权限 → 使用高性能原始套接字实现
- ✅ 普通用户权限 → 使用系统命令封装实现

---

### 🔧 方式二：普通用户模式（无需管理员）

**适合没有管理员权限的环境：**

```bash
# Windows - 普通用户即可运行
python traceroute_nonadmin.py www.google.com

# Linux/macOS - 普通用户即可运行
python3 traceroute_nonadmin.py www.google.com

# 自定义参数
python traceroute_nonadmin.py 8.8.8.8 -m 20 -t 3
```

---

### ⚡ 方式三：高性能模式（需要管理员）

**原始套接字实现，性能最佳：**

#### Windows

```bash
# 以管理员身份运行命令提示符或 PowerShell
python traceroute.py www.google.com

# 指定最大跳数
python traceroute.py 8.8.8.8 -m 20

# 自定义超时和查询次数
python traceroute.py baidu.com -t 3 -q 2
```

#### Linux / macOS

```bash
# 使用 sudo 运行
sudo python3 traceroute.py www.google.com

# 或给予 Python 能力（推荐）
sudo setcap cap_net_raw+ep $(which python3)
python3 traceroute.py www.google.com
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--max-hops` | `-m` | 最大跳数 | 30 |
| `--timeout` | `-t` | 超时时间（秒） | 2 |
| `--queries` | `-q` | 每跳查询次数 | 3 |
| `--help` | `-h` | 显示帮助信息 | - |

## 输出示例

**实时输出效果** - 每一跳完成后立即显示，无需等待全部完成

```
traceroute to www.google.com (142.250.185.100), 30 hops max

 1  192.168.1.1  1.23 ms  1.10 ms  1.05 ms        ← 第1跳立即显示
 2  10.255.255.1  8.45 ms  7.89 ms  8.12 ms       ← 第2跳立即显示
 3  61.148.143.1  12.34 ms  11.98 ms  12.10 ms    ← 逐行实时显示
 4  202.97.33.106  15.67 ms  15.23 ms  *
 5  202.97.50.118  28.45 ms  28.12 ms  27.98 ms
 ...
12  142.250.185.100  35.23 ms  34.89 ms  35.01 ms

到达目标: www.google.com (142.250.185.100)
```

## 输出说明

- **数字**: 跳数（TTL 值）
- **IP/主机名**: 该跳路由器的地址
- **时间**: 往返时间（RTT），单位毫秒（ms）
- **星号(*)**: 该次查询超时，未收到响应

## 技术细节

### ICMP 数据包结构

```
ICMP Echo Request:
┌─────────┬──────┬──────────┬────────┬──────────┐
│  Type   │ Code │ Checksum │   ID   │ Sequence │
│ (8/1B)  │(0/1B)│  (2B)    │ (2B)   │  (2B)    │
└─────────┴──────┴──────────┴────────┴──────────┘
```

### 核心实现

1. **socket.SOCK_RAW**: 创建原始套接字
2. **socket.IPPROTO_ICMP**: 使用 ICMP 协议
3. **IP_TTL**: 设置 Time To Live 值
4. **struct**: 打包/解包二进制数据
5. **select**: 实现跨平台超时控制

## 常见问题

### Q: 没有管理员权限怎么办？

**A**: 使用普通用户模式：
```bash
# 方式一：智能模式（自动选择）
python trace.py www.google.com

# 方式二：直接使用普通用户模式
python traceroute_nonadmin.py www.google.com
```
无需任何特殊权限，直接运行即可！

### Q: 提示权限错误？

**A**: 如果使用 `traceroute.py` 提示权限错误，有两个选择：
1. **切换到普通用户模式**（推荐）：使用 `trace.py` 或 `traceroute_nonadmin.py`
2. **获取管理员权限**：
   - **Windows**: 右键"以管理员身份运行"命令提示符
   - **Linux/Mac**: 使用 `sudo` 运行

### Q: 为什么有些跳显示 `*` ？

**A**: 可能原因：
1. 路由器配置禁止 ICMP Time Exceeded 响应
2. 防火墙过滤了 ICMP 包
3. 网络超时或拥塞
4. 路由器优先级设置较低

### Q: Windows 防火墙拦截？

**A**: 
1. 确保以管理员身份运行
2. 检查 Windows Defender 防火墙规则
3. 临时关闭防火墙测试（不推荐）

### Q: 与系统 tracert/traceroute 结果不同？

**A**: 正常现象，可能原因：
- 网络路径动态变化（负载均衡）
- 查询时间点不同
- 协议实现细节差异（ICMP vs UDP vs TCP）

## 代码结构

```
pytracer/
├── trace.py                  # 智能入口（推荐使用）
├── traceroute_nonadmin.py   # 普通用户模式（无需管理员）
├── traceroute.py            # 高性能模式（需要管理员）
├── example.bat              # Windows 测试脚本
├── requirements.txt         # 依赖说明（仅标准库）
├── .gitignore              # Git 忽略文件
└── README.md               # 本文档
```

### 文件说明

1. **trace.py** - 智能入口脚本
   - 自动检测权限
   - 选择最佳实现方式
   - 推荐日常使用

2. **traceroute_nonadmin.py** - 普通用户模式
   - ✅ 无需管理员权限
   - 调用系统 tracert/traceroute 命令
   - 解析并美化输出

3. **traceroute.py** - 高性能模式
   - ⚡ 原始套接字实现
   - 完全自主的 ICMP 协议处理
   - 需要管理员/root权限

### 主要类和方法

#### traceroute.py (高性能模式)
- `Traceroute`: 核心类
  - `checksum()`: 计算 ICMP 校验和
  - `create_icmp_packet()`: 构造 ICMP 数据包
  - `parse_icmp_header()`: 解析 ICMP 响应
  - `send_probe()`: 发送探测包并接收响应
  - `trace()`: 执行完整的路径追踪

#### traceroute_nonadmin.py (普通用户模式)
- `TracerouteNonAdmin`: 核心类
  - `build_command()`: 构建系统命令
  - `parse_windows_output()`: 解析 Windows 输出
  - `parse_unix_output()`: 解析 Unix 输出
  - `trace()`: 执行路径追踪

## 许可证

本项目使用标准库实现，可自由使用和修改。

## 注意事项

⚠️ **仅供学习和合法网络诊断使用**  
⚠️ **请勿用于未授权的网络扫描或攻击**  
⚠️ **遵守当地法律法规和网络使用政策**

## 更新日志

### v1.0.0 (2025-10-22)
- ✅ 初始版本
- ✅ 实现基本 traceroute 功能
- ✅ 支持 Windows/Linux/macOS
- ✅ 命令行参数解析
- ✅ ICMP 协议实现
- ✅ 超时和重试机制

## 贡献

欢迎提交 Issue 和 Pull Request！

## 参考资料

- [RFC 792 - ICMP Protocol](https://tools.ietf.org/html/rfc792)
- [RFC 1122 - Internet Host Requirements](https://tools.ietf.org/html/rfc1122)
- [Traceroute - Wikipedia](https://en.wikipedia.org/wiki/Traceroute)

