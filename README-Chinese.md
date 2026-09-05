# DDOS-Attack 分布式拒绝服务攻击模拟工具

## 严格的法律与道德警告

- 本项目仅用于教育目的！ 它旨在帮助安全研究人员、网络管理员和学生理解 DDOS 攻击的原理，以便更好地设计防御策略。
- 未经授权对任何非你个人拥有的服务器、网络或设备发起攻击是严重的犯罪行为，将受到法律严惩。
- 请确保你只在拥有完全控制权的隔离实验环境（例如本地虚拟机、自建测试网络）中运行此代码。 作者对任何不当使用不承担任何责任。

---

## 项目简介

DDOS-Attack 是一个跨平台的高性能 DDOS 模拟工具，支持 Python、Java 和 C语言 三种实现版本，能够向指定 IP 和端口发送 UDP 洪水数据包。所有版本均采用高性能优化设计，支持多线程/多进程、批量发送、随机端口等特性。

---

## 主要特性

### 通用特性

- 简洁的命令行交互界面 + 完整的命令行参数支持
- 可自定义目标 IP、端口、总流量（GB）、线程数、突发大小等参数
- 攻击前自动检测目标可达性（避免无效攻击）
- 实时进度条显示（发送进度、速率、剩余时间、丢包统计）
- 增量统计更新（减少锁竞争，提升高并发性能）
- 重试机制（仅针对 EAGAIN/EWOULDBLOCK 重试）
- 优雅停止（Ctrl+C 信号处理）
- 日志记录支持
- 艺术字启动界面（需要 figlet 支持）

### Python 版特性

- 跨平台支持（Windows/Linux/macOS/Android Termux）
- 多线程发送
- 跨平台清屏函数

### Java 版特性

- 阻塞式 DatagramChannel（可靠、简单）
- 预分配 SocketAddress 数组用于随机端口
- ThreadLocalRandom 快速随机
- LongAdder 低竞争统计
- BindException 降级处理

C 语言版特性

- Linux sendmmsg() 批量发送支持（单次系统调用发送多个包，大幅提升吞吐量）
- POSIX sockets + pthread 多线程
- 预分配 sockaddr_in 数组
- 原子操作统计（Interlocked/atomic）
- 高精度单调时钟计时
- 仅支持 Linux（Windows 版单独提供）

### Windows C 语言版特性

- Winsock2 + _beginthreadex 多线程
- 内置参数解析（不依赖 getopt）
- Interlocked 原子操作
- 预分配地址数组
- 支持 --no-prealloc 禁用预分配

---

## 项目结构

```
DDOS-Attack/
├── DDOS/
│   ├── Chinese/
│   │   ├── DDOS-Attack_01_c.py      → 攻击代码文件（完整版），中文
│   │   ├── DDOS-Attack_02_c.py      → 快捷版（省去艺术字体加载），中文
│   │   ├── DDOS-Attack_03_c.py      → 可伪造源 IP 版本（需 ROOT 权限），中文
│   │   ├── DDOS-Attack_05_c.c       → C 语言高性能版本，仅适用于 Windows ，中文
│   │   ├── DDOS-Attack_06_c.java    → Java 高性能版本，中文
│   │   └── DDOS-Attack_07_c.c       → C 语言高性能版本，仅适用于 Linux ，中文
│   └── English/
│        ├── DDOS-Attack_01_e.py      → 攻击代码文件（完整版），英文
│        ├── DDOS-Attack_02_e.py      → 快捷版（省去艺术字体加载），英文
│        └── DDOS-Attack_03_e.py      → 可伪造源 IP 版本（需 ROOT 权限），英文
├── Launcher/
│   ├── LauncherWindows.bat          → Windows 运行文件（自动安装依赖）
│   ├── LauncherPython.py            → Python 安卓运行文件（自动安装依赖）
│   └── LauncherLinux                → Linux 运行文件（自动安装依赖）
├── Art/
│   ├── Figlet_DDOS-Attack           → figlet 字体预览（DDOS-Attack）
│   └── Figlet_AttackStarting        → figlet 字体预览（Attack Starting）
├── README.md                        → 英文介绍
├── README-Chinese.md                → 中文介绍
├── LICENSE                          → 开源许可（GPLv3）
└── Nameplate                        → BC-809 铭牌
```

---

## 环境要求

### Python 版

- Python 3.6+（推荐 3.9+）
- 操作系统：Linux、Windows、macOS、Android（Termux）
- 依赖工具：git 用于克隆仓库，figlet 用于生成艺术字标题（可选）

### Java 版

- JDK 8+（推荐 JDK 11+）
- 操作系统：Linux、Windows、macOS
- 依赖工具：figlet 用于生成艺术字标题（可选）

### C 语言版（Linux）

- GCC 4.9+ 或 Clang
- 操作系统：Linux（内核 3.0+ 以支持 sendmmsg）
- 依赖工具：figlet 用于生成艺术字标题（可选）

### C 语言版（Windows）

- MinGW-w64 或 Microsoft Visual Studio
- 操作系统：Windows 7+
- 依赖工具：figlet 用于生成艺术字标题（可选）

---

## 命令行参数

所有版本均支持以下通用参数：

参数 说明 默认值
- -t, --target 目标 IP 地址 必填
- -p, --port 目标 UDP 端口 必填
- -g, --gb 总流量（GB） 必填
- -P, --processes 线程数/进程数 4
- -T, --threads 同 -P -
- -b, --burst 每突发包数 50
- -r, --rate 速率限制（秒/突发） 0（不限速）
- -d, --duration 攻击持续时间（秒） 0（直到发完）
- -s, --src-port 源端口基数 -1（随机）
- --size 包大小（字节） 1490
- --random-port 随机目标端口 关闭
- --log 日志文件路径 无
- --no-interactive 跳过确认 关闭
- --max-retries 最大重试次数 3
- --no-prealloc 禁用预分配（C/Java） 关闭
- -h, --help 显示帮助 -

---

## 性能对比

### 语言 平台 关键技术 预估 PPS（64 字节包）
- Python 跨平台 多线程 + asyncio 5万~8万
- Java 跨平台 多线程 + NIO 5万~10万
- C (Linux) Linux sendmmsg + 多进程 30万~50万
- C (Windows) Windows 多线程 + sendto 2万~5万

---

## 免责声明

- 本工具仅供学习和研究使用。使用者应遵守当地法律法规，不得将本工具用于任何非法用途。作者不对任何滥用行为承担法律责任。

---

## 开源协议

- 本仓库使用 GPLv3 作为开源协议。详见 LICENSE 文件。

---

## 贡献与反馈

- 欢迎提交 Issue 和 Pull Request。如有建议或问题，请通过 GitHub Issues 联系。

---

作者: BCU-0
GitHub: https://github.com/BC-809/DDOS-Attack
