import time, logging, uuid
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from ..remote import SSHSession

_TEMPLATES = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))

def render(template_name: str, **ctx) -> str:
    return _TEMPLATES.get_template(template_name).render(**ctx)
  
def start_server(cfg: "GlobalCfg", combo: dict, ssh: SSHSession, out_dir: Path) -> str:
    """上传 + 后台 nohup 运行 server,返回远程脚本路径"""
    script = render("server.sh.j2", **cfg.remote.__dict__, **cfg.model.__dict__, **combo)
    local_file = out_dir / f"server_{uuid.uuid4().hex}.sh"
    local_file.write_text(script)
    remote_file = f"/tmp/{local_file.name}"
    ssh.upload(local_file, remote_file)
    ssh.exec(f"chmod +x {remote_file}")
    # 使用 nohup 让其后台运行
    ssh.exec(f"nohup bash {remote_file} > {remote_file}.log 2>&1 &")
    return remote_file

def stop_server(ssh: SSHSession):
    ssh.exec("pkill -9 -f 'vllm serve' || true")