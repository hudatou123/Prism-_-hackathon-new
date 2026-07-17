"""RocketRide adapter — the ONE place the real SDK gets wired in (F2).

ASSUMPTION (flag for the team): the exact RocketRide Cloud SDK surface isn't
pinned in the design doc, so every pipe here is a plain async callable behind a
tiny `Pipe` protocol. When the real SDK is known, implement `deploy()` and
`invoke()` against it and NOTHING upstream changes — agent logic stays put, only
this glue moves (exactly the CH0/F2 "swap providers without touching agent
logic" property).

Minute-0 task (F2): `python -m prism.rocketride hello` deploys/booth-tests
the hello-world path before any real logic exists.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable, Dict, Protocol

PipeFn = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class Pipe(Protocol):
    name: str
    async def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...


# --- registry: each .pipe registers here so deploy() can enumerate them ------
_REGISTRY: Dict[str, PipeFn] = {}


def pipe(name: str) -> Callable[[PipeFn], PipeFn]:
    def deco(fn: PipeFn) -> PipeFn:
        _REGISTRY[name] = fn
        fn.pipe_name = name  # type: ignore[attr-defined]
        return fn
    return deco


def registered() -> Dict[str, PipeFn]:
    return dict(_REGISTRY)


# --- deploy / invoke: real SDK plugs in HERE --------------------------------
async def deploy(name: str) -> str:
    """Deploy one pipe to RocketRide Cloud. Returns a deployment id/url.

    TODO(real SDK): replace the local echo with the RocketRide deploy call.
    Kept as a no-op-with-proof so the hour-0 spike has something to run and the
    'proven path' for the 4:30 redeploy is a single implemented function.
    """
    if name not in _REGISTRY:
        raise KeyError(f"unknown pipe '{name}'; registered: {list(_REGISTRY)}")
    project = os.getenv("ROCKETRIDE_PROJECT", "prism")
    # e.g. return await rocketride_sdk.deploy(project, name, entry=_REGISTRY[name])
    return f"local://{project}/{name}"  # placeholder deployment ref


async def invoke(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a deployed pipe. Plan B fans these out in parallel from FastAPI.

    TODO(real SDK): replace the direct call with the RocketRide invoke/webhook.
    Direct in-process call keeps local dev identical to the deployed contract.
    """
    if name not in _REGISTRY:
        raise KeyError(f"unknown pipe '{name}'")
    return await _REGISTRY[name](payload)


# --- CLI: hour-0 hello-world spike (F2 non-negotiable) ----------------------
def _main() -> None:
    import sys

    # Importing pipelines registers them.
    from pipelines import hello_world  # noqa: F401
    from pipelines import facet_pipeline  # noqa: F401

    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    async def go():
        if cmd == "list":
            print("registered pipes:", list(registered()))
        elif cmd == "hello":
            ref = await deploy("hello_world")
            print("deployed:", ref)
            out = await invoke("hello_world", {"name": "HackwithSeattle"})
            print("invoke ->", out)
        elif cmd == "deploy-all":
            for name in registered():
                print("deployed:", await deploy(name))
        else:
            print(f"unknown command: {cmd}")

    asyncio.run(go())


if __name__ == "__main__":
    # Run via the canonical module so the pipe decorators register into the
    # SAME _REGISTRY this CLI reads (avoids the `-m` __main__ double-import).
    import prism.rocketride as _rr
    _rr._main()
