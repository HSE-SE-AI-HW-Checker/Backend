#!/usr/bin/env python3
"""
CLI for Docker Flutter Builder.

Usage:
    python cli.py build-image [--repo URL] [--dir DIR] [--branch BRANCH] [--tag TAG] [--force]
    python cli.py build [--tag TAG] [--mode release|debug|profile]
    python cli.py test [--tag TAG]
    python cli.py clean
    python cli.py check
    python cli.py images
"""

import argparse
import sys

from builder import DockerFlutterBuilder, RepoConfig


def cmd_build_image(args) -> int:
    """Build the Docker image with cloned repository."""
    builder = DockerFlutterBuilder()

    if not builder.check_docker():
        print("[FAIL] Docker is not available or not running.")
        return 1

    config = RepoConfig(
        repo_url=args.repo,
        project_dir=args.dir,
        branch=args.branch
    )

    if builder.build_image(repo_config=config, tag=args.tag, force_rebuild=args.force):
        print(f"\n[OK] Docker image built successfully: {builder.IMAGE_NAME}:{args.tag}")
        return 0
    else:
        print("\n[FAIL] Failed to build Docker image.")
        return 1


def cmd_build(args) -> int:
    """Run Flutter web build."""
    builder = DockerFlutterBuilder()
    result = builder.run_build(tag=args.tag, build_mode=args.mode)

    if result.success:
        print(f"\n[OK] Build successful!")
        print(f"  Output: {result.output_path}")
        return 0
    else:
        print(f"\n[FAIL] Build failed: {result.error}")
        return 1


def cmd_test(args) -> int:
    """Run Flutter tests."""
    builder = DockerFlutterBuilder()
    result = builder.run_tests(tag=args.tag)

    if result.success:
        print(f"\n[OK] {result.logs}")
        return 0
    else:
        print(f"\n[FAIL] {result.error}")
        return 1


def cmd_clean(args) -> int:
    """Clean build outputs."""
    builder = DockerFlutterBuilder()
    builder.clean_output()
    print("[OK] Cleaned.")
    return 0


def cmd_check(args) -> int:
    """Check Docker availability."""
    builder = DockerFlutterBuilder()

    print("Checking Docker...")
    if builder.check_docker():
        print("[OK] Docker is available and running.")
    else:
        print("[FAIL] Docker is not available or not running.")
        return 1

    print("\nChecking Flutter builder images...")
    images = builder.list_images()
    if images:
        for img in images:
            print(f"  [OK] {img}")
    else:
        print(f"  ○ No images found. Run 'build-image' to create one.")

    return 0


def cmd_images(args) -> int:
    """List all builder images."""
    builder = DockerFlutterBuilder()
    images = builder.list_images()

    if images:
        print("Flutter builder images:")
        for img in images:
            print(f"  - {img}")
    else:
        print("No flutter-web-builder images found.")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Docker Flutter Builder CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check Docker status
    python cli.py check

    # Build image with default repo (Tinder_sample/cats_tinder)
    python cli.py build-image

    # Build image from custom repo
    python cli.py build-image --repo https://github.com/user/repo.git --dir my_app

    # Run web build
    python cli.py build

    # Run tests
    python cli.py test

    # Clean outputs
    python cli.py clean
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # build-image command
    image_parser = subparsers.add_parser("build-image", help="Build Docker image with cloned repository")
    image_parser.add_argument(
        "--repo", "-r",
        type=str,
        default="https://github.com/superesl555/Tinder_sample.git",
        help="Git repository URL (default: Tinder_sample)"
    )
    image_parser.add_argument(
        "--dir", "-d",
        type=str,
        default="cats_tinder",
        help="Project directory inside repo (default: cats_tinder)"
    )
    image_parser.add_argument(
        "--branch", "-b",
        type=str,
        default="main",
        help="Git branch (default: main)"
    )
    image_parser.add_argument(
        "--tag", "-t",
        type=str,
        default="latest",
        help="Image tag (default: latest)"
    )
    image_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force rebuild even if image exists"
    )
    image_parser.set_defaults(func=cmd_build_image)

    # build command
    build_parser = subparsers.add_parser("build", help="Run Flutter web build")
    build_parser.add_argument(
        "--tag", "-t",
        type=str,
        default="latest",
        help="Image tag to use (default: latest)"
    )
    build_parser.add_argument(
        "--mode", "-m",
        choices=["release", "debug", "profile"],
        default="release",
        help="Build mode (default: release)"
    )
    build_parser.set_defaults(func=cmd_build)

    # test command
    test_parser = subparsers.add_parser("test", help="Run Flutter tests")
    test_parser.add_argument(
        "--tag", "-t",
        type=str,
        default="latest",
        help="Image tag to use (default: latest)"
    )
    test_parser.set_defaults(func=cmd_test)

    # clean command
    clean_parser = subparsers.add_parser("clean", help="Clean build outputs")
    clean_parser.set_defaults(func=cmd_clean)

    # check command
    check_parser = subparsers.add_parser("check", help="Check Docker availability")
    check_parser.set_defaults(func=cmd_check)

    # images command
    images_parser = subparsers.add_parser("images", help="List builder images")
    images_parser.set_defaults(func=cmd_images)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
