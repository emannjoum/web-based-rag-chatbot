import streamlit as st


class ClinicalTerminalTheme:
    """Injects the dark-mode clinical terminal design system into Streamlit."""

    COLORS = {
        "graphite_base": "#0B0F19",
        "slate_canvas": "#111827",
        "slate_elevated": "#1A2332",
        "glass_bg": "rgba(17, 24, 39, 0.55)",
        "glass_border": "rgba(45, 212, 191, 0.18)",
        "text_primary": "#F1F5F9",
        "text_muted": "#64748B",
        "text_dim": "#475569",
        "accent_teal": "#2DD4BF",
        "accent_cyan": "#22D3EE",
        "accent_green": "#34D399",
        "accent_glow": "rgba(45, 212, 191, 0.35)",
        "border_subtle": "rgba(148, 163, 184, 0.12)",
        "border_active": "rgba(45, 212, 191, 0.45)",
        "user_bubble": "#1E3A5F",
        "bot_bubble": "rgba(17, 24, 39, 0.85)",
    }

    @classmethod
    def inject(cls) -> None:
        st.markdown(cls._build_global_css(), unsafe_allow_html=True)

    @classmethod
    def _build_global_css(cls) -> str:
        c = cls.COLORS
        return f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Tajawal:wght@300;400;500;700&display=swap');

        :root {{
            --graphite-base: {c['graphite_base']};
            --slate-canvas: {c['slate_canvas']};
            --slate-elevated: {c['slate_elevated']};
            --text-primary: {c['text_primary']};
            --text-muted: {c['text_muted']};
            --accent-teal: {c['accent_teal']};
            --accent-cyan: {c['accent_cyan']};
            --accent-green: {c['accent_green']};
            --border-subtle: {c['border_subtle']};
            --border-active: {c['border_active']};
        }}

        #MainMenu, footer, header {{ visibility: hidden; }}
        .stApp {{
            background: {c['graphite_base']};
            font-family: 'IBM Plex Sans Arabic', 'Tajawal', system-ui, sans-serif;
        }}

        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(160deg, {c['graphite_base']} 0%, {c['slate_canvas']} 55%, #0D1520 100%);
        }}

        [data-testid="stSidebar"] {{
            background: {c['graphite_base']} !important;
            border-right: 1px solid {c['border_subtle']};
            min-width: 280px !important;
            max-width: 300px !important;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: {c['graphite_base']};
            padding-top: 1.25rem;
        }}

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p {{
            color: {c['text_primary']} !important;
        }}

        .sidebar-brand {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            font-weight: 500;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: {c['accent_teal']};
            margin-bottom: 0.15rem;
        }}

        .sidebar-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {c['text_primary']};
            margin-bottom: 1.5rem;
            line-height: 1.3;
        }}

        .timeline-header {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.62rem;
            font-weight: 500;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: {c['text_dim']};
            margin: 1.1rem 0 0.45rem 0;
            padding-left: 0.15rem;
        }}

        .history-item-label {{
            font-size: 0.82rem;
            color: {c['text_muted']};
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .sidebar-footer {{
            position: fixed;
            bottom: 1.25rem;
            left: 1rem;
            width: calc(280px - 2rem);
            padding: 0.85rem 1rem;
            background: {c['slate_elevated']};
            border: 1px solid {c['border_subtle']};
            border-radius: 10px;
        }}

        .sidebar-footer .status-dot {{
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: {c['accent_green']};
            margin-right: 0.5rem;
            animation: pulse-dot 2.4s ease-in-out infinite;
        }}

        @keyframes pulse-dot {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 {c['accent_glow']}; }}
            50% {{ opacity: 0.7; box-shadow: 0 0 0 4px transparent; }}
        }}

        .sidebar-footer .status-text {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.68rem;
            color: {c['text_muted']};
            letter-spacing: 0.06em;
        }}

        [data-testid="stSidebar"] .stButton > button {{
            background: {c['slate_elevated']} !important;
            color: {c['text_primary']} !important;
            border: 1px solid {c['border_subtle']} !important;
            border-radius: 8px !important;
            font-size: 0.84rem !important;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            border-color: {c['border_active']} !important;
            box-shadow: 0 0 12px {c['accent_glow']};
        }}

        .new-chat-btn .stButton > button {{
            background: linear-gradient(135deg, rgba(45,212,191,0.15), rgba(34,211,238,0.08)) !important;
            border-color: {c['border_active']} !important;
            font-weight: 500 !important;
        }}

        .center-column {{
            min-height: calc(100vh - 6rem);
            position: relative;
        }}

        .top-nav-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0 1.2rem 0;
            border-bottom: 1px solid {c['border_subtle']};
            margin-bottom: 1rem;
        }}

        .top-nav-title {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {c['text_muted']};
        }}

        .model-pill-active {{
            display: inline-block;
            padding: 0.3rem 0.85rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-family: 'IBM Plex Mono', monospace;
            background: rgba(45, 212, 191, 0.12);
            border: 1px solid {c['border_active']};
            color: {c['accent_teal']};
        }}

        .empty-state-watermark {{
            position: absolute;
            top: 18%;
            left: 50%;
            transform: translateX(-50%);
            font-family: 'IBM Plex Mono', monospace;
            font-size: clamp(3rem, 8vw, 6rem);
            font-weight: 500;
            color: rgba(148, 163, 184, 0.06);
            letter-spacing: 0.2em;
            text-transform: uppercase;
            pointer-events: none;
            user-select: none;
            white-space: nowrap;
        }}

        .empty-state-subtitle {{
            text-align: center;
            color: {c['text_muted']};
            font-size: 0.9rem;
            margin-bottom: 2rem;
            position: relative;
            z-index: 1;
        }}

        [data-testid="stVerticalBlock"] .inquiry-grid .stButton > button {{
            background: {c['slate_elevated']} !important;
            border: 1px solid {c['border_subtle']} !important;
            border-radius: 10px !important;
            color: {c['text_primary']} !important;
            font-size: 0.82rem !important;
            line-height: 1.45 !important;
            min-height: 72px !important;
            text-align: left !important;
            padding: 1rem 1.1rem !important;
            transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
        }}

        [data-testid="stVerticalBlock"] .inquiry-grid .stButton > button:hover {{
            border-color: {c['border_active']} !important;
            box-shadow: 0 0 16px {c['accent_glow']};
            transform: translateY(-1px);
        }}

        [data-testid="stChatMessage"] {{
            background: transparent !important;
            border: none !important;
            padding: 0.35rem 0 !important;
        }}

        [data-testid="stChatMessage"][data-testid*="user"],
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
            flex-direction: row-reverse;
        }}

        .user-message-block {{
            background: {c['user_bubble']};
            border: 1px solid {c['border_subtle']};
            border-radius: 12px 12px 4px 12px;
            padding: 0.85rem 1.1rem;
            margin-left: auto;
            max-width: 78%;
            color: {c['text_primary']};
            font-size: 0.92rem;
            line-height: 1.55;
        }}

        .bot-message-block {{
            background: {c['bot_bubble']};
            border: 1px solid {c['border_active']};
            border-radius: 12px 12px 12px 4px;
            padding: 0.95rem 1.15rem;
            max-width: 88%;
            color: {c['text_primary']};
            font-size: 0.92rem;
            line-height: 1.6;
        }}

        .bot-message-block a {{
            color: {c['accent_cyan']} !important;
            text-decoration: none;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            padding: 0.1rem 0.35rem;
            background: rgba(34, 211, 238, 0.1);
            border-radius: 4px;
            border: 1px solid rgba(34, 211, 238, 0.25);
        }}

        .quick-actions-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.75rem 0 0.25rem 0;
        }}

        .action-pill .stButton > button {{
            background: transparent !important;
            color: {c['accent_teal']} !important;
            border: 1px solid {c['border_active']} !important;
            border-radius: 20px !important;
            font-size: 0.74rem !important;
            padding: 0.25rem 0.85rem !important;
            font-family: 'IBM Plex Mono', monospace !important;
            letter-spacing: 0.02em;
            transition: background 0.2s, box-shadow 0.2s;
        }}

        .action-pill .stButton > button:hover {{
            background: rgba(45, 212, 191, 0.1) !important;
            box-shadow: 0 0 10px {c['accent_glow']};
        }}

        .citation-pane {{
            background: {c['glass_bg']};
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid {c['glass_border']};
            border-radius: 14px;
            padding: 1.25rem 1rem;
            min-height: calc(100vh - 3rem);
            position: sticky;
            top: 1rem;
        }}

        .citation-pane-header {{
            font-size: 0.78rem;
            font-weight: 600;
            color: {c['text_primary']};
            letter-spacing: 0.04em;
            margin-bottom: 1.1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid {c['border_subtle']};
            line-height: 1.4;
        }}

        .citation-card {{
            background: rgba(26, 35, 50, 0.7);
            border: 1px solid {c['border_subtle']};
            border-radius: 10px;
            padding: 0.85rem 0.9rem;
            margin-bottom: 0.65rem;
            transition: border-color 0.2s;
        }}

        .citation-card:hover {{
            border-color: {c['border_active']};
        }}

        .citation-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.5rem;
            height: 1.5rem;
            border-radius: 6px;
            background: rgba(45, 212, 191, 0.15);
            border: 1px solid {c['border_active']};
            color: {c['accent_teal']};
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            margin-right: 0.55rem;
        }}

        .citation-label {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.62rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: {c['accent_green']};
            margin-bottom: 0.35rem;
        }}

        .citation-url {{
            font-size: 0.78rem;
            color: {c['text_muted']};
            word-break: break-all;
            line-height: 1.4;
            margin-bottom: 0.55rem;
        }}

        .citation-url a {{
            color: {c['accent_cyan']} !important;
            text-decoration: none;
        }}

        .relevance-bar-track {{
            height: 3px;
            background: {c['border_subtle']};
            border-radius: 2px;
            overflow: hidden;
        }}

        .relevance-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, {c['accent_teal']}, {c['accent_cyan']});
            border-radius: 2px;
            transition: width 0.6s ease;
        }}

        .relevance-label {{
            display: flex;
            justify-content: space-between;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.6rem;
            color: {c['text_dim']};
            margin-top: 0.3rem;
        }}

        .citation-empty {{
            text-align: center;
            padding: 2.5rem 1rem;
            color: {c['text_dim']};
            font-size: 0.8rem;
            line-height: 1.5;
        }}

        .arabic-text {{
            font-family: 'Tajawal', 'IBM Plex Sans Arabic', sans-serif;
            line-height: 1.75;
        }}

        [dir="rtl"] .user-message-block,
        [dir="rtl"] .bot-message-block {{
            text-align: right;
        }}

        [data-testid="stChatInput"] {{
            background: {c['slate_elevated']} !important;
            border: 1px solid {c['border_subtle']} !important;
            border-radius: 12px !important;
        }}

        [data-testid="stChatInput"] textarea {{
            color: {c['text_primary']} !important;
            font-family: 'IBM Plex Sans Arabic', 'Tajawal', sans-serif !important;
        }}

        [data-testid="stChatInput"] {{
            border-color: {c['border_active']} !important;
            box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.25);
        }}

        .stSpinner > div {{
            border-top-color: {c['accent_teal']} !important;
        }}

        .stAlert {{
            background: {c['slate_elevated']} !important;
            border: 1px solid {c['border_subtle']} !important;
            color: {c['text_primary']} !important;
        }}

        div[data-testid="stVerticalBlock"] > div:has(.citation-pane) {{
            position: sticky;
            top: 0;
        }}

        .send-icon svg {{
            vertical-align: middle;
        }}

        .scan-line {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, {c['accent_teal']}, transparent);
            opacity: 0.25;
            animation: scan 6s linear infinite;
            pointer-events: none;
            z-index: 9999;
        }}

        @keyframes scan {{
            0% {{ transform: translateY(-100vh); }}
            100% {{ transform: translateY(100vh); }}
        }}
        </style>
        <div class="scan-line"></div>
        """
