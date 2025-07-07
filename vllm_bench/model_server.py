import paramiko, sys
import time, logging, uuid, re
import subprocess, threading
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .remote import SSHSession

_TEMPLATES = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))

def render(template_name: str, **ctx) -> str:
    return _TEMPLATES.get_template(template_name).render(**ctx)
#test
# def duplicate_keys(*dicts):
#     from collections import Counter
#     c = Counter(k for d in dicts for k in d)
#     return [k for k, v in c.items() if v > 1]

def extract_kfd_pids(text: str) -> list[str]:
    """
    从 ROCm SMI 日志中提取 “KFD Processes” 表格里的 PID 列。

    Parameters
    ----------
    text : str
        ROCm SMI 整段原始日志（不含行号）。

    Returns
    -------
    list[str]
        PID 字符串列表，按在日志中出现的顺序返回。
    """
    lines      = text.splitlines()
    pids       = []
    in_kfd_blk = False

    for line in lines:
        # 找到表头
        if "KFD process information" in line:
            in_kfd_blk = True
            continue

        # 遇到下一个分隔线说明表格结束
        if in_kfd_blk and line.startswith("="):
            break

        if in_kfd_blk:
            # 以若干空格 + 整数开头的行就是数据行
            m = re.match(r"\s*(\d+)\s+", line)
            if m:
                pids.append(m.group(1))

    return pids

def start_server(cfg: "GlobalCfg", combo: dict, ssh: SSHSession, out_dir: Path) -> str:
    """上传 + 后台 nohup 运行 server,返回远程脚本路径"""
    #test
    # d1, d2, d3 = cfg.docker.__dict__, cfg.model.__dict__, combo
    # print("重复的关键字有：", duplicate_keys(d1, d2, d3))
    
    print(cfg.docker.__dict__, "\n", cfg.model.__dict__, "\n", combo)
    #script = render("server_test.sh.j2", docker=cfg.docker.__dict__, model=cfg.model.__dict__, combo=combo)
    script = render("server_test.sh.j2", **combo)
    local_file = out_dir / f"server_{uuid.uuid4().hex}.sh"
    local_file.write_text(script)
    remote_file = f"/tmp/server_script/{local_file.name}"
    ssh.upload(local_file, remote_file)
    ssh.exec(f"chmod +x {remote_file}")
    # # 使用 nohup 让其后台运行
    # ssh.exec(f"nohup bash {remote_file} > {remote_file}.log 2>&1 &", get_pty=True)
    #ssh.exec(f"bash {remote_file} > {remote_file}.log 2>&1", get_pty=True)
    #ssh.exec(f"nohup bash {remote_file}")
    threading.Thread(
        target=ssh.exec,
        args=(f"bash {remote_file} > {remote_file}.log 2>&1",),
        kwargs={"get_pty": True},
        daemon=True
    ).start()
    print(remote_file)
    return remote_file

def stop_server(ssh: SSHSession, log):
    with open(log, encoding='utf-8') as f:
        log_text = f.read()
    pid_list = extract_kfd_pids(log_text)
    cmd = "sudo kill -9 "
    for pid in pid_list:
        cmd += pid + " "
    #ssh.exec("pkill -9 -f 'vllm serve' || true")
    print("try to stop\n")
    print(cmd)
    #ssh.exec(f"{cmd} >> ~/Desktop/Smart_Parameter_Automation_Tuning/kill_log.log 2>&1", get_pty=True)
    #ssh.exec(f"{cmd}")
    ssh.exec_sudo(f"{cmd}")
    ssh.exec(f"rm {log}")
    print("finish stop\n")