#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""服务器体检采集器：输出环境概览，并与上次基线对比列出变化项。"""
import json, os, platform, socket, time
from opschart import render_bar

_CACHE = os.path.expanduser("~/.cache/syscheck")
_BASE = os.path.join(_CACHE, "baseline.json")


def _collect():
    st = os.statvfs("/")
    total = st.f_blocks * st.f_frsize // (1024 ** 2)
    free = st.f_bavail * st.f_frsize // (1024 ** 2)
    mem = {}
    try:
        for line in open("/proc/meminfo"):
            k, _, v = line.partition(":")
            mem[k.strip()] = v.split()[0]
    except OSError:
        pass
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    return {
        "ts": int(time.time()),
        "host": socket.gethostname(),
        "sys": "%s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
        "disk_total_mb": total,
        "disk_free_mb": free,
        "mem_total_mb": int(mem.get("MemTotal", 0)) // 1024,
        "mem_avail_mb": int(mem.get("MemAvailable", 0)) // 1024,
        "load1": round(load[0], 2),
    }


def _baseline():
    try:
        with open(_BASE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _changes(cur, prev):
    """与基线对比，输出变化项（首次运行=建立基线）。"""
    if prev is None:
        return ["首次运行：已建立基线（后续巡检与本次对比）"]
    out = []
    for key, label, unit in (("disk_free_mb", "磁盘可用", "MB"),
                             ("mem_avail_mb", "内存可用", "MB")):
        d = cur[key] - prev.get(key, cur[key])
        if d:
            out.append("%s %+d %s" % (label, d, unit))
    dl = round(cur["load1"] - prev.get("load1", cur["load1"]), 2)
    if dl:
        out.append("负载(1m) %+.2f" % dl)
    age_h = (cur["ts"] - prev.get("ts", cur["ts"])) / 3600
    out.append("距上次巡检 %.1f 小时" % age_h)
    return out or ["与基线一致，无变化项"]


def _save_baseline(cur):
    try:
        os.makedirs(_CACHE, exist_ok=True)
        with open(_BASE, "w") as f:
            json.dump(cur, f)
    except OSError:
        pass


def report():
    cur = _collect()
    prev = _baseline()
    changes = _changes(cur, prev)
    _save_baseline(cur)

    mem_pct = 0
    if cur["mem_total_mb"]:
        mem_pct = (cur["mem_total_mb"] - cur["mem_avail_mb"]) * 100 // cur["mem_total_mb"]
    disk_pct = 0
    if cur["disk_total_mb"]:
        disk_pct = (cur["disk_total_mb"] - cur["disk_free_mb"]) * 100 // cur["disk_total_mb"]

    print("== 电脑体检报告 ==")
    print("主机名   : %s" % cur["host"])
    print("系统     : %s" % cur["sys"])
    print("当前用户 : %s" % os.environ.get("USER", "?"))
    print("负载     : %.2f" % cur["load1"])
    print("内存     : %d MB 总 / %d MB 可用 %s"
          % (cur["mem_total_mb"], cur["mem_avail_mb"], render_bar(mem_pct)))
    print("磁盘(/)  : %d MB 已用 / %d MB 可用 %s"
          % (cur["disk_total_mb"] - cur["disk_free_mb"], cur["disk_free_mb"], render_bar(disk_pct)))
    print("相对上次 :")
    for c in changes:
        print("  - %s" % c)
    print("== 报告结束 ==")


if __name__ == "__main__":
    report()
