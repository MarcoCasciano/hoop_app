# streamlit_app.py
import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

API_BASE = "http://localhost:8000"

TEAL  = "#3ABFB8"
AMBER = "#C4883A"
DARK  = "#0D0D0D"
CARD  = "#1A1A1A"
CARD2 = "#222222"
TEXT  = "#F0EDE8"
MUTED = "#7A7A7A"
RED   = "#E05252"

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Hoop · Coffee Tracker",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────
st.markdown(f"""
<style>
    #MainMenu, footer, header {{ visibility: hidden; }}

    .stApp {{ background-color: {DARK}; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #080808;
        border-right: 1px solid #222;
    }}

    /* Radio nav */
    [data-testid="stSidebar"] .stRadio label {{
        color: {MUTED};
        font-size: 15px;
        padding: 8px 12px;
        border-radius: 8px;
        display: block;
        transition: all 0.2s;
    }}
    [data-testid="stSidebar"] .stRadio label:hover {{
        color: {TEXT};
        background: #1a1a1a;
    }}

    /* Metrics */
    [data-testid="metric-container"] {{
        background: {CARD};
        border: 1px solid #252525;
        border-radius: 14px;
        padding: 20px !important;
    }}
    [data-testid="stMetricValue"] {{ color: {TEXT} !important; font-size: 26px !important; }}
    [data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-size: 13px !important; letter-spacing: 0.5px; }}

    /* Buttons */
    .stButton > button {{
        background: {TEAL};
        color: #000;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 15px;
        padding: 10px 0;
        width: 100%;
        transition: background 0.2s;
    }}
    .stButton > button:hover {{ background: #4ECEC7; color: #000; }}

    /* Delete button */
    .del-btn > button {{
        background: transparent !important;
        color: {MUTED} !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 4px 10px !important;
        width: auto !important;
    }}
    .del-btn > button:hover {{ color: {RED} !important; border-color: {RED} !important; }}

    /* Inputs */
    input, textarea, [data-baseweb="select"] > div {{
        background-color: {CARD2} !important;
        border-color: #2a2a2a !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
    }}

    /* Slider */
    [data-testid="stSlider"] > div > div > div > div {{
        background: {TEAL} !important;
    }}

    /* Divider */
    hr {{ border-color: #1e1e1e !important; }}

    /* Cards */
    .brew-card {{
        background: {CARD};
        border: 1px solid #252525;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }}
    .brew-card:hover {{ border-color: #333; }}

    /* Tip box */
    .tip-box {{
        background: {CARD};
        border-left: 3px solid {TEAL};
        border-radius: 0 10px 10px 0;
        padding: 12px 18px;
        margin: 6px 0;
    }}

    /* Preview card */
    .preview-card {{
        background: {CARD};
        border: 1px solid #252525;
        border-radius: 16px;
        padding: 36px 28px;
        text-align: center;
    }}

    /* Section subtitle */
    .subtitle {{
        color: {MUTED};
        font-size: 14px;
        margin-top: -12px;
        margin-bottom: 28px;
    }}
</style>
""", unsafe_allow_html=True)


# ── API helpers ─────────────────────────────────────────────────
def api_get(path: str, params: dict = None):
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("API non raggiungibile — assicurati che il server sia in esecuzione (`uvicorn app.main:app`).")
        return None
    except Exception as e:
        st.error(f"Errore: {e}")
        return None


def api_post(path: str, data: dict):
    try:
        r = httpx.post(f"{API_BASE}{path}", json=data, timeout=5)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("API non raggiungibile.")
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"Errore {e.response.status_code}: {e.response.json().get('detail', 'Errore sconosciuto')}")
        return None


def api_delete(path: str) -> bool:
    try:
        r = httpx.delete(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return True
    except Exception:
        return False


# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:32px 0 36px 0;">
        <div style="font-size:48px; line-height:1;">☕</div>
        <h2 style="color:{TEXT}; margin:10px 0 2px 0; font-size:24px; letter-spacing:3px; font-weight:800;">HOOP</h2>
        <p style="color:{MUTED}; font-size:11px; margin:0; letter-spacing:2px;">COFFEE TRACKER</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["📊  Dashboard", "➕  Nuova Estrazione", "📋  Storico"],
        label_visibility="collapsed",
    )

    st.markdown(f"""
    <div style="margin-top:40px; padding:16px; background:#111; border-radius:12px; text-align:center;">
        <p style="color:{MUTED}; font-size:11px; margin:0; letter-spacing:1px;">ceado hoop coffeebrewer</p>
    </div>
    """, unsafe_allow_html=True)


# ── DASHBOARD ───────────────────────────────────────────────────
if page == "📊  Dashboard":

    st.markdown(f"# Dashboard")
    st.markdown(f"<p class='subtitle'>Panoramica delle tue estrazioni</p>", unsafe_allow_html=True)

    brews = api_get("/brews", {"limit": 200})
    if brews is None:
        st.stop()

    if not brews:
        st.markdown(f"""
        <div style='text-align:center; padding:100px 0; color:{MUTED};'>
            <div style='font-size:72px; margin-bottom:16px;'>☕</div>
            <h3 style='color:{MUTED}; font-weight:400;'>Nessuna estrazione ancora</h3>
            <p style='font-size:14px;'>Vai su "Nuova Estrazione" per iniziare.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    df = pd.DataFrame(brews)
    df["created_at"] = pd.to_datetime(df["created_at"])
    rated = df[df["rating"].notna()].copy()

    # ── Metrics ─────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Estrazioni totali", len(df))
    with c2:
        if not rated.empty:
            st.metric("Rating medio", f"{rated['rating'].mean():.1f} / 10")
        else:
            st.metric("Rating medio", "—")
    with c3:
        if not rated.empty:
            best = rated.groupby("coffee")["rating"].mean().idxmax()
            st.metric("Caffè top ⭐", best)
        else:
            st.metric("Caffè top ⭐", "—")
    with c4:
        st.metric("Macinatura più usata", df["grind"].mode()[0])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row 1 ────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    CHART_BG = dict(
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font_color=TEXT, title_font_color=TEXT,
        margin=dict(l=10, r=10, t=44, b=10),
    )

    with col_left:
        if not rated.empty:
            fig = px.line(
                rated.sort_values("created_at"),
                x="created_at", y="rating",
                title="Andamento rating nel tempo",
                markers=True,
                color_discrete_sequence=[TEAL],
            )
            fig.update_layout(
                **CHART_BG,
                xaxis=dict(gridcolor="#222", title="", showgrid=False),
                yaxis=dict(gridcolor="#222", title="Rating", range=[0, 10.5]),
            )
            fig.update_traces(line_width=2.5, marker_size=8,
                              marker_color=TEAL, line_color=TEAL,
                              fill="tozeroy", fillcolor="rgba(58,191,184,0.08)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aggiungi un rating per visualizzare il grafico di andamento.")

    with col_right:
        grind_counts = df["grind"].value_counts().reset_index()
        grind_counts.columns = ["grind", "count"]
        fig2 = px.pie(
            grind_counts, names="grind", values="count",
            title="Distribuzione macinatura",
            hole=0.62,
            color_discrete_sequence=[TEAL, AMBER, "#E87040"],
        )
        fig2.update_layout(
            **CHART_BG,
            legend=dict(font=dict(color=TEXT)),
        )
        fig2.update_traces(textfont_color=TEXT)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Charts row 2 ────────────────────────────────────────────
    if not rated.empty and len(rated) >= 3:
        col_a, col_b = st.columns(2)

        with col_a:
            fig3 = px.scatter(
                rated, x="dose", y="rating",
                color="grind", size="water",
                hover_data=["coffee", "temperature", "water"],
                title="Dose vs Rating",
                color_discrete_sequence=[TEAL, AMBER, "#E87040"],
            )
            fig3.update_layout(
                **CHART_BG,
                xaxis=dict(gridcolor="#222", title="Dose (g)"),
                yaxis=dict(gridcolor="#222", title="Rating", range=[0, 10.5]),
                legend=dict(font=dict(color=TEXT)),
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col_b:
            temp_counts = df["temperature"].value_counts().reset_index()
            temp_counts.columns = ["temperatura", "count"]
            fig4 = px.bar(
                temp_counts.sort_values("temperatura"),
                x="temperatura", y="count",
                title="Distribuzione temperatura",
                color_discrete_sequence=[AMBER],
            )
            fig4.update_layout(
                **CHART_BG,
                xaxis=dict(gridcolor="#222", title="°C"),
                yaxis=dict(gridcolor="#222", title="N° brew"),
                bargap=0.3,
            )
            st.plotly_chart(fig4, use_container_width=True)


# ── NUOVA ESTRAZIONE ────────────────────────────────────────────
elif page == "➕  Nuova Estrazione":

    st.markdown("# Nuova Estrazione")
    st.markdown(f"<p class='subtitle'>Registra i parametri della tua brew</p>", unsafe_allow_html=True)

    col_form, col_preview = st.columns([3, 2], gap="large")

    with col_form:
        coffee = st.text_input("☕  Caffè / Roaster", placeholder="es. Ethiopia Yirgacheffe")

        c1, c2 = st.columns(2)
        with c1:
            dose = st.number_input("Dose (g)", min_value=1.0, max_value=50.0, value=18.0, step=0.1, format="%.1f")
        with c2:
            ratio = st.number_input("Ratio", min_value=10.0, max_value=25.0, value=16.0, step=0.5, format="%.1f")

        c3, c4 = st.columns(2)
        with c3:
            temperature = st.slider("Temperatura (°C)", min_value=70, max_value=100, value=94)
        with c4:
            grind = st.selectbox("Macinatura", ["medium", "fine", "coarse"])

        rating = st.select_slider(
            "Rating  (0 = non valutato)",
            options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            value=0,
        )
        notes = st.text_area("Note (opzionale)", placeholder="es. floreale, acidità intensa, retrogusto lungo...", max_chars=500)

        st.markdown("<br>", unsafe_allow_html=True)
        save = st.button("Salva estrazione")

    # Preview live (si aggiorna ad ogni cambio widget)
    water = round(dose * ratio, 1)
    rating_label = f"{rating} / 10" if rating > 0 else "—"
    rating_color = TEAL if rating >= 8 else (AMBER if rating >= 6 else (RED if 0 < rating <= 5 else MUTED))

    with col_preview:
        st.markdown(f"""
        <div class="preview-card">
            <p style="color:{MUTED}; font-size:11px; letter-spacing:2px; margin:0 0 4px 0;">ACQUA NECESSARIA</p>
            <h1 style="color:{TEAL}; font-size:72px; font-weight:800; margin:0; line-height:1;">
                {water}<span style="font-size:28px; font-weight:400;"> g</span>
            </h1>
            <p style="color:{MUTED}; font-size:13px; margin:6px 0 28px 0;">{dose}g × {ratio}</p>
            <hr style="border-color:#2a2a2a; margin:0 0 24px 0;">
            <div style="display:flex; justify-content:space-around; text-align:center;">
                <div>
                    <p style="color:{MUTED}; font-size:11px; letter-spacing:1px; margin:0;">TEMP</p>
                    <p style="color:{TEXT}; font-size:22px; font-weight:600; margin:4px 0 0 0;">{temperature}°</p>
                </div>
                <div>
                    <p style="color:{MUTED}; font-size:11px; letter-spacing:1px; margin:0;">GRIND</p>
                    <p style="color:{TEXT}; font-size:22px; font-weight:600; margin:4px 0 0 0;">{grind}</p>
                </div>
                <div>
                    <p style="color:{MUTED}; font-size:11px; letter-spacing:1px; margin:0;">RATING</p>
                    <p style="color:{rating_color}; font-size:22px; font-weight:700; margin:4px 0 0 0;">{rating_label}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if save:
        if not coffee.strip():
            st.error("Il nome del caffè è obbligatorio.")
        else:
            payload = {
                "coffee": coffee.strip(),
                "dose": dose,
                "ratio": ratio,
                "temperature": temperature,
                "grind": grind,
                "rating": rating if rating > 0 else None,
                "notes": notes.strip() if notes.strip() else None,
            }
            result = api_post("/brews", payload)
            if result:
                st.success(f"Estrazione salvata con ID #{result['id']}")

                if rating > 0:
                    tips_data = api_get(f"/brews/{result['id']}/tips")
                    if tips_data:
                        st.markdown(f"<h4 style='color:{TEXT}; margin-top:24px;'>Suggerimenti</h4>", unsafe_allow_html=True)
                        for tip in tips_data["tips"]:
                            st.markdown(f"""
                            <div class="tip-box">
                                <p style="color:{TEXT}; margin:0;">💡 {tip}</p>
                            </div>
                            """, unsafe_allow_html=True)


# ── STORICO ─────────────────────────────────────────────────────
elif page == "📋  Storico":

    st.markdown("# Storico Estrazioni")
    st.markdown(f"<p class='subtitle'>Tutte le tue brew registrate</p>", unsafe_allow_html=True)

    brews = api_get("/brews", {"limit": 200})
    if brews is None:
        st.stop()

    if not brews:
        st.markdown(f"""
        <div style='text-align:center; padding:100px 0; color:{MUTED};'>
            <div style='font-size:72px; margin-bottom:16px;'>📋</div>
            <h3 style='color:{MUTED}; font-weight:400;'>Nessuna estrazione registrata</h3>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    df = pd.DataFrame(brews)

    # Filtri
    c1, c2, c3 = st.columns(3)
    with c1:
        search = st.text_input("🔍  Cerca caffè", placeholder="es. Ethiopia...")
    with c2:
        grind_filter = st.selectbox("Macinatura", ["Tutte", "fine", "medium", "coarse"])
    with c3:
        sort_by = st.selectbox("Ordina per", ["Più recenti", "Più vecchie", "Rating alto", "Rating basso"])

    # Applica filtri
    filtered = df.copy()
    if search:
        filtered = filtered[filtered["coffee"].str.contains(search, case=False, na=False)]
    if grind_filter != "Tutte":
        filtered = filtered[filtered["grind"] == grind_filter]
    if sort_by == "Più vecchie":
        filtered = filtered.iloc[::-1].reset_index(drop=True)
    elif sort_by == "Rating alto":
        filtered = filtered.sort_values("rating", ascending=False, na_position="last").reset_index(drop=True)
    elif sort_by == "Rating basso":
        filtered = filtered.sort_values("rating", ascending=True, na_position="last").reset_index(drop=True)

    st.markdown(f"<p style='color:{MUTED}; font-size:13px; margin-bottom:16px;'>{len(filtered)} estrazioni</p>", unsafe_allow_html=True)

    for _, row in filtered.iterrows():
        rating_val  = row["rating"]
        has_rating  = pd.notna(rating_val)
        r_color     = TEAL if has_rating and rating_val >= 8 else (AMBER if has_rating and rating_val >= 6 else (RED if has_rating else MUTED))
        r_display   = f"{int(rating_val)}/10" if has_rating else "—"
        created_str = pd.to_datetime(row["created_at"]).strftime("%d %b %Y  %H:%M")

        c_main, c_dose, c_water, c_temp, c_rating, c_del = st.columns([3, 1, 1, 1, 1, 1])

        with c_main:
            st.markdown(f"""
            <div style="padding:10px 0;">
                <p style="color:{TEXT}; font-size:16px; font-weight:600; margin:0;">{row['coffee']}</p>
                <p style="color:{MUTED}; font-size:12px; margin:2px 0 0 0;">{created_str} &nbsp;·&nbsp; {row['grind']}</p>
            </div>
            """, unsafe_allow_html=True)
        with c_dose:
            st.markdown(f"<p style='color:{MUTED};font-size:11px;letter-spacing:1px;margin:12px 0 2px 0;'>DOSE</p><p style='color:{TEXT};margin:0;font-size:15px;'>{row['dose']}g</p>", unsafe_allow_html=True)
        with c_water:
            st.markdown(f"<p style='color:{MUTED};font-size:11px;letter-spacing:1px;margin:12px 0 2px 0;'>ACQUA</p><p style='color:{TEXT};margin:0;font-size:15px;'>{row['water']}g</p>", unsafe_allow_html=True)
        with c_temp:
            st.markdown(f"<p style='color:{MUTED};font-size:11px;letter-spacing:1px;margin:12px 0 2px 0;'>TEMP</p><p style='color:{TEXT};margin:0;font-size:15px;'>{row['temperature']}°C</p>", unsafe_allow_html=True)
        with c_rating:
            st.markdown(f"<p style='color:{MUTED};font-size:11px;letter-spacing:1px;margin:12px 0 2px 0;'>RATING</p><p style='color:{r_color};margin:0;font-size:18px;font-weight:700;'>{r_display}</p>", unsafe_allow_html=True)
        with c_del:
            st.markdown("<div class='del-btn'>", unsafe_allow_html=True)
            if st.button("🗑", key=f"del_{row['id']}", help="Elimina questa brew"):
                if api_delete(f"/brews/{row['id']}"):
                    st.toast("Estrazione eliminata", icon="🗑")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if pd.notna(row.get("notes")) and row["notes"]:
            st.markdown(f"<p style='color:{MUTED}; font-size:13px; padding-left:4px; margin:-4px 0 8px 0;'>📝 {row['notes']}</p>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
