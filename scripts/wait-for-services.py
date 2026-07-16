import os
import socket
import sys
import time


def wait(host: str, port: int, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            time.sleep(1)
    print(f"Timeout waiting for {host}:{port}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    wait(os.getenv("POSTGRES_HOST", "postgres"), int(os.getenv("POSTGRES_PORT", "5432")))
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_host = redis_url.split("://", 1)[-1].split("@")[-1].split(":")[0]
    redis_port = int(redis_url.rsplit(":", 1)[-1].split("/")[0])
    wait(redis_host, redis_port)
