[English](README.md)

# DDOS-Attack    分布式拒绝服务攻击模拟工具

## 严格的法律与道德警告
 
- **本项目仅用于教育目的！** 它旨在帮助安全研究人员、网络管理员和学生理解 DDOS 攻击的原理，以便更好地设计防御策略。

- **未经授权对任何非你个人拥有的服务器、网络或设备发起攻击是严重的犯罪行为，将受到法律严惩。**
 
- **请确保你只在拥有完全控制权的隔离实验环境（例如本地虚拟机、自建测试网络）中运行此代码。** 作者对任何不当使用不承担任何责任。

---

## 项目简介

- `DDOS-Attack` 是一个基于 Python 的 DDOS 模拟脚本，能够向指定 IP 和端口发送 UDP 洪水数据包。

---

## 主要特性
- 简洁的命令行交互界面
- 可自定义目标 IP、端口和发包数量
- 攻击前自动检测目标可达性（避免无效攻击）
- 保留艺术字启动界面（需要 `figlet` 支持）

---

## 项目结构
- ├── DDOS/
- │ └──Chinese/
- │    └── DDOS-Attack_01_c.py → 攻击代码文件，中文
- │    └── DDOS-Attack_02_c.py → 快捷版(省去了艺术字体加载)，中文
- │    └── DDOS-Attack_03_c.py → 可伪造源 IP 的版本(需要 ROOT 权限)，中文
- │ └──English/
- │    └── DDOS-Attack_01_e.py → 攻击代码文件，英文
- │    └── DDOS-Attack_02_e.py → 快捷版(省去了艺术字体加载)，英文
- │    └── DDOS-Attack_03_e.py → 可伪造源 IP 的版本(需要 ROOT 权限)，英文
- ├── Launcher/
- │ └── 01_UseWindows.bat → Windows 运行文件(运行时安装所需文件并启动 01)
- │ └── 01_UsePython.py → Python 安卓运行文件(运行时安装所需文件并启动 01)
- │ └── 01_UseLinux → Linux 运行文件(运行时安装所需文件并启动 01)
- ├── Art/
- │ └── Nameplate → DDOS艺术字体
- │ └── Figlet → 代码中生成的 figlet 字体预览
- └── README.md → 英文介绍
- └── README–Chinese.md → 中文介绍
- └── LICENSE → 来源许可

---

## 环境要求

- **Python 3.6+**（推荐 3.9+）
- 操作系统：Linux、Windows、macOS、Android（Termux）
- 依赖工具：`git` 用于克隆仓库，`figlet` 用于生成艺术字标题

## 来源协议
– 本仓库使用`GPLv3`作为开源协议
