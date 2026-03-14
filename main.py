import streamlit as st
from src.services import scrape_and_store_product, fetch_and_store_competitors, ScrapeResult, CompetitorResult
from src.oxylabs_client import ProgressReporter
from src.tinydb import Database
from src.llm import analyze_competitors, AnalysisOutput

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amazon Competitor Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Background ── */
.stApp {
    background: #0d0f14;
    color: #e8eaf0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2rem 3rem 4rem 3rem;
    max-width: 1280px;
}

/* ── Hero header ── */
.hero {
    background: linear-gradient(135deg, #1a1d27 0%, #141720 100%);
    border: 1px solid #2a2d3a;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(255,153,51,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,153,51,0.12);
    border: 1px solid rgba(255,153,51,0.3);
    color: #ff9933;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 0.9rem;
}
.hero h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f0f2f8;
    margin: 0 0 0.5rem 0;
    line-height: 1.2;
}
.hero p {
    color: #7a7f94;
    font-size: 1rem;
    margin: 0;
    font-weight: 400;
}

/* ── Input panel ── */
.input-panel {
    background: #141720;
    border: 1px solid #22253a;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
}
.panel-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4d5168;
    margin-bottom: 1.2rem;
}

/* ── Streamlit widgets overrides ── */
.stTextInput > label,
.stSelectbox > label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #7a7f94 !important;
    margin-bottom: 4px;
}
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #0d0f14 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #ff9933 !important;
    box-shadow: 0 0 0 3px rgba(255,153,51,0.08) !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    border-radius: 10px;
    border: none;
    transition: all 0.2s;
}
.stButton > button[kind="primary"],
.stButton > button:first-child {
    background: linear-gradient(135deg, #ff9933 0%, #e8801a 100%);
    color: #0d0f14;
    padding: 0.55rem 1.6rem;
    box-shadow: 0 4px 16px rgba(255,153,51,0.25);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255,153,51,0.35);
}
.stButton > button[kind="secondary"] {
    background: #1e2130;
    color: #b0b4cc;
    border: 1px solid #2a2d3a;
}
.stButton > button[kind="secondary"]:hover {
    background: #252a3a;
    color: #e8eaf0;
}

/* ── Product card ── */
.product-card {
    background: #141720;
    border: 1px solid #22253a;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.product-card:hover {
    border-color: #3a3d50;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.product-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e8eaf0;
    margin-bottom: 0.5rem;
    line-height: 1.4;
}
.product-meta {
    font-size: 0.8rem;
    color: #4d5168;
    font-family: 'DM Mono', monospace;
}
.price-badge {
    display: inline-block;
    background: rgba(255,153,51,0.1);
    border: 1px solid rgba(255,153,51,0.25);
    color: #ff9933;
    font-weight: 700;
    font-size: 1.05rem;
    padding: 4px 14px;
    border-radius: 8px;
    margin-bottom: 0.6rem;
}
.tag {
    display: inline-block;
    background: #1e2130;
    color: #7a7f94;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 6px;
    margin-right: 6px;
    margin-bottom: 4px;
    border: 1px solid #2a2d3a;
}
.url-text {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #3a7bd5;
    word-break: break-all;
    margin-top: 0.4rem;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.2rem;
}
.section-header h3 {
    font-size: 1.05rem;
    font-weight: 600;
    color: #e8eaf0;
    margin: 0;
}
.section-dot {
    width: 8px; height: 8px;
    background: #ff9933;
    border-radius: 50%;
    flex-shrink: 0;
}

/* ── Pagination ── */
.page-info {
    font-size: 0.8rem;
    color: #4d5168;
    font-family: 'DM Mono', monospace;
    margin-bottom: 1rem;
}

/* ── Divider ── */
.custom-divider {
    border: none;
    border-top: 1px solid #1e2130;
    margin: 2rem 0;
}

/* ── Competitor section ── */
.competitor-panel {
    background: #141720;
    border: 1px solid #22253a;
    border-radius: 16px;
    padding: 1.8rem 2rem;
}
.asin-chip {
    display: inline-block;
    background: rgba(58,123,213,0.1);
    border: 1px solid rgba(58,123,213,0.3);
    color: #3a7bd5;
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 4px 14px;
    border-radius: 8px;
    margin-left: 8px;
}

/* ── Alert overrides ── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid #2a2d3a !important;
    background: #1a1d27 !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #ff9933 !important;
}

/* ── Number input ── */
.stNumberInput > div > div > input {
    background: #0d0f14 !important;
    border: 1px solid #2a2d3a !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Mono', monospace !important;
    text-align: center;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0d0f14;
    border: 1px solid #22253a;
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
[data-testid="metric-container"] label {
    color: #4d5168 !important;
    font-size: 0.75rem !important;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #ff9933 !important;
    font-weight: 700 !important;
}

/* ── Analysis output ── */
.analysis-output {
    background: #0d0f14;
    border: 1px solid #22253a;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    line-height: 1.7;
    color: #c8cad8;
    font-size: 0.93rem;
}

/* ── Delete buttons ── */
[data-testid*="delete_req"] > button,
[data-testid*="delete_all"] > button {
    background: rgba(220,53,69,0.08) !important;
    border: 1px solid rgba(220,53,69,0.3) !important;
    color: #dc3545 !important;
}
[data-testid*="delete_req"] > button:hover,
[data-testid*="delete_all"] > button:hover {
    background: rgba(220,53,69,0.18) !important;
    color: #ff4d5e !important;
}
.danger-confirm > div > button {
    background: linear-gradient(135deg,#dc3545,#b02a37) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(220,53,69,0.35) !important;
}

/* ── Override primary button for delete confirm keys ── */
button[data-testid="baseButton-primary"][kind="primary"]:has(+ *),
div[data-testid="stButton"]:has(button[key*="confirm_yes"]) > button,
div[data-testid="stButton"]:has(button[key*="confirm_delete_all_yes"]) > button {
    background: linear-gradient(135deg, #dc3545, #b02a37) !important;
    box-shadow: 0 4px 14px rgba(220,53,69,0.3) !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)



# ── Streamlit progress reporter ────────────────────────────────────────────────
class StreamlitReporter:
    """
    Concrete ProgressReporter backed by Streamlit widgets.
    Created fresh per operation; call finish() to clear transient widgets.
    """

    def __init__(self):
        self._status = st.empty()
        self._bar    = st.progress(0.0)

    def set_status(self, message: str) -> None:
        self._status.markdown(
            f'<p style="font-size:0.82rem;color:#7a7f94;font-family:DM Mono,monospace;margin:2px 0">' +
            message + "</p>",
            unsafe_allow_html=True,
        )

    def set_progress(self, value: float) -> None:
        self._bar.progress(min(max(value, 0.0), 1.0))

    def finish(self) -> None:
        self._status.empty()
        self._bar.empty()


# ── Header ─────────────────────────────────────────────────────────────────────
def render_header():
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">🔍 Intelligence Dashboard</div>
        <h1>Amazon Competitor Analysis</h1>
        <p>Enter your ASIN and location to uncover competitive insights instantly.</p>
    </div>
    """, unsafe_allow_html=True)


# ── Input panel ────────────────────────────────────────────────────────────────
def render_inputs():
    st.markdown('<div class="input-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">🎯 Search Parameters</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([3, 2, 2, 1.2])
    with col1:
        asin = st.text_input("ASIN", placeholder="e.g., B0CX23VSAS", label_visibility="visible")
    with col2:
        geo = st.text_input("Zip / Postal Code", placeholder="e.g., 83980")
    with col3:
        domain = st.selectbox("Marketplace", [
            "com", "ca", "co.uk", "de", "fr", "it", "ae"
        ], format_func=lambda x: f"amazon.{x}")
    with col4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        scrape_clicked = st.button("Scrape", use_container_width=True, type="primary")

    st.markdown('</div>', unsafe_allow_html=True)
    return asin.strip(), geo.strip(), domain, scrape_clicked


# ── Product card ───────────────────────────────────────────────────────────────
def render_product_card(product, slot: int = 0):
    asin = product["asin"]
    title = product.get("title") or asin
    currency = product.get("currency", "")
    price = product.get("price", "-")
    brand = product.get("brand", "-")
    prod_type = product.get("product", "-")
    domain_info = f"amazon.{product.get('amazon_domain', 'com')}"
    geo_info = product.get("geo_location", "-")
    url = product.get("url", "")

    price_str = f"{currency} {price}".strip() if currency else str(price)

    col_img, col_info = st.columns([1, 3])

    with col_img:
        images = product.get("images", [])
        if images:
            try:
                st.image(images[0], use_container_width=True)
            except Exception:
                st.markdown("<div style='height:120px;background:#1e2130;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#4d5168;font-size:0.8rem'>No image</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='height:120px;background:#1e2130;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#4d5168;font-size:0.8rem'>No image</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown(f'<div class="product-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="price-badge">{price_str}</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <span class="tag">🏷 {brand}</span>
            <span class="tag">📦 {prod_type}</span>
            <span class="tag">🌐 {domain_info}</span>
            <span class="tag">📍 {geo_info}</span>
        """, unsafe_allow_html=True)
        if url:
            st.markdown(f'<div class="url-text">🔗 {url}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        btn_a, btn_d = st.columns([2, 1])
        with btn_a:
            if st.button("🔎 Analyze Competitors", key=f"analyze_{asin}_{slot}", use_container_width=True):
                st.session_state["analyzing_asin"] = asin
                st.rerun()
        with btn_d:
            if st.button("🗑 Delete", key=f"delete_req_{asin}_{slot}", use_container_width=True):
                st.session_state[f"confirm_delete_{asin}"] = True

    # Inline delete confirmation
    if st.session_state.get(f"confirm_delete_{asin}"):
        st.markdown(f"""
        <div style="
            background: rgba(220,53,69,0.06);
            border: 1px solid rgba(220,53,69,0.28);
            border-radius: 10px;
            padding: 0.85rem 1.1rem;
            margin: 0.3rem 0 0.6rem 0;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        ">
            <span style="font-size:1rem">⚠️</span>
            <span style="color:#ff6b7a;font-size:0.87rem;font-weight:600;line-height:1.4">
                Delete&nbsp;
                <code style="background:rgba(220,53,69,0.18);padding:2px 7px;
                             border-radius:5px;color:#ff9aa3;font-size:0.82rem">{asin}</code>
                &nbsp;and all its competitors? This cannot be undone.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Inject scoped button styles for this confirmation
        st.markdown(f"""
        <style>
        div[data-testid="stButton"] > button[kind="secondary"][id*="confirm_yes_{asin}"] {{
            background: linear-gradient(135deg,#dc3545,#b02a37) !important;
            color: #fff !important;
            border: none !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        cc1, cc2, _ = st.columns([0.9, 0.9, 4.2])
        with cc1:
            if st.button(
                "🗑 Yes, delete",
                key=f"confirm_yes_{asin}_{slot}",
                use_container_width=True,
                type="primary",
            ):
                _db = Database()
                _db.delete_product(asin)
                _db.delete_products_by({"parent_asin": asin})
                st.session_state.pop(f"confirm_delete_{asin}", None)
                if st.session_state.get("analyzing_asin") == asin:
                    st.session_state.pop("analyzing_asin", None)
                st.rerun()
        with cc2:
            if st.button(
                "✖ Cancel",
                key=f"confirm_no_{asin}_{slot}",
                use_container_width=True,
            ):
                st.session_state.pop(f"confirm_delete_{asin}", None)
                st.rerun()

    st.markdown("<hr class='custom-divider' style='margin:0.8rem 0'>", unsafe_allow_html=True)


# ── Analysis renderer ──────────────────────────────────────────────────────────
def render_analysis(result: AnalysisOutput) -> None:
    """Render a structured AnalysisOutput — full width, outside any column context."""

    # ── Row 1: Summary + Positioning side by side ──
    col_sum, col_pos = st.columns(2, gap="medium")

    with col_sum:
        st.markdown(f"""
        <div style="background:#141720;border:1px solid #22253a;border-radius:14px;
                    padding:1.6rem;height:100%">
            <div class="panel-label" style="margin-bottom:0.75rem">📋 Summary</div>
            <p style="color:#c8cad8;font-size:0.92rem;line-height:1.75;margin:0">
                {result.summary}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_pos:
        st.markdown(f"""
        <div style="background:#141720;border:1px solid #22253a;border-radius:14px;
                    padding:1.6rem;height:100%">
            <div class="panel-label" style="margin-bottom:0.75rem">🎯 Positioning</div>
            <p style="color:#c8cad8;font-size:0.92rem;line-height:1.75;margin:0">
                {result.positioning}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Row 2: Top Competitors (full width table) ──
    if result.top_competitors:
        st.markdown("""
        <div class="panel-label" style="margin-bottom:0.75rem">🏆 Top Competitors</div>
        """, unsafe_allow_html=True)

        # Table header
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 3fr;
                    gap:0.5rem;padding:0.5rem 1rem;
                    background:#0d0f14;border-radius:8px 8px 0 0;
                    border:1px solid #2a2d3a;border-bottom:none;margin-bottom:0">
            <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                         text-transform:uppercase;color:#4d5168">Product</span>
            <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                         text-transform:uppercase;color:#4d5168">Price</span>
            <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                         text-transform:uppercase;color:#4d5168">Rating</span>
            <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                         text-transform:uppercase;color:#4d5168">Key Points</span>
        </div>
        """, unsafe_allow_html=True)

        for i, c in enumerate(result.top_competitors):
            pts_html = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(c.key_points) if c.key_points else "—"
            rating_val = f"{'★' * int(round(c.rating))}{'☆' * (5 - int(round(c.rating)))} {c.rating}" if c.rating else "—"
            row_bg = "#141720" if i % 2 == 0 else "#0d0f14"
            border_bottom = "border-radius:0" if i < len(result.top_competitors) - 1 else "border-radius:0 0 8px 8px"

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 3fr;
                        gap:0.5rem;padding:0.75rem 1rem;background:{row_bg};
                        border:1px solid #2a2d3a;border-top:none;{border_bottom};
                        align-items:start">
                <div>
                    <div style="font-size:0.88rem;font-weight:600;color:#e8eaf0;
                                line-height:1.4;margin-bottom:2px">
                        {c.title or c.asin}
                    </div>
                    <span style="font-family:'DM Mono',monospace;font-size:0.72rem;
                                 color:#4d5168">{c.asin}</span>
                </div>
                <div>
                    <span style="background:rgba(255,153,51,0.1);border:1px solid rgba(255,153,51,0.25);
                                 color:#ff9933;font-weight:700;font-size:0.88rem;
                                 padding:3px 10px;border-radius:6px;white-space:nowrap">
                        {c.price_str}
                    </span>
                </div>
                <div style="font-size:0.85rem;color:#f0c040;letter-spacing:1px">
                    {rating_val}
                </div>
                <div style="font-size:0.82rem;color:#7a7f94;line-height:1.6">
                    {pts_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Row 3: Recommendations (2-column grid) ──
    if result.recommendations:
        st.markdown("""
        <div class="panel-label" style="margin-bottom:0.75rem">💡 Recommendations</div>
        """, unsafe_allow_html=True)

        # Split into two columns
        recs = result.recommendations
        mid  = (len(recs) + 1) // 2
        rcol1, rcol2 = st.columns(2, gap="medium")

        for col, chunk in [(rcol1, recs[:mid]), (rcol2, recs[mid:])]:
            with col:
                for i, rec in enumerate(chunk, 1):
                    real_i = (recs[:mid].index(rec) + 1) if col == rcol1 else (mid + recs[mid:].index(rec) + 1)
                    st.markdown(f"""
                    <div style="background:#141720;border:1px solid #22253a;
                                border-left:3px solid #ff9933;border-radius:0 10px 10px 0;
                                padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                                display:flex;gap:0.75rem;align-items:flex-start">
                        <span style="color:#ff9933;font-weight:700;font-size:0.8rem;
                                     font-family:'DM Mono',monospace;flex-shrink:0;
                                     padding-top:2px">{real_i:02d}</span>
                        <span style="color:#c8cad8;font-size:0.88rem;line-height:1.65">
                            {rec}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)



# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    render_header()
    asin, geo, domain, scrape_clicked = render_inputs()

    if scrape_clicked and asin:
        with st.spinner("Scraping product data…"):
            result: ScrapeResult = scrape_and_store_product(asin, geo, domain)
        if result.success:
            st.success("✅ Product scraped successfully!")
        else:
            st.error(f"❌ Scrape failed: {result.error}")
    elif scrape_clicked and not asin:
        st.warning("⚠️ Please enter an ASIN before scraping.")

    db = Database()
    products = db.get_all_products()

    if products:
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        # ── Section header + Delete All + pagination ──
        hcol, del_col, pcol = st.columns([3, 1.2, 1])
        with hcol:
            st.markdown("""
            <div class="section-header">
                <div class="section-dot"></div>
                <h3>Scraped Products</h3>
            </div>
            """, unsafe_allow_html=True)

        items_per_page = 10
        total_pages = max(1, (len(products) + items_per_page - 1) // items_per_page)

        with del_col:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("🗑 Delete All", use_container_width=True, key="delete_all_btn"):
                st.session_state["confirm_delete_all"] = True

        with pcol:
            page = st.number_input(
                "Page", min_value=1, max_value=total_pages, value=1,
                label_visibility="collapsed"
            ) - 1

        # ── Delete All confirmation banner ──
        if st.session_state.get("confirm_delete_all"):
            st.markdown("""
            <div style="
                background: rgba(220,53,69,0.06);
                border: 1px solid rgba(220,53,69,0.28);
                border-radius: 10px;
                padding: 0.85rem 1.1rem;
                margin-bottom: 0.8rem;
                display: flex;
                align-items: center;
                gap: 0.6rem;
            ">
                <span style="font-size:1rem">⚠️</span>
                <span style="color:#ff6b7a;font-size:0.87rem;font-weight:600;line-height:1.4">
                    This will permanently delete <strong style="color:#ff4d5e">ALL</strong>
                    scraped products and their competitors. This cannot be undone.
                </span>
            </div>
            """, unsafe_allow_html=True)
            da1, da2, _ = st.columns([1.2, 1.2, 4])
            with da1:
                if st.button(
                    "🗑 Yes, delete all",
                    key="confirm_delete_all_yes",
                    use_container_width=True,
                    type="primary",
                ):
                    _db = Database()
                    _db.delete_all_products()
                    st.session_state.pop("confirm_delete_all", None)
                    st.session_state.pop("analyzing_asin", None)
                    st.rerun()
            with da2:
                if st.button("✖ Cancel", key="confirm_delete_all_no", use_container_width=True):
                    st.session_state.pop("confirm_delete_all", None)
                    st.rerun()

        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(products))

        st.markdown(
            f'<div class="page-info">Showing {start_idx + 1}–{end_idx} of {len(products)} products &nbsp;|&nbsp; Page {page + 1} of {total_pages}</div>',
            unsafe_allow_html=True
        )

        # Deduplicate by ASIN — keep the last entry (most recently scraped)
        seen: dict = {}
        for p in products:
            if p.get("asin"):
                seen[p["asin"]] = p
        unique_products = list(seen.values())

        # Recalculate pagination on deduplicated list
        total_pages_real = max(1, (len(unique_products) + items_per_page - 1) // items_per_page)
        start_idx = page * items_per_page
        end_idx   = min(start_idx + items_per_page, len(unique_products))

        st.markdown('<div class="input-panel" style="padding:1.2rem 1.6rem">', unsafe_allow_html=True)
        for slot, p in enumerate(unique_products[start_idx:end_idx]):
            render_product_card(p, slot=start_idx + slot)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Competitor analysis panel ──
    selected_asin = st.session_state.get("analyzing_asin")
    if selected_asin:
        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="section-header">
            <div class="section-dot"></div>
            <h3>Competitor Analysis <span class="asin-chip">{selected_asin}</span></h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="competitor-panel">', unsafe_allow_html=True)

        db2 = Database()
        existing_comps = db2.search_products({"parent_asin": selected_asin})

        if not existing_comps:
            reporter = StreamlitReporter()
            comp_result: CompetitorResult = fetch_and_store_competitors(
                selected_asin, domain, geo, reporter=reporter
            )
            if comp_result.success:
                st.markdown(f"""
                    <span class="tag">🌐 {comp_result.search_domain}</span>
                    <span class="tag">📍 {comp_result.search_geo}</span>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.success(f"✅ Found **{comp_result.count}** competitors!")
                if comp_result.failed_asins:
                    st.warning(
                        f"⚠️ **{len(comp_result.failed_asins)}** product(s) could not be scraped: "
                        + ", ".join(comp_result.failed_asins)
                    )
            else:
                st.error(f"❌ {comp_result.error}")
        else:
            st.info(f"📂 **{len(existing_comps)}** competitors already in the database.")

        # ── Action buttons row ──
        btn_col1, btn_col2, _ = st.columns([1.4, 1.4, 3])
        with btn_col1:
            refresh_clicked = st.button("🔄 Refresh Competitors", use_container_width=True)
        with btn_col2:
            analyze_clicked = st.button("🤖 Analyze with AI", type="primary", use_container_width=True)

        # Handle refresh (stays inside competitor-panel)
        if refresh_clicked:
            reporter = StreamlitReporter()
            comp_result: CompetitorResult = fetch_and_store_competitors(
                selected_asin, domain, geo, reporter=reporter
            )
            if comp_result.success:
                st.markdown(f"""
                    <span class="tag">🌐 {comp_result.search_domain}</span>
                    <span class="tag">📍 {comp_result.search_geo}</span>
                """, unsafe_allow_html=True)
                st.success(f"✅ Found **{comp_result.count}** competitors!")
                if comp_result.failed_asins:
                    st.warning(
                        f"⚠️ **{len(comp_result.failed_asins)}** product(s) could not be scraped: "
                        + ", ".join(comp_result.failed_asins)
                    )
            else:
                st.error(f"❌ {comp_result.error}")

        # Close competitor-panel BEFORE rendering analysis (full width)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── AI Analysis — full width, outside competitor-panel ──
        if analyze_clicked:
            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="section-header">
                <div class="section-dot"></div>
                <h3>AI Analysis Report</h3>
            </div>
            """, unsafe_allow_html=True)
            with st.spinner("Running AI analysis…"):
                try:
                    analysis: AnalysisOutput = analyze_competitors(selected_asin)
                    st.session_state["analysis_result"] = analysis
                    st.session_state["analysis_asin"]   = selected_asin
                    render_analysis(analysis)
                except Exception as exc:
                    st.error(f"❌ AI analysis failed: {exc}")

        # Persist analysis result across reruns via session state
        if analyze_clicked and "analysis_result" in st.session_state:
            del st.session_state["analysis_result"]

        if "analysis_result" in st.session_state and st.session_state.get("analysis_asin") == selected_asin:
            st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
            st.markdown("""
            <div class="section-header">
                <div class="section-dot"></div>
                <h3>AI Analysis Report</h3>
            </div>
            """, unsafe_allow_html=True)
            render_analysis(st.session_state["analysis_result"])


if __name__ == "__main__":
    main()