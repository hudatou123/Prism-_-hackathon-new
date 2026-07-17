"""Prism — progressive-disclosure fact-checker (HackwithSeattle 2.0).

This package is Person A's territory: the front of the pipeline
(input -> decompose -> fan-out) plus the streaming orchestration and the
RocketRide deploy adapter. Person B fills in the Pro/Con/Judge prompts behind
`agents.procon_judge` protocols; Person D consumes the event stream in
`orchestrator` to drive the FastAPI/SSE backend and the final synthesizer.
"""

__version__ = "0.1.0"
