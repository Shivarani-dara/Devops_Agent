import subprocess


def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"ERROR running command: {e}",
            "returncode": -1
        }