---
name: pc-check
description: 电脑一键体检 — 输出 CPU 负载/内存/磁盘占用概览与相对上次的变化，适合装机后检查、日常看电脑状态。触发词: 电脑体检, 系统体检。
---

# /pc-check — 电脑一键体检

## 使用说明

1. 首次使用先建虚拟环境并安装依赖（Windows 下 `.venv/bin/` 换成 `.venv\Scripts\`）：

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. 运行体检脚本：

   ```bash
   .venv/bin/python scripts/collect.py
   ```

3. 把输出整理成一页小报告说给用户听（异常项放前面）。

## 说明

- 首次运行会在 `~/.cache/syscheck/` 建一个基线（baseline.json）；之后每次体检和基线对比，
  只列出变化项（内存/磁盘/负载的增减），一眼就能看出有没有异常趋势。
- 只读取信息，不改系统设置。
