from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.tinydb import Database
from src.oxylabs_client import (
    scrape_product_details,
    search_competitors,
    scrape_multiple_products,
    ProgressReporter,
    NoopReporter,
    SearchResult,
    MultiScrapeResult,
)


# ── Result containers ──────────────────────────────────────────────────────────

@dataclass
class ScrapeResult:
    """Returned by scrape_and_store_product."""
    success: bool
    product: dict[str, Any] | None = None
    error: str = ""


@dataclass
class CompetitorResult:
    """Returned by fetch_and_store_competitors."""
    success: bool
    competitors: list[dict[str, Any]] = field(default_factory=list)
    # Contextual info rendered by app.py as styled chips/badges
    search_domain: str = ""
    search_geo: str = ""
    error: str = ""
    # ASINs that could not be scraped — surfaced as a warning in app.py
    failed_asins: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.competitors)


# ── Service functions ──────────────────────────────────────────────────────────

def scrape_and_store_product(
    asin: str,
    geo_location: str,
    domain: str,
) -> ScrapeResult:
    """
    Scrape a single product from Amazon and persist it to the database.

    Returns a ScrapeResult — app.py decides how to surface success/error.
    """
    try:
        data = scrape_product_details(asin, geo_location, domain)
        db = Database()
        db.insert_product(data)
        return ScrapeResult(success=True, product=data)
    except Exception as exc:  # noqa: BLE001
        return ScrapeResult(success=False, error=str(exc))


def fetch_and_store_competitors(
    parent_asin: str,
    domain: str,
    geo_location: str,
    pages: int = 2,
    reporter: ProgressReporter | None = None,
) -> CompetitorResult:
    """
    Search, scrape, and persist competitor products for a given parent ASIN.

    Returns a CompetitorResult containing all stored competitors plus
    metadata (domain, geo) so app.py can render context chips.
    No st.* calls are made here.
    """
    try:
        db = Database()
        parent = db.get_product(parent_asin)
        if not parent:
            return CompetitorResult(
                success=False,
                error=f"Parent product '{parent_asin}' not found in the database.",
            )

        # Prefer the stored domain/geo from the parent product
        search_domain = parent.get("amazon_domain") or domain
        search_geo = parent.get("geo_location") or geo_location

        # Build a de-duplicated list of category strings
        raw_categories: list[str] = []
        if parent.get("categories"):
            raw_categories.extend(str(c) for c in parent["categories"] if c)
        if parent.get("category_path"):
            raw_categories.extend(str(c) for c in parent["category_path"] if c)

        search_categories = list(
            {cat.strip() for cat in raw_categories if cat and isinstance(cat, str) and cat.strip()}
        )

        # Search competitors across up to 3 categories
        all_results: list[dict[str, Any]] = []
        for category in search_categories[:3]:
            search_results: list[SearchResult] = search_competitors(
                query_title=parent["title"],
                domain=search_domain,
                categories=[category],
                pages=pages,
                geo_location=search_geo,
                reporter=reporter,
            )
            all_results.extend(search_results)

        # De-duplicate and exclude the parent
        competitor_asins = list(
            {
                r.asin
                for r in all_results
                if r.asin and r.asin != parent_asin and r.title
            }
        )

        # Scrape full details (cap at 20)
        multi: MultiScrapeResult = scrape_multiple_products(
            competitor_asins[:20], geo_location, domain, reporter=reporter
        )

        # Persist successful scrapes
        stored: list[dict[str, Any]] = []
        for comp in multi.products:
            comp["parent_asin"] = parent_asin
            db.insert_product(comp)
            stored.append(comp)

        return CompetitorResult(
            success=True,
            competitors=stored,
            search_domain=search_domain,
            search_geo=search_geo,
            failed_asins=multi.failed_asins,
        )

    except Exception as exc:  # noqa: BLE001
        return CompetitorResult(success=False, error=str(exc))