import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="aiRouting-backend")


def run_freerouting(dsn_path: Path, output_dir: Path):
    """
    Minimal Freerouting CLI invocation.
    Assumes FREEROUTING_JAR points to freerouting-executable.jar.
    """
    jar_env = os.environ.get("FREEROUTING_JAR")
    jar = Path(jar_env) if jar_env else None
    if not jar or not jar.exists():
        raise FileNotFoundError(
            "FREEROUTING_JAR not set or file missing. Set FREEROUTING_JAR to freerouting-executable.jar path."
        )

    ses_path = output_dir / (dsn_path.stem + ".ses")
    log_path = output_dir / (dsn_path.stem + ".log")

    cmd = [
        "java",
        "-jar",
        str(jar),
        "-de",
        str(dsn_path),
        "-do",
        str(ses_path),
        "-dl",
    ]
    with log_path.open("w", encoding="utf-8") as log_file:
        result = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT, check=False)
    return ses_path, log_path, result.returncode


def parse_target_nets(raw: str) -> List[str]:
    return [n.strip() for n in raw.split(",") if n.strip()]


@app.post("/analyze")
async def analyze_board(file: UploadFile, target_nets: str = Form("")):
    """
    Accepts a DSN file and optional comma-separated target nets.
    Returns SES path + log summary placeholder.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="ai-routing-"))
    dsn_path = tmpdir / file.filename
    content = await file.read()
    dsn_path.write_bytes(content)

    nets = parse_target_nets(target_nets)

    try:
        ses_path, log_path, rc = run_freerouting(dsn_path, tmpdir)
        return JSONResponse(
            {
                "status": "ok" if rc == 0 else "error",
                "ses": str(ses_path),
                "log": str(log_path),
                "target_nets": nets,
                "return_code": rc,
            }
        )
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        # Keep artifacts for debugging? For now, remove to avoid leaks.
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.get("/health")
def health():
    return {"status": "ok"}
