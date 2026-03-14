from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

import requests
from dotenv import load_dotenv

load_dotenv()

OXYLABS_BASE_URL = "https://realtime.oxylabs.io/v1/queries"


# ── Progress reporter protocol ─────────────────────────────────────────────────

@runtime_checkable
class ProgressReporter(Protocol):
    """
    Thin interface injected by app.py so the client can report progress
    without importing streamlit.

    app.py creates a concrete implementation backed by st.progress /
    st.empty; tests can pass a no-op or a recorder.
    """

    def set_status(self, message: str) -> None:
        """Short one-line status update (e.g. 'Scraping 3/20: B0ABC…')."""
        ...

    def set_progress(self, value: float) -> None:
        """Progress fraction in [0.0, 1.0]."""
        ...

    def finish(self) -> None:
        """Called once when the operation completes; clears transient widgets."""
        ...


class NoopReporter:
    """Silent fallback — used when no reporter is injected (e.g. unit tests)."""

    def set_status(self, message: str) -> None:
        pass

    def set_progress(self, value: float) -> None:
        pass

    def finish(self) -> None:
        pass


# ── Result containers ──────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """A single competitor hit from amazon_search."""
    asin: str
    title: str
    category: str | None = None
    price: float | None = None
    rating: float | None = None


@dataclass
class MultiScrapeResult:
    """
    Returned by scrape_multiple_products.
    Carries both the products that succeeded and the ASINs that failed
    so callers can surface partial-failure warnings.
    """
    products: list[dict[str, Any]] = field(default_factory=list)
    failed_asins: list[str] = field(default_factory=list)

    @property
    def total_attempted(self) -> int:
        return len(self.products) + len(self.failed_asins)

    @property
    def success_count(self) -> int:
        return len(self.products)


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _post_query(payload: dict[str, Any]) -> dict[str, Any]:
    """POST a single query to Oxylabs and return the parsed JSON."""
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")

    response = requests.post(
        OXYLABS_BASE_URL,
        auth=(username, password),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _extract_content(payload: Any) -> dict[str, Any]:
    """Unwrap Oxylabs envelope and return the innermost content dict."""
    if isinstance(payload, dict):
        if "results" in payload:
            results = payload["results"]
            if isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "content" in first:
                    return first["content"] or {}
        if "content" in payload:
            return payload.get("content") or {}
    return payload if isinstance(payload, dict) else {}


# ── Normalisation helpers ──────────────────────────────────────────────────────

def _normalize_product(content: dict[str, Any]) -> dict[str, Any]:
    category_path = [
        cat.strip()
        for cat in (content.get("category_path") or [])
        if cat
    ]
    return {
        "asin":             content.get("asin"),
        "url":              content.get("url"),
        "brand":            content.get("brand"),
        "price":            content.get("price"),
        "stock":            content.get("stock"),
        "title":            content.get("title"),
        "rating":           content.get("rating"),
        "images":           content.get("images") or [],
        "categories":       content.get("category") or content.get("categories") or [],
        "category_path":    category_path,
        "currency":         content.get("currency"),
        "buybox":           content.get("buybox") or [],
        "product_overview": content.get("product_overview") or [],
    }


def _clean_product_name(title: str) -> str:
    """Strip brand suffixes separated by – or | to get a cleaner search term."""
    for sep in ("-", "|"):
        if sep in title:
            title = title.split(sep)[0]
    return title.strip()


def _extract_search_results(content: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not isinstance(content, dict):
        return items

    if "results" in content:
        results = content["results"]
        if isinstance(results, dict):
            if "organic" in results:
                items.extend(results["organic"])
            if "paid" in results:
                items.extend(results["paid"])
    elif "products" in content and isinstance(content["products"], list):
        items.extend(content["products"])

    return items


def _normalize_search_result(item: dict[str, Any]) -> SearchResult | None:
    asin  = item.get("asin") or item.get("product_asin")
    title = item.get("title")
    if not (asin and title):
        return None
    return SearchResult(
        asin=asin,
        title=title,
        category=item.get("category"),
        price=item.get("price"),
        rating=item.get("rating"),
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def scrape_product_details(
    asin: str,
    geo_location: str,
    domain: str,
) -> dict[str, Any]:
    """
    Scrape a single Amazon product by ASIN.
    Raises requests.HTTPError on network failures.
    """
    payload = {
        "source":       "amazon_product",
        "query":        asin,
        "geo_location": geo_location,
        "domain":       domain,
        "parse":        True,
    }
    raw        = _post_query(payload)
    content    = _extract_content(raw)
    normalized = _normalize_product(content)

    if not normalized.get("asin"):
        normalized["asin"] = asin

    normalized["amazon_domain"] = domain
    normalized["geo_location"]  = geo_location
    return normalized


def search_competitors(
    query_title: str,
    domain: str,
    categories: list[str],
    pages: int = 1,
    geo_location: str = "",
    reporter: ProgressReporter | None = None,
) -> list[SearchResult]:
    """
    Search Amazon for competitor products across multiple sort strategies.

    Progress is reported via `reporter` (no st.* calls here).
    Returns a de-duplicated list of SearchResult objects.
    """
    rep          = reporter or NoopReporter()
    search_title = _clean_product_name(query_title)
    results:     list[SearchResult] = []
    seen_asins:  set[str]           = set()
    strategies   = ["featured", "price_asc", "price_desc", "avg_rating"]
    total_calls  = len(strategies) * max(1, pages)
    call_count   = 0

    rep.set_status("Searching for competitors…")

    for sort_by in strategies:
        for page in range(1, max(1, pages) + 1):
            call_count += 1
            rep.set_progress(call_count / total_calls)
            rep.set_status(f"Searching — strategy: {sort_by}, page {page}/{pages}")

            payload: dict[str, Any] = {
                "source":       "amazon_search",
                "query":        search_title,
                "parse":        True,
                "domain":       domain,
                "page":         page,
                "sort_by":      sort_by,
                "geo_location": geo_location,
            }
            if categories and categories[0]:
                payload["refinements"] = {"category": categories[0]}

            content = _extract_content(_post_query(payload))
            items   = _extract_search_results(content)

            for item in items:
                result = _normalize_search_result(item)
                if result and result.asin not in seen_asins:
                    seen_asins.add(result.asin)
                    results.append(result)

            time.sleep(0.1)

    rep.set_status(f"Search complete — {len(results)} unique competitors found.")
    rep.finish()
    return results


def scrape_multiple_products(
    asins: list[str],
    geo_location: str,
    domain: str,
    reporter: ProgressReporter | None = None,
) -> MultiScrapeResult:
    """
    Scrape full product details for a list of ASINs.

    Progress is reported via `reporter`. Returns a MultiScrapeResult
    that separates successful scrapes from failed ones so callers can
    show partial-failure warnings through their own UI layer.
    """
    rep     = reporter or NoopReporter()
    total   = len(asins)
    result  = MultiScrapeResult()

    rep.set_status(f"Preparing to scrape {total} products…")
    rep.set_progress(0.0)

    for idx, asin in enumerate(asins, 1):
        rep.set_status(f"Scraping competitor {idx}/{total}: {asin}")
        rep.set_progress(idx / total)

        try:
            product = scrape_product_details(asin, geo_location, domain)
            result.products.append(product)
        except Exception:  # noqa: BLE001
            result.failed_asins.append(asin)

        time.sleep(0.1)

    rep.set_status(
        f"Done — {result.success_count}/{total} scraped successfully."
        + (f" ({len(result.failed_asins)} failed)" if result.failed_asins else "")
    )
    rep.finish()
    return result