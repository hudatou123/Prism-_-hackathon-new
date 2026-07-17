"""hello_world pipe — the F2 hour-0 deploy spike.

Non-negotiable (§10): deployed to RocketRide Cloud by 0:45, BEFORE any real
logic exists, so deployment surprises get found when they're cheap. This file
has zero dependencies on the rest of the pipeline on purpose — if THIS won't
deploy, nothing will, and we want to know at minute 20.

(RocketRide's on-disk name for a pipe may be `hello_world.pipe`; here it's a
Python module so `python -m prism.rocketride hello` can import it. The
`@pipe` decorator is what marks it as a deployable unit — see rocketride.py.)

Run:  python -m prism.rocketride hello
"""
from __future__ import annotations

from typing import Any, Dict

from prism.rocketride import pipe


@pipe("hello_world")
async def hello_world(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = payload.get("name", "world")
    return {"message": f"hello, {name} — RocketRide path is live"}
