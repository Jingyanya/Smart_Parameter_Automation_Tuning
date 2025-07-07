import os, subprocess
import logging, time
from pathlib import Path
from .config import GlobalCfg
from .remote import SSHSession
from .model_server import start_server, stop_server
from .client import run_client
import re

pat = re.compile(r'(?:\x1b\[[0-9;]*m)*.*?Application\s+startup\s+complete\.', re.I)

LOG_FILE: str
NEEDLE     = " INFO:     Application startup complete."
TIMEOUT_S  = 300          # 最长等待 5 分钟，可按需调整
SLEEP_STEP = 0.5          # 轮询间隔

def wait_until_startup(log_file, needle=NEEDLE, timeout=TIMEOUT_S):
    start_time = time.time()
    with open(log_file, "r") as f:
        # 跳到文件尾部，避免把历史日志匹配进去
        f.seek(0, os.SEEK_END)

        while True:
            # 超时保护
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Log did not contain '{needle}' within {timeout} s")

            line = f.readline()
            print("log: ", line, "\n")
            if not line:
                time.sleep(SLEEP_STEP)   # 没有新内容就稍等
                continue

            if pat.search(line):
                print("Application startup detected.")
                return

def run_all(cfg_path: str):
    cfg = GlobalCfg.read_yaml(cfg_path)
    cfg.output_dir.mkdir(exist_ok=True, parents=True)
    log = logging.getLogger("orchestrator")

    with SSHSession(cfg.docker.host, cfg.docker.user, cfg.docker.password) as ssh:  
        for combo in cfg.param_grid():
            log.info("Running combo: %s", combo)
            combo_dir = cfg.output_dir / f"r{combo['req_rate']}_run{combo['num_prompt']}"
            combo_dir.mkdir(exist_ok=True)

            remote_script = start_server(cfg, combo, ssh, combo_dir)  
            #time.sleep(240)           # 等待 server ready，可替换成探活逻辑
            print(f"{remote_script}.log")
            time.sleep(5)
            wait_until_startup(log_file=f"{remote_script}.log")
            #time.sleep(300)
            run_client(cfg, combo, ssh, combo_dir)
            time.sleep(2)
            
            show_pid = 'rocm-smi --showpids --showmemuse >> /app/data/pids.log 2>&1'
            pid_cmd = f'docker exec -it d0ce559b0fad /bin/bash -c "{show_pid}"'
            ssh.exec(f"{pid_cmd}", get_pty=True)
            
            time.sleep(2)
            stop_server(ssh, "/home/pvteam64/Desktop/docker_mnt/pids.log")
            log.info("Finished combo %s", combo) 