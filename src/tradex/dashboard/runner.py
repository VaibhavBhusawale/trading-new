import subprocess
import sys
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.address",
            "0.0.0.0",
            "--server.port",
            "8501",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
