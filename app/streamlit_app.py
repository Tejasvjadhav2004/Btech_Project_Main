"""
Supplier Management System — Streamlit UI
Connects to the FastAPI backend at http://localhost:8000
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API = "http://localhost:8000"

st.set_page_config(
    page_title="Supplier Management System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar Navigation ──────────────────────────────────────────────────────

st.sidebar.title("🏭 Supplier Agent")
st.sidebar.caption("AI-powered Procurement System")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🤖 AI Recommend", "🔍 Product Search", "📈 Performance", "💬 Ask AI Agent"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("Backend: FastAPI + PostgreSQL\nAI: LSTM + LangChain + GPT")

# ── API Key Input ─────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Access Key")
api_key = st.sidebar.text_input(
    "Enter your API Key",
    type="password",
    placeholder="key-xxxx-xxxxxxxxxxxx",
    help="Contact the project admin (Prashant) for your personal key.",
)
if not api_key:
    st.sidebar.warning("Enter your API key to use the app.")


# ── Helper ───────────────────────────────────────────────────────────────────

def _headers() -> dict:
    return {"X-API-Key": api_key} if api_key else {}

def get(path: str):
    try:
        r = requests.get(f"{API}{path}", headers=_headers(), timeout=10)
        if r.status_code == 403:
            st.error("🔒 Access denied. Enter a valid API key in the sidebar.")
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Make sure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_products() -> list:
    """Fetch all known product names from the backend for autocomplete."""
    try:
        r = requests.get(f"{API}/supplier/products", headers=_headers(), timeout=10)
        if r.status_code == 200:
            return r.json().get("products", [])
    except Exception:
        pass
    return []

def post(path: str, data: dict):
    try:
        r = requests.post(f"{API}{path}", json=data, headers=_headers(), timeout=60)
        if r.status_code == 403:
            st.error("🔒 Access denied. Enter a valid API key in the sidebar.")
            return None
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Make sure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.title("📊 Supplier Dashboard")
    st.caption("Overview of all registered suppliers and their current KPIs")

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh Metrics"):
            result = post("/supplier/update-metrics", {})
            if result:
                st.success(result.get("message", "Metrics updated!"))

    suppliers = get("/supplier/list")
    if not suppliers:
        st.info("No suppliers found. Click **Refresh Metrics** to seed data.")
        st.stop()

    df = pd.DataFrame(suppliers)

    # ── KPI Cards ────────────────────────────────────────────────────────────
    st.markdown("### Key Metrics")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Suppliers", len(df))
    k2.metric("Avg Reliability", f"{df['reliability_score'].mean():.1f}%")
    k3.metric("Avg Lead Time", f"{df['avg_lead_time_days'].mean():.1f} days")
    k4.metric("Avg Quality", f"{df['quality_rating'].mean():.2f} / 5")

    st.markdown("---")

    # ── Reliability Bar Chart ────────────────────────────────────────────────
    st.markdown("### Reliability Scores")
    df_sorted = df.sort_values("reliability_score", ascending=False)
    fig_bar = px.bar(
        df_sorted,
        x="name",
        y="reliability_score",
        color="reliability_score",
        color_continuous_scale="RdYlGn",
        range_color=[70, 100],
        labels={"name": "Supplier", "reliability_score": "Reliability (%)"},
        height=380,
    )
    fig_bar.update_layout(
        xaxis_tickangle=-35,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=30, b=100),
    )
    st.plotly_chart(fig_bar, width="stretch")

    # ── Scatter: Quality vs Lead Time ─────────────────────────────────────────
    st.markdown("### Quality vs Lead Time")
    fig_scatter = px.scatter(
        df,
        x="avg_lead_time_days",
        y="quality_rating",
        size="reliability_score",
        color="reliability_score",
        color_continuous_scale="Blues",
        hover_name="name",
        labels={
            "avg_lead_time_days": "Avg Lead Time (days)",
            "quality_rating": "Quality Rating (1-5)",
            "reliability_score": "Reliability %",
        },
        height=400,
    )
    st.plotly_chart(fig_scatter, width="stretch")

    # ── Full Table ─────────────────────────────────────────────────────────────
    st.markdown("### All Suppliers")
    display_df = df[["id","name","location","specialties","reliability_score","avg_lead_time_days","quality_rating"]].copy()
    display_df.columns = ["ID","Name","Location","Specialties","Reliability (%)","Lead Time (days)","Quality (1-5)"]
    st.dataframe(display_df, width="stretch", hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — AI Recommend
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🤖 AI Recommend":
    st.title("🤖 AI Supplier Recommendation")
    st.caption("Blended score: 70% Weighted Utility Model + 30% LSTM Deep Learning prediction")

    # ── Product autocomplete (outside form so it updates live) ───────────────
    known_products = fetch_products()
    col_prod, col_custom = st.columns([3, 2])
    with col_prod:
        selected_product = st.selectbox(
            "📦 Select a product",
            options=known_products,
            index=None,
            placeholder="Type to search known products...",
        )
    with col_custom:
        custom_product = st.text_input(
            "Or enter a custom product name",
            placeholder="e.g. Custom Gear, Special Part",
        )
    item_name = selected_product or custom_product
    if item_name:
        st.caption(f"✅ Product selected: **{item_name}**")

    with st.form("recommend_form"):
        col1, col2 = st.columns(2)
        with col1:
            quantity  = st.number_input("Quantity Required", min_value=1, value=100)
        with col2:
            max_lead  = st.number_input("Max Lead Time (days)", min_value=0, value=0,
                                        help="Leave 0 for no constraint")
            max_price = st.number_input("Max Price per Unit (₹)", min_value=0.0, value=0.0, step=10.0,
                                        help="Leave 0 for no constraint")
            priority  = st.selectbox("Priority", ["balanced", "cost", "speed", "quality"])

        submitted = st.form_submit_button("🚀 Get Recommendations", width="stretch")

    if submitted:
        if not item_name:
            st.warning("Please select or enter a product name above.")
        else:
            payload = {
                "item_name": item_name,
                "quantity": int(quantity),
                "max_lead_time_days": int(max_lead) if max_lead > 0 else None,
                "max_price_per_unit": float(max_price) if max_price > 0 else None,
                "priority": priority,
            }
            with st.spinner("Finding the best suppliers for you..."):
                result = post("/supplier/recommend", payload)

            if result:
                best = result.get("best_choice")
                recs = result.get("recommendations", [])

                if best:
                    st.success(f"✅ Best Choice: **{best['supplier_name']}**")
                    b1, b2, b3, b4 = st.columns(4)
                    b1.metric("AI Score", f"{best['utility_score']}")
                    b2.metric("Est. Total Cost", f"₹{best['estimated_total_cost']:,.0f}")
                    b3.metric("Lead Time", f"{best['estimated_lead_time']} days")
                    b4.metric("Rationale", "See below ↓")
                    st.info(f"💡 {best['rationale']}")

                st.markdown("### Top Recommendations")
                if recs:
                    df_recs = pd.DataFrame(recs)
                    df_recs = df_recs[["supplier_name","utility_score","estimated_total_cost","estimated_lead_time","rationale"]]
                    df_recs.columns = ["Supplier","AI Score","Est. Cost (₹)","Lead Time (days)","Rationale"]
                    df_recs.index = range(1, len(df_recs)+1)

                    fig = px.bar(
                        df_recs.reset_index(),
                        x="Supplier",
                        y="AI Score",
                        color="AI Score",
                        color_continuous_scale="Greens",
                        height=320,
                    )
                    fig.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig, width="stretch")
                    st.dataframe(df_recs, width="stretch")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Product Search
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🔍 Product Search":
    st.title("🔍 Product Supplier Search")
    st.caption("Finds suppliers by product name, past order history, and specialty keywords")

    # ── Product autocomplete (outside form so it updates live) ───────────────
    known_products = fetch_products()
    col_prod2, col_custom2 = st.columns([3, 2])
    with col_prod2:
        selected_product2 = st.selectbox(
            "📦 Select a product",
            options=known_products,
            index=None,
            placeholder="Type to search known products...",
            key="ps_select",
        )
    with col_custom2:
        custom_product2 = st.text_input(
            "Or enter a custom product name",
            placeholder="e.g. Custom Part, New Item",
            key="ps_custom",
        )
    product = selected_product2 or custom_product2
    if product:
        st.caption(f"✅ Product selected: **{product}**")

    with st.form("search_form"):
        col2, col3 = st.columns(2)
        with col2:
            qty      = st.number_input("Quantity", min_value=1, value=50)
            top_n    = st.slider("Top N Suppliers", 1, 10, 3)
        with col3:
            ml_days  = st.number_input("Max Lead Time (days, 0=any)", min_value=0, value=0)
            ml_price = st.number_input("Max Price/Unit ₹ (0=any)", min_value=0.0, value=0.0, step=5.0)

        search_btn = st.form_submit_button("🔍 Search", width="stretch")

    if search_btn:
        if not product:
            st.warning("Please select or enter a product name above.")
        else:
            payload = {
                "product": product,
                "quantity": int(qty),
                "top_n": int(top_n),
                "max_lead_time_days": int(ml_days) if ml_days > 0 else None,
                "max_price_per_unit": float(ml_price) if ml_price > 0 else None,
            }
            with st.spinner("Searching suppliers for your product..."):
                result = post("/supplier/search", payload)

            if result:
                st.success(f"🏆 Best: **{result['best_supplier_name']}**")
                st.info(result['summary'])

                st.markdown("### Matched Suppliers")
                tops = result.get("top_suppliers", [])
                for i, s in enumerate(tops, 1):
                    with st.expander(f"#{i} {s['supplier_name']} — Score: {s['utility_score']}", expanded=(i==1)):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Reliability", f"{s['reliability_score']}%")
                        c2.metric("Lead Time", f"{s['avg_lead_time_days']} days")
                        c3.metric("Quality", f"{s['quality_rating']}/5")
                        c4.metric("Est. Cost", f"₹{s['estimated_total_cost']:,.0f}")
                        st.write(f"📍 {s['location']}  |  🏷️ {s['specialties']}")
                        st.write(f"📦 Past orders for this product: {s['past_orders_for_product']}")
                        st.caption(s['rationale'])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Performance Report
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📈 Performance":
    st.title("📈 Supplier Performance Report")
    st.caption("Historical analysis: On-Time Delivery, Quality, Prices + Customer Reviews")

    suppliers = get("/supplier/list")
    if not suppliers:
        st.stop()

    names = {s["name"]: s["id"] for s in suppliers}
    chosen = st.selectbox("Select Supplier", list(names.keys()))

    if st.button("📊 Load Report", width="content"):
        sup_id = names[chosen]
        with st.spinner("Loading performance report..."):
            report = get(f"/supplier/performance/{sup_id}")

        if report:
            s = report["supplier"]
            st.markdown(f"## {s['name']}")
            st.caption(f"📍 {s['location']}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Orders", report["total_orders"])
            m2.metric("On-Time Delivery", f"{report['on_time_delivery_rate']}%")
            m3.metric("Avg Quality", f"{report['avg_quality']} / 5")

            st.markdown("---")

            gd = report["graph_data"]
            if gd["months"]:
                col_l, col_r = st.columns(2)

                with col_l:
                    st.markdown("#### On-Time Delivery % (Last 12 orders)")
                    fig_otd = go.Figure()
                    fig_otd.add_trace(go.Scatter(
                        x=gd["months"], y=gd["otd_rates"],
                        mode="lines+markers",
                        line=dict(color="#2ecc71", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(46,204,113,0.12)",
                        name="OTD %"
                    ))
                    fig_otd.update_layout(height=280, margin=dict(l=20,r=20,t=30,b=40),
                                          yaxis=dict(range=[0,110]))
                    st.plotly_chart(fig_otd, width="stretch")

                with col_r:
                    st.markdown("#### Quality Scores (Last 12 orders)")
                    fig_q = go.Figure()
                    fig_q.add_trace(go.Scatter(
                        x=gd["months"], y=gd["quality_scores"],
                        mode="lines+markers",
                        line=dict(color="#3498db", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(52,152,219,0.12)",
                        name="Quality"
                    ))
                    fig_q.update_layout(height=280, margin=dict(l=20,r=20,t=30,b=40),
                                        yaxis=dict(range=[0,5]))
                    st.plotly_chart(fig_q, width="stretch")

                st.markdown("#### Unit Price Trend")
                fig_price = go.Figure()
                fig_price.add_trace(go.Bar(
                    x=gd["months"], y=gd["avg_prices"],
                    marker_color="#e67e22",
                    name="₹ Price"
                ))
                fig_price.update_layout(height=260, margin=dict(l=20,r=20,t=30,b=40))
                st.plotly_chart(fig_price, width="stretch")

            # ── Reviews ───────────────────────────────────────────────────────
            reviews = report.get("recent_reviews", [])
            if reviews:
                st.markdown("### 💬 Recent Customer Reviews")
                for rev in reviews:
                    stars = "⭐" * int(rev.get("rating", 4))
                    st.markdown(f"**{rev['date']}** &nbsp; {stars}")
                    st.write(f"> {rev['comment']}")
                    st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Ask AI Agent
# ══════════════════════════════════════════════════════════════════════════════

elif page == "💬 Ask AI Agent":
    st.title("💬 Ask the AI Procurement Agent")
    st.caption("Powered by LangChain + OpenAI GPT with LSTM-enriched supplier data")

    st.info(
        "**Example questions:**\n"
        "- Who should I buy 500 Circuit Boards from within 6 days?\n"
        "- Which supplier has the best reliability and quality rating?\n"
        "- What is the LSTM reliability prediction for supplier 1?\n"
        "- Compare Alpha Supplies and Lambda Steel Industries.\n"
        "- Show me suppliers for Motor Units under ₹150 per unit."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask anything about suppliers, procurement, or predictions...")

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question and fetching supplier data..."):
                result = post("/supplier/ask", {"question": question})

            if result:
                answer = result.get("answer", "No answer returned.")
                tools  = result.get("tools_used", [])
                st.markdown(answer)
                if tools:
                    st.caption(f"🔧 Tools used: `{'`, `'.join(tools)}`")
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            else:
                err = "❌ Could not get a response from the agent."
                st.error(err)
                st.session_state.chat_history.append({"role": "assistant", "content": err})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
