import time, logging, uuid
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from ..remote import SSHSession

_TEMPLATES = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))

def render(template_name: str, **ctx) -> str:
    return _TEMPLATES.get_template(template_name).render(**ctx)

def run_client(cfg: "GlobalCfg", combo: dict, ssh: SSHSession, out_dir: Path):
    script = render("client.sh.j2", **cfg.remote.__dict__,
                    **cfg.model.__dict__, **cfg.benchmark.__dict__, **combo)
    local = out_dir / f"client_{uuid.uuid4().hex}.sh"
    remote = f"/tmp/{local.name}"
    local.write_text(script)
    ssh.upload(local, remote)
    ssh.exec(f"chmod +x {remote}")
    out, err = ssh.exec(f"bash {remote}", get_pty=True)
    (out_dir / f"client_stdout_{combo['run_id']}.log").write_text(out + err)