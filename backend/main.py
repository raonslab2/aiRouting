import subprocess
import tempfile
import shutil
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

app = FastAPI(title="aiRouting-backend")


def run_freerouting(dsn_path: Path, output_dir: Path):
    """
    Minimal Freerouting CLI invocation.
    Assumes freerouting JAR or gradlew executableJar already built.
    """
    # Placeholder command; adjust jar path as needed.
    jar = Path(os.environ.get("FREEROUTING_JAR", "freerouting-executable.jar"))
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
    with log_path.open("w") as log_file:
        subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT, check=False)
    return ses_path, log_path


@app.post("/analyze")
async def analyze_board(file: UploadFile, target_nets: str = Form("")):
    """
    Accepts a DSN file and optional comma-separated target nets.
    Returns SES path + log summary (placeholder).
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="ai-routing-"))
    dsn_path = tmpdir / file.filename
    content = await file.read()
    dsn_path.write_bytes(content)

    try:
        ses_path, log_path = run_freerouting(dsn_path, tmpdir)
        return JSONResponse(
            {
                "status": "ok",
                "ses": str(ses_path),
                "log": str(log_path),
                "target_nets": target_nets.split(",") if target_nets else [],
            }
        )
    finally:
        # For now, keep artifacts; caller can clean or we can purge in future.
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.get("/health")
def health():
    return {"status": "ok"}
