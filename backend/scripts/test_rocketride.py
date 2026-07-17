"""Verify RocketRide Cloud authentication and execute a minimal pipeline."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from rocketride import RocketRideClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env", override=False)


async def main() -> None:
    uri = os.getenv("ROCKETRIDE_URI", "https://api.rocketride.ai").strip()
    api_key = os.getenv("ROCKETRIDE_APIKEY", "").strip()
    if not api_key:
        raise SystemExit("ROCKETRIDE_APIKEY is empty in backend/.env")

    pipeline = BACKEND_DIR / "pipelines" / "hello.pipe"
    client = RocketRideClient(uri=uri, auth=api_key, request_timeout=30000)
    token = None
    try:
        await client.connect(timeout=30000)
        await client.ping()
        result = await client.use(filepath=str(pipeline))
        token = result["token"]
        output = await client.send(
            token,
            "Truthscope RocketRide connection verified",
            objinfo={"name": "truthscope-smoke.txt"},
            mimetype="text/plain",
        )
        print("RocketRide Cloud connection: OK")
        print(f"Pipeline response received: {bool(output)}")
    finally:
        if token is not None:
            await client.terminate(token)
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
