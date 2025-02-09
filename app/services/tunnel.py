import asyncio
import logging
import random
from typing import Dict, Optional

import paramiko

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('ssh_tunnel.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class SSHTunnel:
    def __init__(self, ssh_config: Dict):
        self.config = ssh_config
        self.client = None
        self.sftp = None

    async def connect(self) -> bool:
        try:
            logger.info("Initializing SSH client.")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.info(
                "Attempting SSH connection to %s:%s",
                self.config['host'],
                self.config.get('port', 22)
            )

            # Connect with keepalive options
            self.client.connect(
                hostname=self.config['host'],
                port=int(self.config.get('port', 22)),
                username=self.config['username'],
                password=self.config['password'],
                look_for_keys=False,
                allow_agent=False,
                timeout=30
            )

            # Enable keepalive packets
            transport = self.client.get_transport()
            transport.set_keepalive(15)  # Send keepalive every 15 seconds

            logger.info("SSH connection established successfully.")
            logger.info("Initializing SFTP connection")
            self.sftp = self.client.open_sftp()
            logger.info("SFTP connection established successfully")
            return True
        except Exception as e:
            logger.error("SSH connection failed: %s", e)
            print(f"SSH connection failed: {e}")
            return False

    async def execute_command(self, command: str, timeout: int = 60) -> str:
        """Execute a command with a specified timeout."""
        if not self.client:
            error_msg = "SSH connection not established"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        try:
            logger.info("Executing command: %s", command)
            # Use get_transport().open_session() for better timeout control
            channel = self.client.get_transport().open_session()
            channel.settimeout(timeout)
            channel.exec_command(command)

            stdout = channel.makefile('rb', -1)
            stderr = channel.makefile_stderr('rb', -1)

            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            exit_status = channel.recv_exit_status()

            if error:
                logger.error("Command error output: %s", error)
            if output:
                logger.debug("Command output: %s", output)

            if exit_status != 0:
                raise Exception(f"Command failed with status {exit_status}: {error}")

            return error if error else output
        except Exception as e:
            logger.error("Command execution failed: %s", e)
            raise

    async def execute_long_command(self, command: str, timeout: int = 3600) -> str:
        """Execute a long-running command with automatic reconnection."""
        try:
            # Set a longer timeout for long-running commands
            return await self.execute_command(command, timeout=timeout)
        except Exception as e:
            if "SSH session not active" in str(e):
                logger.info("Session expired during long command, reconnecting...")
                await self.connect()
                return await self.execute_command(command, timeout=timeout)
            raise

    async def write_file(self, remote_path: str, content: str):
        if not self.sftp:
            error_msg = "SFTP not established"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        try:
            logger.info("Writing content to %s", remote_path)
            with self.sftp.open(remote_path, 'w') as f:
                f.write(content)
            logger.info("File write completed successfully")
        except Exception as e:
            logger.error("File write failed: %s", e)
            raise

    async def get_free_port(self, start_port: int = 8000) -> Optional[int]:
        try:
            port = random.randint(8000, 9000)
            logger.info(f"Selected random port: {port}")
            return port
        except Exception as e:
            logger.error(f"Error selecting port: {e}")
            return start_port

    async def check_and_install_dependencies(self):
        """Check if npm and localtunnel are installed, install if missing."""
        try:
            # Check for npm installation without raising exception on failure
            logger.info("Checking for npm installation")
            try:
                npm_check = await self.execute_command("which npm")
                npm_installed = bool(npm_check)
            except Exception:
                npm_installed = False

            if not npm_installed:
                logger.info("Installing npm...")
                try:
                    # Update package list first
                    update_cmd = f'echo "{self.config["password"]}" | sudo -S apt-get update'
                    await self.execute_command(update_cmd)

                    # Install npm
                    install_cmd = f'echo "{self.config["password"]}" | sudo -S apt-get install -y npm'
                    await self.execute_command(install_cmd)
                    logger.info("npm installation completed")
                except Exception as e:
                    logger.error(f"Failed to install npm: {e}")
                    return False

            # Check for localtunnel only if npm is available
            if npm_installed or await self.execute_command("which npm"):
                logger.info("Checking for localtunnel installation")
                try:
                    lt_check = await self.execute_command("which lt")
                    lt_installed = bool(lt_check)
                except Exception:
                    lt_installed = False

                if not lt_installed:
                    logger.info("Installing localtunnel globally...")
                    try:
                        await self.execute_command(
                            f'echo "{self.config["password"]}" | sudo -S npm install -g localtunnel'
                        )
                        logger.info("localtunnel installation completed")
                    except Exception as e:
                        logger.error(f"Failed to install localtunnel: {e}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error checking/installing dependencies: {e}")
            return False

    async def create_tunnel_fallback(self, port: int, subdomain: str) -> Optional[str]:
        """Create a tunnel using nohup as fallback."""
        try:
            logger.info(f"Creating tunnel for port {port} with subdomain {subdomain}")

            # Create log directory first and ensure proper name formatting
            safe_subdomain = subdomain.replace("/", "-").replace(".", "-").lower()
            log_dir = "/tmp/tunnels"
            log_file = f"{log_dir}/tunnel_{safe_subdomain}_{port}.log"

            # Create directory and log file with proper permissions
            await self.execute_command(f'mkdir -p {log_dir}')
            await self.execute_command(f'touch {log_file}')
            await self.execute_command(f'chmod 777 {log_file}')

            # Start tunnel process in background
            tunnel_cmd = (
                f"nohup lt --port {port} --subdomain {safe_subdomain} > {log_file} 2>&1 & echo $!"
            )
            pid = await self.execute_command(tunnel_cmd)
            logger.info(f"Started tunnel process with PID: {pid}")

            # Wait for tunnel to establish
            max_retries = 5
            for attempt in range(max_retries):
                await asyncio.sleep(3)

                # Check log for URL
                try:
                    log_content = await self.execute_command(f"cat {log_file}")
                    for line in log_content.split('\n'):
                        if 'your url is:' in line.lower():
                            tunnel_url = line.split('your url is:')[-1].strip()
                            logger.info(f"Tunnel created successfully: {tunnel_url}")

                            # Save PID for future reference
                            await self.write_file(f"{log_dir}/tunnel_{safe_subdomain}_{port}.pid", pid)
                            return tunnel_url
                except Exception as e:
                    logger.warning(f"Error reading log file on attempt {attempt + 1}: {e}")

                logger.warning(f"URL not found in logs on attempt {attempt + 1}")

            logger.error("Failed to create tunnel after maximum retries")
            return None

        except Exception as e:
            logger.error(f"Error creating tunnel: {e}")
            return None

    async def check_tunnel_status(self, subdomain: str, port: int) -> Dict:
        """Check status of a specific tunnel."""
        try:
            safe_subdomain = subdomain.replace("/", "-").replace(".", "-").lower()
            log_dir = "/tmp/tunnels"
            pid_file = f"{log_dir}/tunnel_{safe_subdomain}_{port}.pid"
            log_file = f"{log_dir}/tunnel_{safe_subdomain}_{port}.log"

            # Try to get PID from file
            try:
                pid = await self.execute_command(f"cat {pid_file}")
                ps_check = await self.execute_command(f"ps -p {pid} | grep lt")
                is_running = bool(ps_check)
            except Exception:
                is_running = False

            # Get logs if available
            try:
                logs = await self.execute_command(f"tail -n 20 {log_file}")
            except Exception:
                logs = "No logs available"

            return {
                "active": is_running,
                "logs": logs,
                "pid": pid if is_running else None
            }
        except Exception as e:
            logger.error(f"Error checking tunnel status: {e}")
            return {
                "active": False,
                "error": str(e)
            }

    def close(self):
        try:
            if self.sftp:
                logger.info("Closing SFTP connection")
                self.sftp.close()
            if self.client:
                logger.info("Closing SSH connection")
                self.client.close()
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error("Error while closing connections: %s", e)
