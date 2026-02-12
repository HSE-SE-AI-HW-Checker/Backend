"""
Docker Flutter Builder - manages Docker containers for Flutter Web builds from Git repositories.
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class BuildResult:
    success: bool
    output_path: Optional[str]
    logs: str
    error: Optional[str] = None


@dataclass
class RepoConfig:
    """Configuration for repository to build."""
    repo_url: str = "https://github.com/superesl555/Tinder_sample.git"
    project_dir: str = "cats_tinder"
    branch: str = "main"


class DockerFlutterBuilder:
    """Manages Flutter Web builds in Docker containers from Git repositories."""

    IMAGE_NAME = "flutter-web-builder"
    DOCKERFILE = "Dockerfile.flutter_web"

    def __init__(self, output_dir: Optional[str] = None):
        self.module_dir = Path(__file__).parent
        self.dockerfile_path = self.module_dir / self.DOCKERFILE
        self.output_dir = Path(output_dir) if output_dir else self.module_dir / "output"
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _run_command(self, cmd: list[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result."""
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            encoding='utf-8'
        )

    def check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = self._run_command(["docker", "info"])
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def image_exists(self, tag: str = "latest") -> bool:
        """Check if the Flutter builder image already exists."""
        result = self._run_command(["docker", "images", "-q", f"{self.IMAGE_NAME}:{tag}"])
        return bool(result.stdout.strip())

    def build_image(
        self,
        repo_config: Optional[RepoConfig] = None,
        tag: str = "latest",
        force_rebuild: bool = False
    ) -> bool:
        """
        Build the Docker image for Flutter Web builds.

        Args:
            repo_config: Repository configuration (uses defaults if None)
            tag: Image tag
            force_rebuild: Force rebuild even if image exists
        """
        config = repo_config or RepoConfig()
        image_tag = f"{self.IMAGE_NAME}:{tag}"

        if self.image_exists(tag) and not force_rebuild:
            print(f"Image '{image_tag}' already exists. Use force_rebuild=True to rebuild.")
            return True

        print(f"Building Docker image '{image_tag}'...")
        print(f"  Repository: {config.repo_url}")
        print(f"  Project dir: {config.project_dir}")
        print(f"  Branch: {config.branch}")

        result = self._run_command([
            "docker", "build",
            "--progress=plain",
            "--build-arg", f"REPO_URL={config.repo_url}",
            "--build-arg", f"PROJECT_DIR={config.project_dir}",
            "--build-arg", f"BRANCH={config.branch}",
            "-t", image_tag,
            "-f", str(self.dockerfile_path),
            str(self.module_dir)
        ], capture_output=False)

        return result.returncode == 0

    def run_build(self, tag: str = "latest", build_mode: str = "release") -> BuildResult:
        """
        Run Flutter Web build inside the container.

        Args:
            tag: Image tag to use
            build_mode: Build mode - 'release', 'debug', or 'profile'

        Returns:
            BuildResult with success status and logs
        """
        if not self.check_docker():
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error="Docker is not available or not running."
            )

        image_tag = f"{self.IMAGE_NAME}:{tag}"

        if not self.image_exists(tag):
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error=f"Image '{image_tag}' not found. Run build_image() first."
            )

        container_name = f"flutter-build-{os.getpid()}"
        build_output = self.output_dir / "web"

        print(f"Starting Flutter Web build ({build_mode})...")

        # Run build and copy output
        cmd = [
            "docker", "run",
            "--rm",
            "--name", container_name,
            "-v", f"{build_output.parent}:/output",
            image_tag,
            "sh", "-c",
            f"flutter build web --{build_mode} && cp -r build/web /output/"
        ]

        result = self._run_command(cmd, capture_output=False)

        if result.returncode == 0 and build_output.exists():
            return BuildResult(
                success=True,
                output_path=str(build_output),
                logs="Build completed successfully."
            )
        else:
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error="Build failed. Check Docker logs for details."
            )

    def run_tests(self, tag: str = "latest") -> BuildResult:
        """
        Run Flutter tests inside the container.

        Args:
            tag: Image tag to use

        Returns:
            BuildResult with success status and logs
        """
        if not self.check_docker():
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error="Docker is not available or not running."
            )

        image_tag = f"{self.IMAGE_NAME}:{tag}"

        if not self.image_exists(tag):
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error=f"Image '{image_tag}' not found. Run build_image() first."
            )

        container_name = f"flutter-test-{os.getpid()}"

        print("Running Flutter tests...")

        cmd = [
            "docker", "run",
            "--rm",
            "--name", container_name,
            image_tag,
            "flutter", "test"
        ]

        result = self._run_command(cmd, capture_output=False)

        if result.returncode == 0:
            return BuildResult(
                success=True,
                output_path=None,
                logs="All tests passed."
            )
        else:
            return BuildResult(
                success=False,
                output_path=None,
                logs="",
                error="Tests failed."
            )

    def clean_output(self) -> None:
        """Clean build output directory."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"Cleaned: {self.output_dir}")

    def remove_image(self, tag: str = "latest") -> bool:
        """Remove the Docker image."""
        result = self._run_command(["docker", "rmi", f"{self.IMAGE_NAME}:{tag}"])
        return result.returncode == 0

    def list_images(self) -> list[str]:
        """List all flutter-web-builder images."""
        result = self._run_command([
            "docker", "images",
            "--format", "{{.Repository}}:{{.Tag}}",
            self.IMAGE_NAME
        ])
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
