"""
src/llm.py
──────────
LLM analysis layer. Returns a structured AnalysisOutput object —
app.py is responsible for all rendering. No st.* calls here.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# ── Pydantic output models ─────────────────────────────────────────────────────

class CompetitorInsights(BaseModel):
    asin: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    key_points: List[str] = Field(default_factory=list)

    @property
    def price_str(self) -> str:
        """Formatted price string with correct currency symbol."""
        if self.price is None:
            return "N/A"
        symbol = self.currency.strip() if self.currency else "$"
        return f"{symbol} {self.price:,.2f}"


class AnalysisOutput(BaseModel):
    summary: str
    positioning: str
    top_competitors: List[CompetitorInsights] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_competitors(db, parent_asin: str) -> list[dict]:
    """Pull competitor rows from DB and normalise into a flat list of dicts."""
    comps = db.search_products({"parent_asin": parent_asin})
    return [
        {
            "asin":          c.get("asin"),
            "title":         c.get("title"),
            "price":         c.get("price"),
            "currency":      c.get("currency"),
            "rating":        c.get("rating"),
            "amazon_domain": c.get("amazon_domain"),
        }
        for c in comps
    ]


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_competitors(asin: str) -> AnalysisOutput:
    """
    Run LLM-based competitor analysis for a given parent ASIN.

    Uses Google Gemini via langchain_google_genai.
    Returns a structured AnalysisOutput — app.py renders it.
    Raises on LLM / DB errors so app.py can show st.error().
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from src.tinydb import Database

    db          = Database()
    product     = db.get_product(asin)
    competitors = _format_competitors(db, asin)

    parser = PydanticOutputParser(pydantic_object=AnalysisOutput)

    system_msg = (
        "You are a senior market analyst. "
        "Respond ONLY with valid JSON that matches the schema below — "
        "no markdown fences, no extra text.\n\n"
        "{format_instructions}"
    )

    human_msg = (
        "Analyse the product and its competitors.\n\n"
        "## Product\n"
        "- Title:         {product_title}\n"
        "- Brand:         {brand}\n"
        "- Price:         {currency} {price}\n"
        "- Rating:        {rating}\n"
        "- Categories:    {categories}\n"
        "- Amazon Domain: {amazon_domain}\n\n"
        "## Competitors (JSON)\n"
        "{competitors}\n\n"
        "IMPORTANT: Always display prices with their correct currency symbol "
        "and compare prices within the same currency context."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human",  human_msg),
    ]).partial(format_instructions=parser.get_format_instructions())

    # Model fallback list — tried in order until one succeeds
    # gemini-1.5-* and older are retired (404). Use 2.5 series only.
    MODELS = [
        "gemini-2.5-flash-lite-preview-06-17",   # fastest, highest free RPD
        "gemini-2.5-flash",                       # balanced
        "gemini-2.5-pro",                         # most capable, lower RPD
    ]

    invoke_kwargs = {
        "product_title": product.get("title")                  if product else asin,
        "brand":         product.get("brand", "")              if product else "",
        "price":         product.get("price", "N/A")           if product else "N/A",
        "currency":      product.get("currency", "")           if product else "",
        "rating":        product.get("rating", "N/A")          if product else "N/A",
        "categories":    json.dumps(product.get("categories", [])) if product else "[]",
        "amazon_domain": product.get("amazon_domain", "com")   if product else "com",
        "competitors":   json.dumps(competitors, ensure_ascii=False),
    }

    last_error: Exception | None = None

    for model_name in MODELS:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        chain = prompt | llm | parser

        # Retry up to 3 times with exponential backoff for rate-limit errors
        for attempt in range(3):
            try:
                result: AnalysisOutput = chain.invoke(invoke_kwargs)
                return result
            except Exception as exc:
                last_error = exc
                err_str = str(exc).lower()
                is_rate_limit = "429" in str(exc) or "resource_exhausted" in err_str or "quota" in err_str
                if is_rate_limit and attempt < 2:
                    wait = 15 * (attempt + 1)   # 15s → 30s
                    time.sleep(wait)
                    continue
                break   # non-rate-limit error or retries exhausted → try next model

    raise RuntimeError(
        f"All Gemini models exhausted. Last error: {last_error}"
    )