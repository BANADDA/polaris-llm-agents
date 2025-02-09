import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple

import docker
import firebase_admin
import pytz
from firebase_admin import credentials, firestore
from jinja2 import Environment, FileSystemLoader

from .model_registry import ModelRegistry
from .tunnel import SSHTunnel

# Configure logger for the deployment service
logger = logging.getLogger("DeploymentService")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("deployment.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class DeploymentService:
    def __init__(self):
        logger.info("Initializing DeploymentService")
        self.template_env = Environment(loader=FileSystemLoader('app/templates'))
        self.model_registry = ModelRegistry()
        self.tunnel = None

        # Initialize Firebase Admin if not already initialized
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("app/auth/config.json")
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized successfully.")
        except Exception as e:
            logger.error("Error initializing Firebase Admin: %s", e)

    async def deploy_model(self, model_id: str, user_id: str, api_name: str, ssh_config: Dict) -> Dict:
        try:
            logger.info(f"Deploying model: {model_id} for user: {user_id}")

            # Get model type
            model_type = await self.model_registry.get_model_type(model_id)
            if not model_type:
                error_msg = f"Model type not found for model id: {model_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info(f"Model type found: {model_type}")

            # Setup SSH tunnel
            logger.info(f"Setting up SSH tunnel using config: {ssh_config}")
            self.tunnel = SSHTunnel(ssh_config)
            if not await self.tunnel.connect():
                error_msg = "Failed to establish SSH connection"
                logger.error(error_msg)
                raise ConnectionError(error_msg)

            # Verify Docker and install tunnel dependencies
            await self.verify_docker_running()
            if not await self.tunnel.check_and_install_dependencies():
                logger.warning("Failed to verify/install tunnel dependencies")

            # Get a random free port
            port = await self.tunnel.get_free_port()
            if not port:
                raise RuntimeError("Failed to get port")
            logger.info(f"Using free port: {port}")

            # Build and deploy container using the new _deploy_container method
            safe_model_id = model_id.replace("/", "-").lower()
            image_tag = f"{user_id}-{safe_model_id}:{uuid.uuid4().hex[:8]}"
            logger.info(f"Using image tag: {image_tag}")

            container_id, network_details, tunnel_url = await self._deploy_container(
                model_id, user_id, model_type, image_tag, port, ssh_config, api_name
            )

            # Start log streaming
            asyncio.create_task(self._start_log_streaming(ssh_config, container_id, duration=60, interval=5))

            # Format timestamp
            tz = pytz.timezone("Etc/GMT-3")
            timestamp_str = datetime.now(tz).strftime("%B %d, %Y at %I:%M:%S %p %Z")

            # Prepare response
            response = {
                "container_id": container_id,
                "model_id": model_id,
                "network_details": network_details,
                "timestamp": timestamp_str,
                "user_id": user_id,
                "api_url": f"http://{ssh_config['host']}:{port}",
                "tunnel_url": tunnel_url,
                "api_name": api_name
            }

            logger.info("Deployment successful; returning connection details")
            return response
        except Exception as e:
            logger.error(f"Deployment error: {e}", exc_info=True)
            raise
        finally:
            if self.tunnel:
                self.tunnel.close()

    async def verify_docker_running(self) -> bool:
        logger.info("Verifying Docker service status on remote machine")
        try:
            result = await self.tunnel.execute_command("docker ps")
            if "Cannot connect to the Docker daemon" in result:
                start_result = await self.tunnel.execute_command(
                    f'echo "{self.tunnel.config["password"]}" | sudo -S systemctl start docker'
                )
                if start_result:
                    raise Exception(f"Failed to start Docker: {start_result}")
                # Verify Docker started successfully
                verify_result = await self.tunnel.execute_command("docker ps")
                if "Cannot connect to the Docker daemon" in verify_result:
                    raise Exception("Docker failed to start after attempting to start service")
            return True
        except Exception as e:
            logger.error(f"Docker verification failed: {e}")
            raise RuntimeError(f"Docker verification failed: {str(e)}")

    async def _deploy_container(self, model_id: str, user_id: str, model_type: str,
                                image_tag: str, port: int, ssh_config: Dict, api_name: str) -> Tuple[str, str, Optional[str]]:
        temp_dir = None
        container_id = None
        try:
            # Create temporary directory
            deploy_id = uuid.uuid4().hex[:8]
            temp_dir = f"/tmp/deploy_{deploy_id}"
            logger.info(f"Creating temporary directory on remote: {temp_dir}")
            await self.tunnel.execute_command(f"mkdir -p {temp_dir}")

            # Setup package structure and copy files
            await self._setup_directory_structure(temp_dir, model_id, user_id)

            # Build Docker image with longer timeout
            logger.info("Building Docker image on remote machine")
            build_cmd = f"cd {temp_dir} && docker build -t {image_tag} ."
            build_result = await self.tunnel.execute_long_command(build_cmd, timeout=3600)
            logger.info(f"Build result: {build_result}")

            # Verify image was built successfully
            image_check = await self.tunnel.execute_command(f"docker images {image_tag} --quiet")
            if not image_check:
                raise Exception(f"Failed to build Docker image. Build output: {build_result}")

            # Run container with HuggingFace token
            logger.info("Starting container on remote")
            hf_token = os.getenv("HUGGINGFACE_TOKEN")  # Get token from environment
            container_cmd = (
                f"docker run -d "
                f"-p {port}:8000 "
                f"{f'-e HF_TOKEN={hf_token} ' if hf_token else ''}"  # Add token if available
                f"{image_tag}"
            )
            container_id = await self.tunnel.execute_command(container_cmd)
            container_id = container_id.strip()

            # Wait for container to be ready
            await self._wait_for_container(container_id)

            # Get network details
            network_details = await self.tunnel.execute_command(
                f"docker inspect --format='{{{{json .NetworkSettings}}}}' {container_id}"
            )

            # Create a tunnel if an API name was provided
            tunnel_url = None
            if api_name:
                logger.info(f"Creating persistent tunnel for {api_name}")
                tunnel_url = await self.tunnel.create_tunnel_fallback(port, api_name)
                if tunnel_url:
                    logger.info(f"Tunnel created successfully: {tunnel_url}")
                else:
                    logger.warning("Failed to create tunnel")

            # Update Firestore with deployment details
            await self._update_firestore(
                user_id, model_id, container_id, network_details,
                ssh_config['host'], port, tunnel_url, api_name
            )

            # Cleanup temporary directory
            await self._cleanup_temp_directory(temp_dir)

            return container_id, network_details.strip(), tunnel_url

        except Exception as e:
            logger.error(f"Error in deployment: {e}", exc_info=True)
            await self._handle_deployment_error(temp_dir, container_id)
            raise

    async def _wait_for_container(self, container_id: str, max_retries: int = 3) -> None:
        """Wait for container to be ready with retries."""
        for attempt in range(max_retries):
            try:
                status = await self.tunnel.execute_command(
                    f"docker inspect --format='{{{{.State.Status}}}}' {container_id}"
                )
                if status.strip() == "running":
                    logger.info(f"Container {container_id} is running")
                    return
                elif status.strip() == "exited":
                    logs = await self.tunnel.execute_command(f"docker logs {container_id}")
                    raise Exception(f"Container exited. Logs: {logs}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Container failed to start: {str(e)}")
                await asyncio.sleep(2)

    # --- Helper Methods ---
    async def _setup_directory_structure(self, temp_dir: str, model_id: str, user_id: str) -> None:
        """Set up the directory structure and copy necessary files."""
        try:
            # Create directory structure
            await self.tunnel.execute_command(f"mkdir -p {temp_dir}/app/auth")
            await self.tunnel.execute_command(f"mkdir -p {temp_dir}/app/api")

            # Create __init__.py files with proper imports
            await self.tunnel.write_file(f"{temp_dir}/app/__init__.py", "from .app import app")
            await self.tunnel.write_file(f"{temp_dir}/app/auth/__init__.py", "")
            await self.tunnel.write_file(f"{temp_dir}/app/api/__init__.py", "")

            # Generate and write template files
            await self._generate_and_write_templates(temp_dir, model_id, user_id)

        except Exception as e:
            logger.error(f"Error setting up directory structure: {e}")
            raise

    async def _cleanup_temp_directory(self, temp_dir: str) -> None:
        """Clean up the temporary directory on the remote machine."""
        if temp_dir:
            logger.info("Cleaning up temporary files")
            await self.tunnel.execute_command(f"rm -rf {temp_dir}")

    async def _handle_deployment_error(self, temp_dir: Optional[str], container_id: Optional[str]) -> None:
        """Handle deployment errors by cleaning up resources."""
        if container_id:
            try:
                await self.tunnel.execute_command(f"docker rm -f {container_id}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up container: {cleanup_error}")
        if temp_dir:
            try:
                await self.tunnel.execute_command(f"rm -rf {temp_dir}")
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")

    async def _update_firestore(self, user_id: str, model_id: str, container_id: str, network_details: str,
                                host: str, port: int, tunnel_url: Optional[str], api_name: str) -> None:
        """Update Firestore with deployment details."""
        try:
            db = firestore.client()
            safe_model_id = model_id.replace("/", "-").lower()
            deployment_doc = {
                "user_id": user_id,
                "model_id": model_id,
                "container_id": container_id,
                "network_details": network_details.strip(),
                "api_url": f"http://{host}:{port}",
                "tunnel_url": tunnel_url,
                "api_name": api_name,
                "port": port,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            # Store current deployment and history
            doc_path = f"{user_id}-{safe_model_id}"
            db.collection('deployments').document(doc_path).set(deployment_doc)
            db.collection('deployment_history').add(deployment_doc)
        except Exception as e:
            logger.error(f"Error updating Firestore: {e}")

    async def _generate_and_write_templates(self, temp_dir: str, model_id: str, user_id: str):
        """Generate and write all required template files."""
        templates = {
            "Dockerfile": ("text_generation/Dockerfile.j2", f"{temp_dir}/Dockerfile"),
            "requirements.txt": ("text_generation/requirements.j2", f"{temp_dir}/requirements.txt"),
            "app.py": ("text_generation/app.py.j2", f"{temp_dir}/app/app.py"),
            "auth_middleware": ("model_server/auth/middleware.py.j2", f"{temp_dir}/app/auth/middleware.py"),
            "auth_token": ("model_server/auth/token.py.j2", f"{temp_dir}/app/auth/token.py"),
            "auth_config": ("model_server/auth/config.json.j2", f"{temp_dir}/app/auth/config.json"),
            "api_inference": ("model_server/api/inference.py.j2", f"{temp_dir}/app/api/inference.py"),
            "api_token": ("model_server/api/token.py.j2", f"{temp_dir}/app/api/token.py")
        }

        for template_name, (template_path, output_path) in templates.items():
            try:
                template = self.template_env.get_template(template_path)
                content = template.render(
                    model_id=model_id,
                    user_id=user_id,
                    use_llama_cpp="llama" in model_id.lower()
                )
                await self.tunnel.write_file(output_path, content)
                logger.info(f"Generated {template_name} at {output_path}")
            except Exception as e:
                logger.error(f"Error generating {template_name}: {e}")
                raise

    async def _start_log_streaming(self, ssh_config: Dict, container_id: str, duration: int = 60, interval: int = 5):
        """Stream container logs through a separate SSH tunnel."""
        logger.info(f"Starting log streaming for container {container_id}")
        log_tunnel = SSHTunnel(ssh_config)
        if not await log_tunnel.connect():
            logger.error("Failed to establish log streaming tunnel")
            return

        try:
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < duration:
                try:
                    logs = await log_tunnel.execute_command(f"docker logs {container_id} 2>&1")
                    logger.info(f"Container {container_id} logs:\n{logs}")
                except Exception as e:
                    logger.error(f"Error fetching logs: {e}")
                await asyncio.sleep(interval)
        finally:
            log_tunnel.close()
