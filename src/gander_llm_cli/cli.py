from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import typer
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from dotenv import load_dotenv

load_dotenv()


class OutputPayload(BaseModel):
    """Canonical JSON payload returned by the CLI."""

    human_response_markdown: str = Field(
        ..., description="User-facing answer in markdown."
    )
    citations: List[str] = Field(
        default_factory=list, description="Every URL cited in the answer."
    )
    mentions: List[str] = Field(
        default_factory=list, description="Occurrences of the brand name in the answer."
    )
    owned_sources: List[HttpUrl] = Field(
        default_factory=list, description="URLs under the brand's domain or subdomains."
    )
    sources: List[HttpUrl] = Field(
        default_factory=list, description="Non-owned external URLs present in the answer."
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Budgets, usage counts, token notes, and any run diagnostics.",
    )


@dataclass
class Budgets:
    """Hard caps for search and source selection."""
    max_searches: int
    max_sources: int


def normalize_domain(url: str) -> Optional[str]:
    """Return the registrable domain for grouping owned sources."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return host.lstrip(".")
    except Exception:
        return None


def extract_urls(markdown: str) -> list[str]:
    """Return all HTTP(S) URLs in reading order, de-duplicated and cleaned."""
    # Simple and reliable: grab any http(s) URL, then trim common trailing punctuation.
    urls = re.findall(r"https?://[^\s)>\]]+", markdown)
    cleaned = [u.rstrip(").,;:!?") for u in urls]
    # Preserve first occurrence order
    seen = {}
    for u in cleaned:
        if u not in seen:
            seen[u] = True
    return list(seen.keys())


def extract_mentions(markdown: str, brand: str) -> List[str]:
    """Return exact-case mentions of the brand from the answer text."""
    if not brand:
        return []
    pattern = r"\b" + re.escape(brand) + r"\b"
    return re.findall(pattern, markdown)


def split_owned_external(urls: List[str], brand_domain: str) -> Tuple[List[str], List[str]]:
    """Partition URLs into owned vs external by comparing domains."""
    owned, external = [], []
    brand_domain = brand_domain.lower()
    for u in urls:
        host = normalize_domain(u) or ""
        if host == brand_domain or host.endswith("." + brand_domain):
            owned.append(u)
        else:
            external.append(u)
    owned = list(dict.fromkeys(owned))
    external = list(dict.fromkeys(external))
    return owned, external


def simulate_model_answer(question: str, brand: str, brand_url: str) -> str:
    """Return a deterministic placeholder answer for early development."""
    return (
        f"Here is a brief answer to your question about {brand}.\n\n"
        f"For full details, see the official site: {brand_url}\n"
        f"You may also find third-party reviews helpful at https://example.org/review.\n"
    )


def main(
    brand: str = typer.Option(..., help="Brand name, used to detect mentions."),
    url: str = typer.Option(..., help="Brand's canonical site URL."),
    question: str = typer.Option(..., help="End-user question to answer."),
    max_searches: int = typer.Option(0, help="Hard cap on web searches."),
    max_sources: int = typer.Option(0, help="Hard cap on sources included."),
    model: str = typer.Option("gpt-4o-mini", help="Model identifier."),
    output: Optional[str] = typer.Option(None, help="Path to write JSON output."),
) -> None:
    """
    Produce a single JSON with the final answer and extracted fields.

    This baseline does not perform search. It emits a clean payload and records
    the configured budgets to demonstrate shape and invariants.
    """
    budgets = Budgets(max_searches=max_searches, max_sources=max_sources)
    brand_domain = normalize_domain(url) or ""

    human_md = simulate_model_answer(question=question, brand=brand, brand_url=url)

    all_urls = extract_urls(human_md)
    owned, external = split_owned_external(all_urls, brand_domain)
    citations = all_urls[:]
    mentions = extract_mentions(human_md, brand)

    payload = OutputPayload(
        human_response_markdown=human_md.strip(),
        citations=citations,
        mentions=mentions,
        owned_sources=owned,
        sources=external,
        metadata={
            "model": model,
            "budgets": {"max_searches": budgets.max_searches, "max_sources": budgets.max_sources},
            "usage": {"searches": 0, "sources_included": len(owned) + len(external)},
            "notes": "Skeleton run without search or real model calls.",
        },
    )

    try:
        blob = payload.model_dump_json(indent=2, by_alias=True)
    except ValidationError as ve:
        typer.echo(f"Payload validation failed: {ve}", err=True)
        raise typer.Exit(code=1)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(blob)
        typer.echo(output)
    else:
        sys.stdout.write(blob)
