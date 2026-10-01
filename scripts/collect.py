#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""电脑体检采集器：输出 CPU 负载/内存/磁盘占用概览，并与上次基线对比列出变化项。"""
import json, os, platform, socket, time
from opschart import render_bar

_CACHE = os.path.expanduser("~/.cache/syscheck")
_BASE = os.path.join(_CACHE, "baseline.json")
_SYS = platform.system()
_ROOT = os.environ.get("SystemDrive", "C:") + "\\" if _SYS == "Windows" else "/"


def _disk_mb():
    """磁盘总量/可用（MB）。Windows 用 shutil，其余走 statvfs。"""
    if _SYS == "Windows":
        import shutil
        du = shutil.disk_usage(_ROOT)
        return du.total // (1024 ** 2), du.free // (1024 ** 2)
    st = os.statvfs("/")
    return st.f_blocks * st.f_frsize // (1024 ** 2), st.f_bavail * st.f_frsize // (1024 ** 2)


def _mem_mb():
    """内存总量/可用（MB）。Linux=/proc，macOS=sysctl+vm_stat，Windows=GlobalMemoryStatusEx。"""
    if _SYS == "Linux":
        mem = {}
        try:
            for line in open("/proc/meminfo"):
                k, _, v = line.partition(":")
                mem[k.strip()] = v.split()[0]
        except OSError:
            pass
        return int(mem.get("MemTotal", 0)) // 1024, int(mem.get("MemAvailable", 0)) // 1024
    if _SYS == "Darwin":
        try:
            import subprocess
            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()) // (1024 ** 2)
            ps, free = 4096, 0
            vm = subprocess.check_output(["vm_stat"]).decode("utf-8", "replace")
            for line in vm.splitlines():
                if "page size of" in line:
                    ps = int(line.split()[-2])
                if line.startswith("Pages free") or line.startswith("Pages inactive"):
                    free += int(line.split()[-1].rstrip(".")) * ps
            return total, free // (1024 ** 2)
        except Exception:
            return 0, 0
    if _SYS == "Windows":
        try:
            import ctypes
            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = _MS(); m.dwLength = ctypes.sizeof(_MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys // (1024 ** 2), m.ullAvailPhys // (1024 ** 2)
        except Exception:
            return 0, 0
    return 0, 0


def _load1():
    try:
        return round(os.getloadavg()[0], 2)
    except Exception:
        return 0.0


def _collect():
    total, free = _disk_mb()
    mem_total, mem_avail = _mem_mb()
    return {
        "ts": int(time.time()),
        "host": socket.gethostname(),
        "sys": "%s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
        "disk_total_mb": total,
        "disk_free_mb": free,
        "mem_total_mb": mem_total,
        "mem_avail_mb": mem_avail,
        "load1": _load1(),
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

    user = os.environ.get("USERNAME") or os.environ.get("USER", "?")
    print("== 电脑体检报告 ==")
    print("主机名   : %s" % cur["host"])
    print("系统     : %s" % cur["sys"])
    print("当前用户 : %s" % user)
    print("负载     : %.2f" % cur["load1"])
    print("内存     : %d MB 总 / %d MB 可用 %s"
          % (cur["mem_total_mb"], cur["mem_avail_mb"], render_bar(mem_pct)))
    print("磁盘(%s)  : %d MB 已用 / %d MB 可用 %s"
          % (_ROOT, cur["disk_total_mb"] - cur["disk_free_mb"], cur["disk_free_mb"], render_bar(disk_pct)))
    print("相对上次 :")
    for c in changes:
        print("  - %s" % c)
    print("== 报告结束 ==")


if __name__ == "__main__":
    report()
