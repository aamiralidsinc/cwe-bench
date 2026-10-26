"""Run the product's own CLI entry point from the restored workspace."""
import os
import sys

sys.path.insert(0, os.environ.get("PD_WORKSPACE", "/workspace"))

from proot_distro.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = ["proot-distro", *sys.argv[1:]]
    main()
