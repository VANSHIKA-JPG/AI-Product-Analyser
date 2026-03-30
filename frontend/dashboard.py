"""
AI Product Analyser — Streamlit Dashboard.

Interactive frontend for analyzing Amazon products with
sentiment analysis, fake review detection, and AI summaries.

Run: streamlit run frontend/dashboard.py
"""

import json
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Product Analyser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API Configuration ─────────────────────────────────────────────────────
API_BASE = "http://localhost:5000/api"


# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #333;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #aaa;
        margin-top: 5px;
    }
    .risk-low { color: #00c853; }
    .risk-medium { color: #ffab00; }
    .risk-high { color: #ff1744; }
    .recommendation-buy { color: #00c853; font-weight: 700; }
    .recommendation-skip { color: #ff1744; font-weight: 700; }
    .recommendation-maybe { color: #ffab00; font-weight: 700; }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("🔍 AI Analyser")
    page = st.radio(
        "Navigation",
        ["🏠 Analyse Product", "📊 Compare Products", "📜 History"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("v1.0.0 | Powered by Gemini AI")


# ── Helper Functions ───────────────────────────────────────────────────────

def create_sentiment_gauge(score: float, title: str = "Sentiment Score") -> go.Figure:
    """Create a gauge chart for sentiment score."""
    color = "#00c853" if score > 0.2 else ("#ff1744" if score < -0.2 else "#ffab00")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round((score + 1) / 2 * 100, 1),  # Convert -1..1 to 0..100
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 16, "color": "#ddd"}},
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#888"}},
            "bar": {"color": color},
            "bgcolor": "#1a1a2e",
            "bordercolor": "#333",
            "steps": [
                {"range": [0, 33], "color": "rgba(255,23,68,0.15)"},
                {"range": [33, 66], "color": "rgba(255,171,0,0.15)"},
                {"range": [66, 100], "color": "rgba(0,200,83,0.15)"},
            ],
        },
    ))
    fig.update_layout(
        height=250,
        margin=dict(t=40, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ddd"},
    )
    return fig


def create_trust_gauge(score: float) -> go.Figure:
    """Create a gauge chart for trust score."""
    color = "#00c853" if score >= 70 else ("#ffab00" if score >= 40 else "#ff1744")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Trust Score", "font": {"size": 16, "color": "#ddd"}},
        number={"suffix": "/100", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#888"}},
            "bar": {"color": color},
            "bgcolor": "#1a1a2e",
            "bordercolor": "#333",
            "threshold": {
                "line": {"color": "#ff1744", "width": 2},
                "thickness": 0.75,
                "value": 40,
            },
        },
    ))
    fig.update_layout(
        height=250,
        margin=dict(t=40, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ddd"},
    )
    return fig


def create_sentiment_distribution(distribution: dict) -> go.Figure:
    """Create a bar chart for sentiment distribution."""
    labels = list(distribution.keys())
    values = list(distribution.values())
    colors = ["#ff1744", "#ff6d00", "#ffab00", "#69f0ae", "#00c853"]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=values,
        textposition="auto",
    ))
    fig.update_layout(
        title={"text": "Sentiment Distribution", "font": {"size": 16, "color": "#ddd"}},
        xaxis_title="Sentiment",
        yaxis_title="Count",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ddd"},
        xaxis={"gridcolor": "#333"},
        yaxis={"gridcolor": "#333"},
    )
    return fig


def create_aspect_radar(aspects: dict) -> go.Figure:
    """Create a radar chart for aspect-based sentiment."""
    valid_aspects = {k: v for k, v in aspects.items() if v.get("score") is not None}
    if not valid_aspects:
        return None

    categories = list(valid_aspects.keys())
    scores = [(v["score"] + 1) / 2 * 100 for v in valid_aspects.values()]
    # Close the radar
    categories.append(categories[0])
    scores.append(scores[0])

    fig = go.Figure(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill="toself",
        fillcolor="rgba(102,126,234,0.2)",
        line={"color": "#667eea", "width": 2},
        marker={"size": 6, "color": "#667eea"},
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#333", tickfont={"color": "#888"}),
            angularaxis=dict(gridcolor="#333", tickfont={"color": "#ddd"}),
        ),
        title={"text": "Aspect Analysis", "font": {"size": 16, "color": "#ddd"}},
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ddd"},
        margin=dict(t=50, b=30),
    )
    return fig


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict | None:
    """Make an API call and return the response."""
    try:
        url = f"{API_BASE}/{endpoint}"
        if method == "POST":
            resp = requests.post(url, json=data, timeout=120)
        else:
            resp = requests.get(url, timeout=30)

        if resp.status_code == 200:
            return resp.json().get("data")
        else:
            error = resp.json().get("message", "Unknown error")
            st.error(f"API Error: {error}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Run `python app.py` first!")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ── Page: Analyse Product ─────────────────────────────────────────────────
if page == "🏠 Analyse Product":
    st.markdown('<h1 class="main-header">🔍 AI Product Analyser</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Paste an Amazon product URL to get AI-powered insights</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        url = st.text_input(
            "Amazon Product URL",
            placeholder="https://www.amazon.in/dp/XXXXXXXXXX",
            label_visibility="collapsed",
        )
    with col2:
        analyze_btn = st.button("🚀 Analyse", use_container_width=True)

    if analyze_btn and url:
        with st.spinner("🔄 Scraping reviews & running AI analysis... This may take 1-2 minutes."):
            result = call_api("analyze", method="POST", data={"url": url})

        if result:
            product = result.get("product", {})
            sentiment = result.get("sentiment", {})
            trust = result.get("trust", {})
            ai_summary = result.get("ai_summary", {})
            value = result.get("value_analysis", {})

            # ── Product Info ───────────────────────────────────────
            st.divider()
            col1, col2 = st.columns([1, 3])
            with col1:
                if product.get("image_url"):
                    st.image(product["image_url"], width=200)
            with col2:
                st.subheader(product.get("name", "Unknown Product"))
                pcol1, pcol2, pcol3 = st.columns(3)
                pcol1.metric("Price", f"₹{product.get('price', 'N/A')}")
                pcol2.metric("Rating", f"{product.get('average_rating', 'N/A')} ⭐")
                pcol3.metric("Reviews Analyzed", result.get("reviews_count", 0))

            st.divider()

            # ── Key Metrics Row ────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.plotly_chart(
                    create_sentiment_gauge(sentiment.get("overall_score", 0)),
                    use_container_width=True,
                )
            with m2:
                st.plotly_chart(
                    create_trust_gauge(trust.get("score", 0)),
                    use_container_width=True,
                )
            with m3:
                rec = ai_summary.get("recommendation", "N/A")
                rec_color = {"buy": "🟢", "skip": "🔴", "maybe": "🟡"}.get(rec, "⚪")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{rec_color} {rec.upper()}</div>
                    <div class="metric-label">AI Recommendation</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{value.get('value_score', 0)}/100</div>
                    <div class="metric-label">Value Score</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # ── AI Summary ─────────────────────────────────────────
            st.subheader("🤖 AI Summary")
            st.write(ai_summary.get("summary", "No summary available"))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Pros**")
                pros = ai_summary.get("pros", [])
                for pro in pros:
                    st.markdown(f"- {pro}")
            with col2:
                st.markdown("**❌ Cons**")
                cons = ai_summary.get("cons", [])
                for con in cons:
                    st.markdown(f"- {con}")

            if ai_summary.get("recommendation_reason"):
                st.info(f"💡 **Recommendation Reason**: {ai_summary['recommendation_reason']}")

            st.divider()

            # ── Charts Row ─────────────────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                dist = sentiment.get("distribution", {})
                if dist:
                    st.plotly_chart(
                        create_sentiment_distribution(dist),
                        use_container_width=True,
                    )
            with col2:
                aspects = sentiment.get("aspects", {})
                radar = create_aspect_radar(aspects)
                if radar:
                    st.plotly_chart(radar, use_container_width=True)

            # ── Trust Details ──────────────────────────────────────
            st.divider()
            st.subheader("🛡️ Review Trust Analysis")
            t1, t2, t3 = st.columns(3)
            t1.metric("Suspicious Reviews", f"{trust.get('suspicious_count', 0)}/{trust.get('total_analyzed', 0)}")
            t2.metric("Suspicious %", f"{trust.get('suspicious_pct', 0)}%")
            risk = trust.get("risk_level", "unknown")
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk, "⚪")
            t3.metric("Risk Level", f"{risk_emoji} {risk.upper()}")

            # ── Value Analysis ─────────────────────────────────────
            st.divider()
            st.subheader("💰 Value Analysis")
            st.write(f"**Price Category**: {value.get('price_category', 'N/A').title()}")
            st.write(f"**Verdict**: {value.get('verdict', 'N/A')}")


# ── Page: Compare Products ─────────────────────────────────────────────────
elif page == "📊 Compare Products":
    st.markdown('<h1 class="main-header">📊 Product Comparison</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Compare up to 5 Amazon products side by side</p>', unsafe_allow_html=True)

    num_products = st.slider("Number of products to compare", 2, 5, 2)
    urls = []
    for i in range(num_products):
        url = st.text_input(f"Product {i+1} URL", key=f"compare_url_{i}",
                            placeholder="https://www.amazon.in/dp/XXXXXXXXXX")
        if url:
            urls.append(url)

    if st.button("🔄 Compare Products") and len(urls) >= 2:
        with st.spinner("Comparing products..."):
            result = call_api("compare", method="POST", data={"urls": urls})

        if result:
            comparison = result.get("comparison", [])
            if comparison:
                st.divider()
                cols = st.columns(len(comparison))
                for i, product in enumerate(comparison):
                    with cols[i]:
                        badge = "🥇" if product.get("best_value") else f"#{product.get('rank', i+1)}"
                        st.markdown(f"### {badge} {product.get('name', 'Unknown')[:40]}")
                        st.metric("Price", f"₹{product.get('price', 'N/A')}")
                        st.metric("Rating", f"{product.get('rating', 'N/A')} ⭐")
                        st.metric("Value Score", f"{product.get('value_score', 0)}/100")
                        st.write(f"**{product.get('verdict', '')}**")


# ── Page: History ──────────────────────────────────────────────────────────
elif page == "📜 History":
    st.markdown('<h1 class="main-header">📜 Analysis History</h1>', unsafe_allow_html=True)

    result = call_api("history")

    if result:
        analyses = result.get("results", [])
        if not analyses:
            st.info("No analyses yet. Go to 'Analyse Product' to get started!")
        else:
            for item in analyses:
                analysis = item.get("analysis", {})
                product = item.get("product", {})
                with st.expander(
                    f"📦 {product.get('name', 'Unknown')[:60]} — "
                    f"Score: {analysis.get('overall_sentiment_score', 'N/A')} | "
                    f"Trust: {analysis.get('trust_score', 'N/A')}/100"
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Sentiment", f"{analysis.get('positive_percentage', 0)}% positive")
                    c2.metric("Trust", f"{analysis.get('trust_score', 0)}/100")
                    c3.metric("Recommendation", analysis.get("recommendation", "N/A"))
                    st.write(analysis.get("ai_summary", "No summary"))
                    st.caption(f"Analyzed: {analysis.get('analyzed_at', 'Unknown date')}")

    pagination = result.get("pagination", {}) if result else {}
    if pagination.get("pages", 0) > 1:
        st.write(f"Page {pagination['page']} of {pagination['pages']}")
