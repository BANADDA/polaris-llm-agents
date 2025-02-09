import asyncio
from typing import Dict, Optional, Tuple

import paramiko


class SSHManager:
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.known_hosts = {}

    async def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(**self.config)
            return True
        except Exception as e:
            print(f"SSH error: {e}")
            return False

    async def execute_command(self, command: str) -> Tuple[str, str]:
        if not self.client:
            await self.connect()
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

    async def check_docker(self) -> bool:
        stdout, _ = await self.execute_command("docker --version")
        return "Docker version" in stdout

    def close(self):
        if self.client:
            self.client.close()