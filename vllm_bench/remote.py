import paramiko, pathlib, time, logging
from paramiko import SSHClient, AutoAddPolicy

class SSHSession:
    def __init__(self, host, user, password):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy)
        self.client.connect(hostname=host, username=user, password=password)
        self.sftp = self.client.open_sftp()
        self._sudo_pw = password
        self.log = logging.getLogger("ssh")
    # with 语法进入时调用
    def __enter__(self):
        return self          

    # with 语法退出时调用
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        return False
    
    def upload(self, local, remote):
        remote_dir = pathlib.Path(remote).parent.as_posix()  
        try:
            self.sftp.stat(remote_dir)  
        except IOError:  
            self.sftp.mkdir(remote_dir)  
        self.sftp.put(local, remote)  
        self.log.debug("Uploaded %s → %s", local, remote)
    
    def exec(self, cmd, get_pty=False):
        self.log.debug("Exec: %s", cmd)
        stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=get_pty)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out, err
    
    def exec_sudo(self, cmd):
        sudo_cmd = f"sudo -S -p '' {cmd}"
        self.log.debug("Exec (sudo): %s", sudo_cmd)

        # 必须分配 TTY，否则很多发行版默认 requiretty
        stdin, stdout, stderr = self.client.exec_command(
            sudo_cmd, get_pty=True)

        # 把密码写入 sudo
        stdin.write(self._sudo_pw + '\n')
        stdin.flush()

        out, err = stdout.read().decode(), stderr.read().decode()
        return out, err
    
    def close(self):
        self.sftp.close()
        self.client.close()