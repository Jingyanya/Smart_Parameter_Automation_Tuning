import paramiko, pathlib, time, logging
from paramiko import SSHClient, AutoAddPolicy

class SSHSession:
    def __init__(self, host, user, password):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy)
        self.client.connect(hostname=host, username=user, password=password)
        self.sftp = self.client.open_sftp()
        self.log = logging.getLogger("ssh")
    
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
    
    def close(self):
        self.sftp.close()
        self.client.close()