"""
test_smoke.py — The three canonical test cases from the design doc.

Run this every time you tune a prompt. If any of these regress, revert.

Usage:
    python test_smoke.py
    python test_smoke.py --live   # bypass cache, hit real APIs

Expected outcomes:
  1. "The earth is round" → con_abstained=True, verdict='confirmed'
  2. "Meta laid off 5% of workforce" → real Con evidence, verdict likely
     'disputed' or 'mostly_confirmed' depending on what search returns
  3. Fresh news claim → live pipeline sanity check, no regression on
     the settled-fact and dispute cases
"""
from __future__ import annotations

import sys
from pprint import pprint

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from facet_runner import run_facet
from grounding import cache_stats, clear_cache
from schemas import FacetQuery

console = Console()


def print_facet_result(fr):
    """Pretty-print a FacetResult so you can eyeball it during dev."""
    header = f"[bold]FACET[/bold] {fr.facet_name}  |  [bold]VERDICT[/bold] {fr.verdict}"
    if fr.con_abstained:
        header += "  |  [yellow]CON ABSTAINED[/yellow]"
    console.print(Panel(header))

    if fr.abstain_reason:
        console.print(f"  [dim]abstain reason:[/dim] {fr.abstain_reason}")

    console.print(
        f"  sources_examined={fr.sources_examined}  "
        f"quotes_attempted={fr.quotes_attempted}  "
        f"quotes_verified={fr.quotes_verified}"
    )

    if fr.pro_claims:
        t = Table(title="PRO", show_lines=False)
        t.add_column("tier", style="cyan")
        t.add_column("match", style="green")
        t.add_column("quote", overflow="fold", max_width=60)
        t.add_column("url", overflow="fold", max_width=40)
        for v in fr.pro_claims:
            t.add_row(v.quality_tier, v.match_type, v.claim.quote[:200], v.claim.url)
        console.print(t)

    if fr.con_claims:
        t = Table(title="CON", show_lines=False)
        t.add_column("tier", style="cyan")
        t.add_column("match", style="green")
        t.add_column("quote", overflow="fold", max_width=60)
        t.add_column("url", overflow="fold", max_width=40)
        for v in fr.con_claims:
            t.add_row(v.quality_tier, v.match_type, v.claim.quote[:200], v.claim.url)
        console.print(t)

    console.print()


# ── Test case 1: settled fact (should short-circuit or abstain) ─────────
def test_settled_fact():
    console.print("[bold magenta]TEST 1: settled fact — the earth is round[/bold magenta]")
    fq = FacetQuery(
        facet_name="fact",
        topic="The earth is round",
        queries=["is the earth round scientific consensus"],
        is_settled_fact=True,  # Decomposer would mark this
    )
    fr = run_facet(fq)
    print_facet_result(fr)
    assert fr.con_abstained, "Con should have abstained on settled fact"
    assert fr.verdict == "confirmed", f"Expected 'confirmed', got '{fr.verdict}'"
    console.print("[bold green]✓ PASSED[/bold green]\n")


# ── Test case 2: real dispute ──────────────────────────────────────────
def test_real_dispute():
    console.print("[bold magenta]TEST 2: real dispute — Meta layoff scale[/bold magenta]")
    fq = FacetQuery(
        facet_name="scale",
        topic="Meta laid off approximately 5% of its workforce in early 2025",
        queries=[
            "Meta layoffs 2025 percentage workforce",
            "Meta 5 percent layoff official announcement",
        ],
        is_settled_fact=False,
    )
    fr = run_facet(fq)
    print_facet_result(fr)
    # Loose assertion — we're checking the pipeline runs, not that any
    # specific verdict comes back. Live web is noisy.
    assert fr.verdict in {"confirmed", "mostly_confirmed", "disputed", "unclear"}, \
        f"Got unexpected verdict '{fr.verdict}'"
    console.print("[bold green]✓ PASSED[/bold green]\n")


# ── Test case 3: fresh news (pipeline sanity check) ────────────────────
def test_fresh_claim():
    console.print("[bold magenta]TEST 3: fresh live claim (pipeline sanity)[/bold magenta]")
    # Change this to something from today's news at the venue.
    fq = FacetQuery(
        facet_name="fact",
        topic="The Federal Reserve most recently changed interest rates in 2025",
        queries=["Federal Reserve interest rate decision 2025 latest"],
        is_settled_fact=False,
    )
    fr = run_facet(fq)
    print_facet_result(fr)
    console.print("[bold green]✓ PASSED (sanity)[/bold green]\n")


# ── Test case 4: stakeholder reactions (grassroots + named) ────────────
def test_stakeholder_reactions():
    console.print("[bold magenta]TEST 4: stakeholder reactions with grassroots[/bold magenta]")
    fq = FacetQuery(
        facet_name="stakeholder_reactions",
        topic="Meta laid off approximately 5% of its workforce",
        queries=[
            "Meta layoff reactions employees",
            "Meta layoff analyst response",
        ],
        is_settled_fact=False,
    )
    fr = run_facet(fq)
    print_facet_result(fr)
    console.print("[bold green]✓ PASSED (sanity)[/bold green]\n")


# ── Main ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--live" in sys.argv:
        console.print("[bold red]--live: clearing cache first[/bold red]")
        clear_cache()

    console.print(f"Cache before run: {cache_stats()}\n")

    test_settled_fact()
    test_real_dispute()
    test_fresh_claim()
    test_stakeholder_reactions()

    console.print(f"Cache after run: {cache_stats()}")
