import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import database as db
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BibSSJ",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# INIT BANCO — executa uma vez por sessão
# ─────────────────────────────────────────────
db.init_db()
db.sincronizar_atrasos()
db.sincronizar_multas()  # ← ADICIONE ESTA LINHA

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
def inject_css():
    st.html("""
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
        :root {
            --bg:        #0D1B2A;
            --surface:   #162032;
            --surface2:  #1E2F45;
            --border:    #253650;
            --teal:      #4ECDC4;
            --teal-dim:  #2BA8A0;
            --amber:     #F5A623;
            --red:       #FF6B6B;
            --green:     #2ED573;
            --text:      #E8EDF2;
            --muted:     #7A92AD;
            --radius:    12px;
        }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        .stApp { background: var(--bg) !important; color: var(--text) !important; }
        section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
        section[data-testid="stSidebar"] * { color: var(--text) !important; }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        /* ── Input labels ── */
        .stTextInput label, .stSelectbox label, .stNumberInput label,
        .stDateInput label, .stTextArea label, .stMultiSelect label,
        div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] {
            color: var(--text) !important; font-size: 13px !important; font-weight: 500 !important;
        }
        /* ── Inputs ── */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
        .stNumberInput input, .stDateInput input, .stTextArea textarea {
            background: var(--surface2) !important; border: 1px solid var(--border) !important;
            border-radius: 8px !important; color: var(--text) !important;
        }
        .stTextInput input:focus { border-color: var(--teal) !important; box-shadow: 0 0 0 2px rgba(78,205,196,.2) !important; }
        div[data-baseweb="popover"] ul { background: var(--surface2) !important; }
        div[data-baseweb="popover"] li { color: var(--text) !important; }
        div[data-baseweb="popover"] li:hover { background: var(--border) !important; }
        input::placeholder, textarea::placeholder { color: var(--muted) !important; opacity: 1 !important; }

        /* ── Buttons ── */
        .stButton > button {
            background: var(--teal) !important; color: #0D1B2A !important;
            border: none !important; border-radius: 8px !important;
            font-weight: 600 !important; letter-spacing: .02em !important;
            padding: 8px 20px !important; transition: background .2s, transform .15s !important;
        }
        .stButton > button:hover { background: var(--teal-dim) !important; transform: translateY(-1px) !important; }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 10px; padding: 4px; gap: 2px; }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important; color: var(--muted) !important;
            border-radius: 8px !important; font-size: 13px !important; padding: 6px 16px !important;
        }
        .stTabs [aria-selected="true"] { background: var(--teal) !important; color: #0D1B2A !important; font-weight: 600 !important; }

        /* ── Alerts ── */
        .stAlert { border-radius: var(--radius) !important; }
        div[data-testid="stAlert"] { background: var(--surface2) !important; border-color: var(--teal) !important; }

        /* ── Metric ── */
        [data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; }
        [data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 12px !important; }
        [data-testid="stMetricValue"] { font-family: 'Playfair Display', serif !important; color: var(--text) !important; }

        /* ── Custom components ── */
        .section-header { font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
        .section-sub    { font-size: 13px; color: var(--muted); margin-bottom: 24px; }
        .card           { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 16px; }
        .card-title     { font-size: 14px; font-weight: 600; color: var(--teal); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 16px; }
        .kpi-card       { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; transition: transform .2s, box-shadow .2s; }
        .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.35); }
        .kpi-label      { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
        .kpi-value      { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; line-height: 1; }
        .kpi-delta      { font-size: 12px; margin-top: 6px; color: var(--muted); }
        .kpi-teal  { border-top: 3px solid var(--teal); }
        .kpi-amber { border-top: 3px solid var(--amber); }
        .kpi-red   { border-top: 3px solid var(--red); }
        .kpi-green { border-top: 3px solid var(--green); }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; letter-spacing: .04em; }
        .badge-green  { background: rgba(46,213,115,.15);  color: var(--green); }
        .badge-red    { background: rgba(255,107,107,.15); color: var(--red); }
        .badge-amber  { background: rgba(245,166,35,.15);  color: var(--amber); }
        .badge-teal   { background: rgba(78,205,196,.15);  color: var(--teal); }
        .divider      { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
        .brand        { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: var(--teal); letter-spacing: .02em; }
        .brand-sub    { font-size: 11px; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; }
        .status-row   { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
        .status-row:last-child { border-bottom: none; }
        .timeline-item { display: flex; gap: 14px; padding: 12px 0; border-bottom: 1px solid var(--border); }
        .timeline-dot  { width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
        .timeline-title { font-size: 13px; font-weight: 500; }
        .timeline-meta  { font-size: 11px; color: var(--muted); margin-top: 2px; }
        .loan-card         { background: var(--surface2); border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; border-left: 4px solid var(--teal); font-size: 13px; }
        .loan-card.overdue { border-left-color: var(--red); }
        .loan-card.warning { border-left-color: var(--amber); }
        </style>
    """)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "page"       not in st.session_state: st.session_state.page       = "Dashboard"
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "admin_nome" not in st.session_state: st.session_state.admin_nome = ""
if "admin_perfil" not in st.session_state: st.session_state.admin_perfil = ""

# ─────────────────────────────────────────────
# HELPER: TABELA HTML DARK
# ─────────────────────────────────────────────
def render_table(df: pd.DataFrame):
    STATUS_COLORS = {
        "Disponível":   ("#2ED573", "#0d2b1a"),
        "Indisponível": ("#FF6B6B", "#2b0d0d"),
        "Atrasado":     ("#FF6B6B", "#2b0d0d"),
        "Ativo":        ("#4ECDC4", "#0d2625"),
        "Em dia":       ("#4ECDC4", "#0d2625"),
        "Regular":      ("#2ED573", "#0d2b1a"),
        "Inadimplente": ("#F5A623", "#2b1f0d"),
        "Suspenso":     ("#FF6B6B", "#2b0d0d"),
        "Pendente":     ("#F5A623", "#2b1f0d"),
        "Pago":         ("#2ED573", "#0d2b1a"),
        "Devolvido":    ("#7A92AD", "#1a2533"),
    }

    def fmt_cell(val):
        s = str(val)
        if s in STATUS_COLORS:
            fg, bg = STATUS_COLORS[s]
            return f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;background:{bg};color:{fg};">{s}</span>'
        return s

    header_cells = "".join(f"<th>{col}</th>" for col in df.columns)
    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg = "#162032" if i % 2 == 0 else "#1a2a3d"
        cells = "".join(f"<td>{fmt_cell(v)}</td>" for v in row)
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

    st.html(f"""
    <style>
    .dark-table {{ width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;font-size:13px;color:#E8EDF2; }}
    .dark-table th {{ background:#1E2F45;color:#7A92AD;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;padding:10px 14px;text-align:left;border-bottom:1px solid #253650; }}
    .dark-table td {{ padding:10px 14px;border-bottom:1px solid #1E2F45;color:#E8EDF2; }}
    .dark-table tr:last-child td {{ border-bottom:none; }}
    .dark-table tr:hover td {{ background:#1E2F45 !important; }}
    </style>
    <div style="border-radius:10px;overflow:hidden;border:1px solid #253650;">
        <table class="dark-table">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """)

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────

def get_img_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def login_page():
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            brasao_b64 = get_img_base64("assets/brasao.jpg")
            img_tag = f'<img src="data:image/jpeg;base64,{brasao_b64}" style="width:96px;height:96px;object-fit:contain;margin-bottom:12px;">'
        except FileNotFoundError:
            img_tag = '<div style="font-size:48px;margin-bottom:8px;">📚</div>'
        st.markdown(f"""
            <div style="text-align:center;margin-bottom:32px;">
                {img_tag}
                <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:#4ECDC4;">BibSSJ</div>
                <div style="font-size:12px;color:#7A92AD;letter-spacing:.12em;text-transform:uppercase;margin-top:4px;">
                    Sistema de Gerenciamento da Biblioteca do Seminário São José
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card-title">Acesso ao Sistema</div>', unsafe_allow_html=True)
        usuario_input = st.text_input("E-mail", placeholder="admin@bibssj.edu.br")
        senha_input   = st.text_input("Senha", type="password", placeholder="••••••••")
        col_a, col_b  = st.columns(2)
        with col_a:
            if st.button("Entrar", use_container_width=True):
                if usuario_input and senha_input:
                    admin = db.autenticar(usuario_input, senha_input)
                    if admin:
                        st.session_state.logged_in   = True
                        st.session_state.admin_nome  = admin["nome"]
                        st.session_state.admin_perfil= admin["perfil"]
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
                else:
                    st.error("Preencha os campos.")
        with col_b:
            if st.button("Esqueci a senha", use_container_width=True):
                st.info("Contate o administrador do sistema.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <div style="text-align:center;font-size:11px;color:#7A92AD;margin-top:16px;">
                Versão 2.0 · BibSSJ © 2026 &nbsp;·&nbsp;
                <span style="color:#253650;">admin@bibssj.edu.br / admin123</span>
            </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def sidebar():
    stats = db.get_stats()
    with st.sidebar:
        st.image("assets/brasao.jpg", width=100)
        st.markdown(f"""
            <div style="padding:12px 4px 20px;">
                <div class="brand">BibSSJ</div>
                <div class="brand-sub">Biblioteca do Seminário São José</div>
                <div style="font-size:11px;color:#7A92AD;margin-top:8px;">
                    {st.session_state.admin_nome} · {st.session_state.admin_perfil}
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        pages = [
            ("🏠", "Dashboard"), ("📖", "Acervo"), ("👥", "Usuários"),
            ("📋", "Empréstimos"), ("💰", "Financeiro"), ("⚙️", "Administrativo"),
        ]
        for icon, label in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.page = label
                st.rerun()

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(f"""
            <div style="font-size:11px;color:#7A92AD;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Status rápido</div>
            <div class="status-row"><span>Em circulação</span><span style="color:#4ECDC4;font-weight:600;">{stats['emprestimos_ativos']}</span></div>
            <div class="status-row"><span>Atrasados</span><span style="color:#FF6B6B;font-weight:600;">{stats['atrasados']}</span></div>
            <div class="status-row"><span>Inadimplentes</span><span style="color:#F5A623;font-weight:600;">{stats['inadimplentes']}</span></div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        if st.button("🚪  Sair", use_container_width=True):
            st.session_state.logged_in   = False
            st.session_state.admin_nome  = ""
            st.session_state.admin_perfil= ""
            st.rerun()
        st.markdown('<div style="font-size:10px;color:#253650;text-align:center;margin-top:20px;">BibSSJ v2.0 · 2026</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    stats = db.get_stats()

    st.markdown('<div class="section-header">Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Visão geral do sistema · Hoje, {datetime.now().strftime("%d de %B de %Y")}</div>', unsafe_allow_html=True)

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    for col, cls, val, label, delta in [
        (k1, "kpi-teal",  stats["total_exemplares"],   "Exemplares no Acervo",   ""),
        (k2, "kpi-amber", stats["total_usuarios"],     "Usuários Cadastrados",   ""),
        (k3, "kpi-green", stats["emprestimos_ativos"], "Empréstimos Ativos",     ""),
        (k4, "kpi-red",   stats["atrasados"],          "Devoluções Atrasadas",   "⚠ requer atenção" if stats["atrasados"] > 0 else ""),
    ]:
        with col:
            st.markdown(f"""
                <div class="kpi-card {cls}">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{val}</div>
                    <div class="kpi-delta">{delta}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="card"><div class="card-title">Empréstimos Recentes</div>', unsafe_allow_html=True)
        df_emp = db.get_emprestimos(apenas_ativos=True).tail(6)
        if not df_emp.empty:
            df_show = df_emp[["Usuário", "Livro", "Devolução Prevista", "Status"]].copy()
            render_table(df_show)
        else:
            st.markdown('<div style="color:#7A92AD;font-size:13px;">Nenhum empréstimo ativo.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card"><div class="card-title">Multas Pendentes</div>', unsafe_allow_html=True)
        multas = db.get_multas()
        pendentes = multas[multas["Status Pagamento"] == "Pendente"] if not multas.empty else multas
        if not pendentes.empty:
            for _, row in pendentes.iterrows():
                st.markdown(f"""
                    <div class="timeline-item">
                        <div class="timeline-dot" style="background:#FF6B6B;"></div>
                        <div>
                            <div class="timeline-title">{row['Usuário']}</div>
                            <div class="timeline-meta">{row['Livro']} · {row['Dias de Atraso']} dias · <b style="color:#FF6B6B;">R$ {row['Multa (R$)']:.2f}</b></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#7A92AD;font-size:13px;">Nenhuma multa pendente.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown('<div class="card"><div class="card-title">Livros Mais Emprestados</div>', unsafe_allow_html=True)
        top = stats.get("top_livros", [])
        max_val = top[0]["total"] if top else 1
        colors  = ["#4ECDC4", "#2ED573", "#F5A623", "#FF6B6B"]
        for i, item in enumerate(top):
            pct = int(item["total"] / max_val * 100)
            st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                        <span>{item['titulo']}</span><span style="color:#7A92AD;">{item['total']}x</span>
                    </div>
                    <div style="background:#1E2F45;border-radius:999px;height:6px;">
                        <div style="width:{pct}%;background:{colors[i % 4]};border-radius:999px;height:6px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b2:
        st.markdown('<div class="card"><div class="card-title">Acervo por Categoria</div>', unsafe_allow_html=True)
        cats     = stats.get("categorias", [])
        total_ex = sum(c["total"] for c in cats) or 1
        colors   = ["#4ECDC4", "#2ED573", "#F5A623", "#FF6B6B", "#A78BFA"]
        for i, cat in enumerate(cats):
            pct = int(cat["total"] / total_ex * 100)
            st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                        <span>{cat['categoria']}</span>
                        <span style="color:#7A92AD;">{cat['total']} ex · {pct}%</span>
                    </div>
                    <div style="background:#1E2F45;border-radius:999px;height:6px;">
                        <div style="width:{pct}%;background:{colors[i % 5]};border-radius:999px;height:6px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: ACERVO
# ─────────────────────────────────────────────
def page_acervo():
    st.markdown('<div class="section-header">Acervo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Catálogo de livros da biblioteca</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋  Catálogo", "➕  Cadastrar Livro", "✏️  Alterar Livro"])

    with tab1:
        # ── Barra de totais ──
        acv = db.get_acervo_stats()
        st.html(f"""
            <div style="display:flex;gap:24px;margin-bottom:20px;flex-wrap:wrap;">
                <div style="background:#162032;border:1px solid #253650;border-radius:10px;padding:12px 20px;min-width:120px;">
                    <div style="font-size:11px;color:#7A92AD;text-transform:uppercase;letter-spacing:.06em;">Títulos</div>
                    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:#E8EDF2;">{acv['titulos']}</div>
                </div>
                <div style="background:#162032;border:1px solid #253650;border-radius:10px;padding:12px 20px;min-width:120px;">
                    <div style="font-size:11px;color:#7A92AD;text-transform:uppercase;letter-spacing:.06em;">Exemplares</div>
                    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:#E8EDF2;">{acv['exemplares']}</div>
                </div>
                <div style="background:#162032;border:1px solid #253650;border-radius:10px;padding:12px 20px;min-width:120px;">
                    <div style="font-size:11px;color:#7A92AD;text-transform:uppercase;letter-spacing:.06em;">Disponíveis</div>
                    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:#2ED573;">{acv['disponiveis']}</div>
                </div>
                <div style="background:#162032;border:1px solid #253650;border-radius:10px;padding:12px 20px;min-width:120px;">
                    <div style="font-size:11px;color:#7A92AD;text-transform:uppercase;letter-spacing:.06em;">Em uso</div>
                    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:#F5A623;">{acv['exemplares'] - acv['disponiveis']}</div>
                </div>
            </div>
        """)

        # ── Filtros: busca + categoria ──
        col_s, col_f = st.columns([3, 1])
        with col_s:
            busca = st.text_input(
                "", placeholder="🔍  Buscar por título, autor ou ISBN…",
                key="acervo_busca",
            )
        with col_f:
            cats_db    = ["Todas"] + db.get_categorias()
            filtro_cat = st.selectbox("Categoria", cats_db, key="acervo_cat")

        # Decide se há consulta ativa
        consulta_ativa = bool(busca.strip()) or filtro_cat != "Todas"

        if not consulta_ativa:
            st.html('<div style="margin:8px 0 4px;font-size:12px;color:#7A92AD;">Digite o título, autor ou ISBN, ou selecione uma categoria para pesquisar.</div>')
        else:
            # ── Resultados ──
            PAGE_SIZE = 20
            if "acervo_offset" not in st.session_state:
                st.session_state.acervo_offset = 0

            # Zera paginação quando filtro muda
            filtro_id = f"{busca}|{filtro_cat}"
            if st.session_state.get("acervo_filtro_id") != filtro_id:
                st.session_state.acervo_offset   = 0
                st.session_state.acervo_filtro_id = filtro_id

            offset = st.session_state.acervo_offset
            total  = db.count_livros(busca=busca, categoria=filtro_cat)
            df     = db.get_livros_paginado(busca=busca, categoria=filtro_cat,
                                            limit=PAGE_SIZE, offset=offset)

            if total == 0:
                st.info("Nenhum livro encontrado para esta busca.")
            else:
                ini = offset + 1
                fim = min(offset + PAGE_SIZE, total)
                st.html(f"""
                    <div style="font-size:12px;color:#7A92AD;margin-bottom:12px;">
                        Exibindo <b style="color:#E8EDF2;">{ini}–{fim}</b> de
                        <b style="color:#E8EDF2;">{total}</b> resultado(s)
                    </div>
                """)

                # ── Cards compactos ──
                CAT_COLORS = {
                    "Computação":      "#4ECDC4",
                    "Matemática":      "#A78BFA",
                    "Engenharia":      "#F5A623",
                    "Literatura":      "#FF6B6B",
                    "Ciências Sociais":"#2ED573",
                    "Direito":         "#60A5FA",
                    "Medicina":        "#F472B6",
                }
                rows_html = ""
                for _, row in df.iterrows():
                    cat_color  = CAT_COLORS.get(str(row["Categoria"]), "#7A92AD")
                    disp_color = "#2ED573" if str(row["Status"]) == "Disponível" else "#FF6B6B"
                    disp_bg    = "rgba(46,213,115,.12)" if str(row["Status"]) == "Disponível" else "rgba(255,107,107,.12)"
                    ano        = str(row["Ano"]) if str(row["Ano"]) not in ("None", "nan", "") else "—"
                    rows_html += f"""
                        <div style="display:flex;align-items:center;gap:16px;
                                    padding:12px 16px;border-bottom:1px solid #1E2F45;
                                    transition:background .15s;"
                             onmouseover="this.style.background='#1E2F45'"
                             onmouseout="this.style.background='transparent'">
                            <div style="width:4px;height:40px;border-radius:2px;
                                        background:{cat_color};flex-shrink:0;"></div>
                            <div style="flex:1;min-width:0;">
                                <div style="font-weight:600;font-size:13px;
                                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                    {row['Título']}
                                </div>
                                <div style="font-size:11px;color:#7A92AD;margin-top:2px;">
                                    {row['Autor']} · {ano}
                                    {'· ISBN: ' + str(row['ISBN']) if str(row['ISBN']) not in ('None','nan','') else ''}
                                </div>
                            </div>
                            <div style="display:flex;align-items:center;gap:10px;flex-shrink:0;">
                                <span style="font-size:11px;padding:2px 8px;border-radius:999px;
                                             background:rgba(255,255,255,.06);color:{cat_color};">
                                    {row['Categoria']}
                                </span>
                                <span style="font-size:11px;color:#7A92AD;min-width:60px;text-align:right;">
                                    {row['Disponíveis']}/{row['Exemplares']} ex.
                                </span>
                                <span style="font-size:11px;padding:2px 8px;border-radius:999px;
                                             background:{disp_bg};color:{disp_color};font-weight:600;">
                                    {row['Status']}
                                </span>
                            </div>
                        </div>
                    """

                st.html(f"""
                    <div style="background:#162032;border:1px solid #253650;
                                border-radius:12px;overflow:hidden;">
                        {rows_html}
                    </div>
                """)

                # ── Navegação de páginas ──
                col_prev, col_info, col_next, col_exp = st.columns([1, 2, 1, 2])
                with col_prev:
                    if st.button("← Anterior", disabled=offset == 0, key="acervo_prev", use_container_width=True):
                        st.session_state.acervo_offset = max(0, offset - PAGE_SIZE)
                        st.rerun()
                with col_info:
                    pagina_atual = offset // PAGE_SIZE + 1
                    total_pags   = (total + PAGE_SIZE - 1) // PAGE_SIZE
                    st.html(f'<div style="text-align:center;font-size:12px;color:#7A92AD;padding-top:10px;">Página {pagina_atual} de {total_pags}</div>')
                with col_next:
                    if st.button("Próxima →", disabled=fim >= total, key="acervo_next", use_container_width=True):
                        st.session_state.acervo_offset = offset + PAGE_SIZE
                        st.rerun()
                with col_exp:
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇ Exportar página", csv, "acervo_bibssj.csv", "text/csv", use_container_width=True, key="acervo_exp")

    with tab2:
        st.markdown('<div class="card"><div class="card-title">Novo Livro</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            titulo  = st.text_input("Título *",  key="liv_titulo")
            autor   = st.text_input("Autor *",   key="liv_autor")
            isbn    = st.text_input("ISBN",       key="liv_isbn")
            editora = st.text_input("Editora",    key="liv_editora")
            edicao  = st.text_input("Edição",     key="liv_edicao")
        with c2:
            ano            = st.number_input("Ano de Publicação", min_value=1800, max_value=2099, value=2023, key="liv_ano")
            cats_cad       = db.get_categorias() + ["+ Nova categoria..."]
            cat_sel        = st.selectbox("Categoria *", cats_cad, key="liv_cat")
            if cat_sel == "+ Nova categoria...":
                categoria  = st.text_input("Nome da nova categoria *", key="liv_cat_nova")
            else:
                categoria  = cat_sel
            idioma         = st.selectbox("Idioma", ["Português","Inglês","Espanhol","Francês","Alemão"], key="liv_idioma")
            qtd            = st.number_input("Quantidade de Exemplares", min_value=1, value=1, key="liv_qtd")
        localizacao = st.text_input("Localização na Estante (ex: A-12)", key="liv_loc")
        if st.button("Salvar Livro", key="btn_salvar_livro"):
            if titulo and autor:
                ok = db.insert_livro(titulo, autor, isbn, editora, ano, categoria, idioma, edicao, localizacao, qtd)
                if ok:
                    st.success(f"✅ Livro **{titulo}** cadastrado com sucesso!")
                    st.cache_data.clear()
                else:
                    st.error("Erro ao salvar. Verifique os dados.")
            else:
                st.error("Preencha os campos obrigatórios (*).")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card"><div class="card-title">Alterar Livro</div>', unsafe_allow_html=True)

        busca_alt = st.text_input(
            "Buscar livro para alterar",
            placeholder="\U0001F50D  Digite o título, autor ou ISBN...",
            key="alt_busca",
        )

        if not busca_alt.strip():
            st.html('<div style="font-size:13px;color:#7A92AD;margin-top:6px;">Digite para localizar o livro que deseja editar.</div>')
        else:
            df_alt = db.get_livros_paginado(busca=busca_alt, limit=8, offset=0)

            if df_alt.empty:
                st.warning("Nenhum livro encontrado para esta busca.")
            else:
                opcoes = {
                    f"{row['Título']}  —  {row['Autor']}": int(row["ID"])
                    for _, row in df_alt.iterrows()
                }
                livro_escolhido = st.selectbox(
                    f"{len(opcoes)} resultado(s) — selecione o livro:",
                    list(opcoes.keys()),
                    key="alt_livro_sel",
                )
                livro_id = opcoes[livro_escolhido]
                dados    = db.get_livro_por_id(livro_id)

                if dados:
                    st.html('<hr style="border:none;border-top:1px solid #253650;margin:16px 0;">')

                    IDIOMAS    = ["Português","Inglês","Espanhol","Francês","Alemão"]
                    CATEGORIAS = db.get_categorias()
                    # Garante que a categoria atual do livro esteja na lista
                    # mesmo que não esteja cadastrada em outros livros ainda
                    if dados["categoria"] and dados["categoria"] not in CATEGORIAS:
                        CATEGORIAS = [dados["categoria"]] + CATEGORIAS

                    cat_idx    = CATEGORIAS.index(dados["categoria"]) if dados["categoria"] in CATEGORIAS else 0
                    idioma_idx = IDIOMAS.index(dados["idioma"])       if dados["idioma"]    in IDIOMAS    else 0
                    em_uso     = dados["qtd_exemplares"] - dados["qtd_disponivel"]

                    with st.form(key=f"form_editar_livro_{livro_id}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            e_titulo  = st.text_input("Título *",  value=dados["titulo"]  or "")
                            e_autor   = st.text_input("Autor *",   value=dados["autor"]   or "")
                            e_isbn    = st.text_input("ISBN",      value=dados["isbn"]    or "")
                            e_editora = st.text_input("Editora",   value=dados["editora"] or "")
                            e_edicao  = st.text_input("Edição",    value=dados["edicao"]  or "")
                        with c2:
                            e_ano      = st.number_input("Ano de Publicação", min_value=1800, max_value=2099,
                                                         value=int(dados["ano_publicacao"] or 2000))
                            e_categoria= st.selectbox("Categoria *", CATEGORIAS, index=cat_idx)
                            e_idioma   = st.selectbox("Idioma",      IDIOMAS,    index=idioma_idx)
                            e_qtd      = st.number_input("Qtd. Exemplares", min_value=1,
                                                         value=int(dados["qtd_exemplares"] or 1))
                        e_loc = st.text_input("Localização na Estante", value=dados["localizacao"] or "")

                        st.html(
                            f'<div style="font-size:12px;color:#7A92AD;margin:4px 0 8px;">' +
                            f'<b style="color:#F5A623;">{em_uso}</b> exemplar(es) em uso · ' +
                            f'<b style="color:#2ED573;">{dados["qtd_disponivel"]}</b> disponível(is). ' +
                            'Ao alterar a quantidade total, os disponíveis serão recalculados automaticamente.</div>'
                        )

                        submitted = st.form_submit_button("\U0001F4BE  Salvar Alterações", use_container_width=False)
                        if submitted:
                            if e_titulo and e_autor:
                                ok, msg = db.update_livro(
                                    livro_id, e_titulo, e_autor, e_isbn, e_editora,
                                    e_ano, e_categoria, e_idioma, e_edicao, e_loc, e_qtd,
                                )
                                if ok:
                                    st.success(f"✅ **{e_titulo}** atualizado com sucesso!")
                                else:
                                    st.error(f"Erro ao salvar: {msg}")
                            else:
                                st.error("Título e Autor são obrigatórios.")

        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: USUÁRIOS
# ─────────────────────────────────────────────
def page_usuarios():
    st.markdown('<div class="section-header">Usuários</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cadastro e gestão de usuários do sistema</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👥  Lista de Usuários", "➕  Cadastrar Usuário"])

    with tab1:
        col_s, col_f = st.columns([3, 1])
        with col_s:
            busca_u = st.text_input("", placeholder="🔍  Buscar por nome, CPF ou e-mail…", key="busca_u")
        with col_f:
            filtro_cat_u = st.selectbox("Categoria", ["Todos","Aluno","Professor"], key="filtro_cat_u")

        df_u = db.get_usuarios(busca=busca_u, categoria=filtro_cat_u)

        if not df_u.empty:
            for _, row in df_u.iterrows():
                badge_cls = {"Regular":"badge-green","Inadimplente":"badge-amber","Suspenso":"badge-red"}.get(row["Status"], "badge-teal")
                st.markdown(f"""
                    <div class="status-row" style="padding:12px 0;">
                        <div>
                            <div style="font-weight:500;">{row['Nome']}</div>
                            <div style="font-size:11px;color:#7A92AD;">{row['Categoria']} · {row['E-mail']}</div>
                        </div>
                        <div style="display:flex;align-items:center;gap:16px;">
                            <div style="font-size:12px;color:#7A92AD;">{row['Empréstimos Ativos']} empréstimo(s)</div>
                            <span class="badge {badge_cls}">{row['Status']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_exp2, _ = st.columns([1, 3])
            with col_exp2:
                st.download_button("⬇ Exportar CSV", df_u.to_csv(index=False).encode("utf-8"), "usuarios_bibssj.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nenhum usuário encontrado.")

    with tab2:
        st.markdown('<div class="card"><div class="card-title">Novo Usuário</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            nome_u  = st.text_input("Nome Completo *", key="usu_nome")
            cpf_u   = st.text_input("CPF *", placeholder="000.000.000-00", key="usu_cpf")
            nasc_u  = st.date_input("Data de Nascimento", value=date(2000, 1, 1), key="usu_nasc")
            email_u = st.text_input("E-mail *", key="usu_email")
        with c2:
            cat_u    = st.selectbox("Categoria *", ["Aluno","Professor","Funcionário","Visitante"], key="usu_cat")
            limite_u = st.number_input("Limite de Empréstimos", min_value=1, max_value=10, value=3, key="usu_limite")
            end_u    = st.text_input("Endereço", key="usu_end")
            obs_u    = st.text_area("Observações", height=80, key="usu_obs")
        if st.button("Salvar Usuário", key="btn_salvar_usuario"):
            if nome_u and cpf_u and email_u:
                ok, msg = db.insert_usuario(nome_u, cpf_u, nasc_u, end_u, email_u, cat_u, limite_u, obs_u)
                if ok:
                    st.success(f"✅ Usuário **{nome_u}** cadastrado com sucesso!")
                else:
                    st.error(f"Erro: {msg}")
            else:
                st.error("Preencha os campos obrigatórios (*).")
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: EMPRÉSTIMOS
# ─────────────────────────────────────────────
def page_emprestimos():
    st.markdown('<div class="section-header">Empréstimos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Controle de circulação do acervo</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋  Ativos", "➕  Novo Empréstimo", "↩  Devolução"])

    with tab1:
        df_emp = db.get_emprestimos(apenas_ativos=True)
        if df_emp.empty:
            st.info("Nenhum empréstimo ativo no momento.")
        else:
            hoje = date.today()
            for _, row in df_emp.iterrows():
                try:
                    dev  = date.fromisoformat(str(row["Devolução Prevista"]))
                    diff = (dev - hoje).days
                except Exception:
                    diff = 0
                if row["Status"] == "Atrasado":
                    card_cls    = "overdue"
                    status_html = '<span class="badge badge-red">Atrasado</span>'
                    days_info   = f'<span style="color:#FF6B6B;font-size:11px;">{abs(diff)} dia(s) em atraso · Multa estimada: R$ {abs(diff)*2:.2f}</span>'
                elif diff <= 2:
                    card_cls    = "warning"
                    status_html = '<span class="badge badge-amber">Vence em breve</span>'
                    days_info   = f'<span style="color:#F5A623;font-size:11px;">Vence em {diff} dia(s)</span>'
                else:
                    card_cls    = ""
                    status_html = '<span class="badge badge-teal">Em dia</span>'
                    days_info   = f'<span style="color:#7A92AD;font-size:11px;">Devolução: {dev.strftime("%d/%m/%Y")}</span>'

                st.markdown(f"""
                    <div class="loan-card {card_cls}">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div>
                                <div style="font-weight:600;font-size:14px;">{row['Livro']}</div>
                                <div style="font-size:12px;color:#7A92AD;margin-top:2px;">{row['Usuário']} · Retirada: {row['Retirada']}</div>
                                <div style="margin-top:6px;">{days_info}</div>
                            </div>
                            <div>{status_html}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card"><div class="card-title">Registrar Empréstimo</div>', unsafe_allow_html=True)
        usuarios_lista = db.get_usuarios_ativos()
        livros_lista   = db.get_livros_disponiveis()

        if not usuarios_lista:
            st.warning("Nenhum usuário ativo disponível.")
        elif not livros_lista:
            st.warning("Nenhum livro disponível para empréstimo.")
        else:
            c1, c2 = st.columns(2)

            # ── Coluna esquerda: busca de usuário ──
            with c1:
                busca_usu = st.text_input(
                    "Buscar Usuário *",
                    placeholder="Digite nome ou parte do nome…",
                    key="emp_busca_usuario",
                )
                usu_filtrados = [
                    u for u in usuarios_lista
                    if busca_usu.lower() in u["nome"].lower()
                ] if busca_usu else []

                usu_sel_data = None
                if busca_usu and not usu_filtrados:
                    st.markdown(
                        '<div style="font-size:12px;color:#FF6B6B;margin-top:4px;">Nenhum usuário encontrado.</div>',
                        unsafe_allow_html=True,
                    )
                elif usu_filtrados:
                    st.markdown(
                        f'<div style="font-size:11px;color:#7A92AD;margin-top:2px;">{len(usu_filtrados)} resultado(s)</div>',
                        unsafe_allow_html=True,
                    )
                    usu_map     = {u["nome"]: u for u in usu_filtrados}
                    usu_nome_sel= st.selectbox("Selecionar usuário", list(usu_map.keys()), key="emp_usuario_sel", label_visibility="collapsed")
                    usu_sel_data= usu_map[usu_nome_sel]
                    cat_usu     = usu_sel_data["categoria"]
                    prazo       = 14 if cat_usu == "Professor" else 7
                    st.info(f"**{usu_nome_sel}** · {cat_usu} · Prazo padrão: **{prazo} dias**")
                else:
                    prazo = 7  # default enquanto nenhum usuário selecionado

            # ── Coluna direita: busca de livro ──
            with c2:
                busca_liv = st.text_input(
                    "Buscar Livro *",
                    placeholder="Digite título ou parte do título…",
                    key="emp_busca_livro",
                )
                liv_filtrados = [
                    l for l in livros_lista
                    if busca_liv.lower() in l["titulo"].lower()
                ] if busca_liv else []

                liv_sel_data = None
                if busca_liv and not liv_filtrados:
                    st.markdown(
                        '<div style="font-size:12px;color:#FF6B6B;margin-top:4px;">Nenhum livro disponível encontrado.</div>',
                        unsafe_allow_html=True,
                    )
                elif liv_filtrados:
                    st.markdown(
                        f'<div style="font-size:11px;color:#7A92AD;margin-top:2px;">{len(liv_filtrados)} resultado(s)</div>',
                        unsafe_allow_html=True,
                    )
                    liv_map     = {l["titulo"]: l["id"] for l in liv_filtrados}
                    liv_titulo_sel = st.selectbox("Selecionar livro", list(liv_map.keys()), key="emp_livro_sel", label_visibility="collapsed")
                    liv_sel_data   = {"titulo": liv_titulo_sel, "id": liv_map[liv_titulo_sel]}

                data_dev = st.date_input(
                    "Data de Devolução Prevista",
                    value=date.today() + timedelta(days=prazo),
                    key="emp_data_dev",
                )

            obs_emp = st.text_input("Observações", key="emp_obs")

            # Resumo da seleção antes de confirmar
            if usu_sel_data and liv_sel_data:
                st.markdown(f"""
                    <div style="background:#1E2F45;border-radius:8px;padding:12px 16px;margin:12px 0;font-size:13px;border-left:3px solid #4ECDC4;">
                        <span style="color:#7A92AD;">Resumo · </span>
                        <b>{usu_sel_data['nome']}</b>
                        <span style="color:#7A92AD;"> tomará emprestado </span>
                        <b>{liv_sel_data['titulo']}</b>
                        <span style="color:#7A92AD;"> até </span>
                        <b>{data_dev.strftime('%d/%m/%Y')}</b>
                    </div>
                """, unsafe_allow_html=True)

            btn_disabled = not (usu_sel_data and liv_sel_data)
            if st.button(
                "Confirmar Empréstimo" if not btn_disabled else "Confirmar Empréstimo (selecione usuário e livro)",
                key="btn_confirmar_emp",
                disabled=btn_disabled,
            ):
                ok, msg = db.insert_emprestimo(
                    usuario_id    = usu_sel_data["id"],
                    livro_id      = liv_sel_data["id"],
                    data_retirada = date.today(),
                    data_prevista = data_dev,
                    obs           = obs_emp,
                )
                if ok:
                    st.success(f"✅ Empréstimo de **{liv_sel_data['titulo']}** para **{usu_sel_data['nome']}** registrado!")
                    db.sincronizar_atrasos()
                else:
                    st.error(f"Erro: {msg}")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card"><div class="card-title">Registrar Devolução</div>', unsafe_allow_html=True)

        # ── Passo 1: busca do usuário ──
        busca_dev = st.text_input(
            "Buscar Usuário",
            placeholder="🔍  Digite o nome do usuário…",
            key="dev_busca_usuario",
        )

        if not busca_dev:
            st.markdown(
                '<div style="font-size:13px;color:#7A92AD;margin-top:8px;">Digite o nome do usuário para localizar os empréstimos ativos.</div>',
                unsafe_allow_html=True,
            )
        else:
            usuarios_com_emp = db.buscar_usuarios_com_emprestimo(busca_dev)

            if not usuarios_com_emp:
                st.markdown(
                    '<div style="font-size:13px;color:#FF6B6B;margin-top:8px;">Nenhum usuário com empréstimo ativo encontrado.</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Se mais de um resultado, exibe seletor; caso único, seleciona direto
                if len(usuarios_com_emp) == 1:
                    usuario_selecionado = usuarios_com_emp[0]
                else:
                    usu_dev_map  = {u["nome"]: u for u in usuarios_com_emp}
                    usu_dev_nome = st.selectbox(
                        f"{len(usuarios_com_emp)} usuários encontrados — selecione:",
                        list(usu_dev_map.keys()),
                        key="dev_usuario_sel",
                        label_visibility="visible",
                    )
                    usuario_selecionado = usu_dev_map[usu_dev_nome]

                # ── Passo 2: lista de livros do usuário ──
                emprestimos_usuario = db.get_emprestimos_ativos_por_usuario(usuario_selecionado["id"])
                hoje = date.today()

                st.markdown(f"""
                    <div style="margin:16px 0 12px;">
                        <span style="font-size:15px;font-weight:600;">{usuario_selecionado['nome']}</span>
                        <span style="font-size:12px;color:#7A92AD;margin-left:8px;">{usuario_selecionado['categoria']} · {len(emprestimos_usuario)} exemplar(es) em posse</span>
                    </div>
                """, unsafe_allow_html=True)

                # Renderiza cada livro como card selecionável
                if "dev_livro_selecionado" not in st.session_state:
                    st.session_state.dev_livro_selecionado = None

                for emp in emprestimos_usuario:
                    data_prev    = date.fromisoformat(emp["data_devolucao_prevista"])
                    dias_atraso  = max(0, (hoje - data_prev).days)
                    multa_est    = dias_atraso * 2.0
                    atrasado     = emp["status"] == "Atrasado" or dias_atraso > 0
                    selecionado  = st.session_state.dev_livro_selecionado == emp["id"]

                    # Cores e badges por situação
                    if atrasado:
                        borda     = "#FF6B6B"
                        badge_html= f'<span style="background:rgba(255,107,107,.15);color:#FF6B6B;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;">Atrasado · {dias_atraso} dia(s)</span>'
                        multa_html= f'<span style="color:#FF6B6B;font-size:12px;font-weight:600;">Multa estimada: R$ {multa_est:.2f}</span>'
                    elif (data_prev - hoje).days <= 2:
                        borda     = "#F5A623"
                        badge_html= f'<span style="background:rgba(245,166,35,.15);color:#F5A623;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;">Vence em {(data_prev-hoje).days} dia(s)</span>'
                        multa_html= '<span style="color:#7A92AD;font-size:12px;">Sem multa</span>'
                    else:
                        borda     = "#4ECDC4"
                        badge_html= '<span style="background:rgba(78,205,196,.15);color:#4ECDC4;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600;">Em dia</span>'
                        multa_html= '<span style="color:#7A92AD;font-size:12px;">Sem multa</span>'

                    sel_style = f"outline:2px solid {borda};" if selecionado else ""

                    st.html(f"""
                        <div style="background:#1E2F45;border-radius:10px;padding:14px 18px;
                                    margin-bottom:10px;border-left:4px solid {borda};{sel_style}">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                                <div style="flex:1;">
                                    <div style="font-weight:600;font-size:14px;margin-bottom:2px;">{emp['titulo']}</div>
                                    <div style="font-size:12px;color:#7A92AD;">{emp['autor']}
                                        {'· ' + emp['localizacao'] if emp['localizacao'] else ''}
                                    </div>
                                    <div style="margin-top:6px;display:flex;gap:10px;align-items:center;">
                                        {badge_html}
                                        <span style="font-size:11px;color:#7A92AD;">
                                            Retirada: {emp['data_retirada']} · Prevista: {emp['data_devolucao_prevista']}
                                        </span>
                                    </div>
                                    <div style="margin-top:4px;">{multa_html}</div>
                                </div>
                            </div>
                        </div>
                    """)

                    btn_label = "✓ Selecionado" if selecionado else "Selecionar para devolução"
                    if st.button(btn_label, key=f"dev_sel_{emp['id']}", use_container_width=False):
                        st.session_state.dev_livro_selecionado = emp["id"]
                        st.rerun()

                # ── Passo 3: data e confirmação ──
                emp_sel_id = st.session_state.dev_livro_selecionado
                emp_sel    = next((e for e in emprestimos_usuario if e["id"] == emp_sel_id), None)

                if emp_sel:
                    st.markdown('<hr class="divider">', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:13px;font-weight:500;margin-bottom:10px;">Devolvendo: <span style="color:#4ECDC4;">{emp_sel["titulo"]}</span></div>', unsafe_allow_html=True)

                    data_dev_real = st.date_input(
                        "Data de Devolução Real",
                        value=hoje,
                        key="dev_data_real",
                    )

                    # Recalcula multa com a data escolhida
                    data_prev_sel  = date.fromisoformat(emp_sel["data_devolucao_prevista"])
                    diff_final     = (data_dev_real - data_prev_sel).days
                    multa_final    = max(0, diff_final) * 2.0

                    if diff_final > 0:
                        st.warning(f"⚠ **{diff_final} dia(s) de atraso** · Multa a registrar: **R$ {multa_final:.2f}**")
                    else:
                        st.success("✅ Devolução dentro do prazo — nenhuma multa será aplicada.")

                    if st.button("Confirmar Devolução", key="btn_confirmar_dev"):
                        resultado = db.registrar_devolucao(emp_sel["id"], data_dev_real)
                        if resultado["sucesso"]:
                            st.session_state.dev_livro_selecionado = None
                            if resultado["multa"] > 0:
                                st.warning(f"✅ Devolução registrada. Multa gerada: **R$ {resultado['multa']:.2f}** ({resultado['dias_atraso']} dia(s) de atraso).")
                            else:
                                st.success("✅ Devolução registrada com sucesso. Nenhuma multa aplicada.")
                            db.sincronizar_atrasos()
                            st.rerun()
                else:
                    st.markdown(
                        '<div style="font-size:12px;color:#7A92AD;margin-top:12px;">👆 Selecione um livro acima para prosseguir com a devolução.</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: FINANCEIRO
# ─────────────────────────────────────────────
def page_financeiro():
    # ─ SINCRONIZA ATRASOS E MULTAS ─
    db.sincronizar_atrasos()
    db.sincronizar_multas()  # ← ADICIONE ESTA LINHA
    
    st.markdown('<div class="section-header">Financeiro</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Gestão de multas, cobranças e inadimplência</div>', unsafe_allow_html=True)

    stats = db.get_stats()
    c1, c2, c3 = st.columns(3)
    for col, cls, val, label in [
        (c1, "kpi-red",   f"R$ {stats['multas_pendentes']:.2f}", "Multas Pendentes"),
        (c2, "kpi-green", f"R$ {stats['multas_recebidas']:.2f}", "Recebido (total)"),
        (c3, "kpi-amber", str(stats["inadimplentes"]),           "Usuários Inadimplentes"),
    ]:
        with col:
            st.markdown(f"""
                <div class="kpi-card {cls}">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{val}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📄  Todas as Multas", "✅  Confirmar Pagamento", "📧  Notificações"])

    with tab1:
        df_multas = db.get_multas()
        if not df_multas.empty:
            render_table(df_multas.drop(columns=["ID"]))
        else:
            st.info("Nenhuma multa registrada.")

    with tab2:
        st.markdown('<div class="card"><div class="card-title">Confirmar / Abonar Pagamento</div>', unsafe_allow_html=True)
        pendentes = db.get_multas_pendentes_lista()
        if not pendentes:
            st.success("Nenhuma multa pendente no momento.")
        else:
            multa_map  = {f"{p['nome']} — R$ {p['valor']:.2f}": p for p in pendentes}
            multa_sel  = st.selectbox("Multa pendente", list(multa_map.keys()), key="fin_multa")
            forma_pgto = st.selectbox("Forma de Pagamento", ["PIX / QR Code","Dinheiro","Cartão","Abonado (dispensa)"], key="fin_forma")
            obs_fin    = st.text_input("Observações", key="fin_obs")
            col_qr, col_conf = st.columns(2)
            with col_qr:
                if st.button("Gerar QR Code PIX", use_container_width=True, key="btn_qr"):
                    st.info("📱 QR Code gerado! Apresente ao usuário para pagamento.")
            with col_conf:
                if st.button("Confirmar Pagamento", use_container_width=True, key="btn_confirmar_pgto"):
                    ok = db.confirmar_pagamento(multa_map[multa_sel]["id"], forma_pgto, obs_fin)
                    if ok:
                        st.success("✅ Pagamento confirmado e multa quitada!")
                        st.rerun()
                    else:
                        st.error("Erro ao confirmar pagamento.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card"><div class="card-title">Notificações Automáticas</div>', unsafe_allow_html=True)
        
        tipo_notif = st.selectbox("Tipo de aviso", [
            "Lembrete de vencimento (2 dias antes)",
            "Notificação de atraso", 
            "Cobrança de multa", 
            "Suspensão de conta",
        ], key="notif_tipo")
        
        # Busca dinâmica de usuários
        busca_dest = st.text_input(
            "Buscar destinatários",
            placeholder="Digite nome, e-mail ou selecione abaixo…",
            key="notif_busca"
        )
        
        df_usuarios = db.get_usuarios(categoria="Todos")
        
        # Filtra por tipo de notificação
        if tipo_notif in ["Notificação de atraso", "Suspensão de conta", "Cobrança de multa"]:
            df_usuarios = df_usuarios[df_usuarios["Status"] == "Inadimplente"]
        
        usuarios_filtrados = df_usuarios[
            df_usuarios["Nome"].str.contains(busca_dest, case=False, na=False) |
            df_usuarios["E-mail"].str.contains(busca_dest, case=False, na=False)
        ] if busca_dest else df_usuarios
        
        if not usuarios_filtrados.empty:
            st.markdown(f'<div style="font-size:11px;color:#7A92AD;margin:8px 0;">{len(usuarios_filtrados)} usuário(s) encontrado(s)</div>', unsafe_allow_html=True)
            
            dest_selecionados = st.multiselect(
                "Selecionar destinatários",
                usuarios_filtrados["Nome"].tolist(),
                key="notif_dest_multiselect",
                label_visibility="collapsed"
            )
        else:
            dest_selecionados = []
            if busca_dest:
                st.markdown('<div style="font-size:12px;color:#FF6B6B;">Nenhum usuário encontrado.</div>', unsafe_allow_html=True)
        
        # Preview da notificação
        if dest_selecionados:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="font-size:12px;color:#7A92AD;text-transform:uppercase;letter-spacing:.08em;">Preview</div>', unsafe_allow_html=True)
            corpo_preview = f"<p>Olá {dest_selecionados[0]},</p><p>Esta é uma notificação de <b>{tipo_notif}</b>.</p>"
            st.markdown(corpo_preview, unsafe_allow_html=True)
        
        col_clear, col_send = st.columns([1, 1])
        
        with col_clear:
            if st.button("Limpar", use_container_width=True, key="btn_limpar_notif"):
                st.session_state.notif_dest_multiselect = []
                st.rerun()
        
        with col_send:
            btn_disabled = len(dest_selecionados) == 0
            if st.button(
                "Enviar Notificações",
                use_container_width=True,
                key="btn_enviar_notif",
                disabled=btn_disabled,
            ):
                if not btn_disabled:
                    enviados = 0
                    falhas = 0
                    usuarios_com_erro = []

                    for usuario_nome in dest_selecionados:
                        usuario_data = usuarios_filtrados[usuarios_filtrados["Nome"] == usuario_nome].iloc[0]
                        email_dest = usuario_data["E-mail"]
                        
                        # Monta corpo da notificação
                        corpo_email = f"""
                        <p>Olá <b>{usuario_nome}</b>,</p>
                        <p>Esta é uma notificação de <b>{tipo_notif}</b>.</p>
                        <p>Favor verificar sua conta na plataforma BibSSJ para mais detalhes.</p>
                        <br>
                        <p>Atenciosamente,<br>Equipe BibSSJ</p>
                        """
                        
                        # Chama função de envio (certifique-se de que está definida)
                        if enviar_email(email_dest, f"BibSSJ - {tipo_notif}", corpo_email):
                            enviados += 1
                        else:
                            falhas += 1
                            usuarios_com_erro.append(usuario_nome)

                    # Feedback visual
                    if enviados > 0:
                        st.success(f"✅ {enviados} notificação(ões) enviada(s) com sucesso.")
                    if falhas > 0:
                        st.error(f"❌ {falhas} falha(s) de envio para: {', '.join(usuarios_com_erro)}")
                    if enviados == 0 and falhas == 0:
                        st.info("ℹ️ Nenhum e-mail enviado. Verifique se há destinatários selecionados.")
                else:
                    st.error("❌ Selecione ao menos um destinatário.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE: ADMINISTRATIVO
# ─────────────────────────────────────────────
def page_admin():
    st.markdown('<div class="section-header">Administrativo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Configurações e gestão avançada do sistema</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤  Admins & Permissões", "📢  Avisos Gerais", "📊  Relatórios"])

    with tab1:
        st.markdown('<div class="card"><div class="card-title">Administradores do Sistema</div>', unsafe_allow_html=True)
        for adm in db.get_administradores():
            color = {"Super Admin":"#FF6B6B","Bibliotecária":"#4ECDC4","Operador":"#F5A623"}.get(adm["perfil"], "#7A92AD")
            ativo_txt = "Ativo" if adm["ativo"] else "Inativo"
            st.markdown(f"""
                <div class="status-row">
                    <div>
                        <div style="font-weight:500;">{adm['nome']}</div>
                        <div style="font-size:11px;color:#7A92AD;">{adm['email']} · {ativo_txt}</div>
                    </div>
                    <span class="badge" style="background:rgba(255,255,255,.07);color:{color};">{adm['perfil']}</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Cadastrar Novo Administrador</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            nome_adm  = st.text_input("Nome *",   key="adm_nome")
            email_adm = st.text_input("E-mail *", key="adm_email")
        with c2:
            role_adm  = st.selectbox("Perfil de Acesso", ["Operador","Bibliotecária","Super Admin"], key="adm_perfil")
            senha_adm = st.text_input("Senha provisória *", type="password", key="adm_senha")
        if st.button("Cadastrar Admin", key="btn_cadastrar_adm"):
            if nome_adm and email_adm and senha_adm:
                ok, msg = db.insert_administrador(nome_adm, email_adm, senha_adm, role_adm)
                if ok:
                    st.success(f"✅ Administrador **{nome_adm}** cadastrado com perfil **{role_adm}**.")
                else:
                    st.error(f"Erro: {msg}")
            else:
                st.error("Preencha os campos obrigatórios.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card"><div class="card-title">Alterar Senha de Administrador</div>', unsafe_allow_html=True)
        adms = db.get_administradores()
        if adms:
            adm_names = {adm["nome"]: adm["id"] for adm in adms}
            adm_selecionado = st.selectbox("Selecionar Administrador", list(adm_names.keys()), key="adm_alterar_sel")
            adm_id = adm_names[adm_selecionado]
            
            c_alt1, c_alt2 = st.columns(2)
            with c_alt1:
                nova_senha = st.text_input("Nova Senha *", type="password", key="adm_nova_senha")
            with c_alt2:
                confirma_senha = st.text_input("Confirmar Nova Senha *", type="password", key="adm_confirma_senha")
            
            if st.button("Atualizar Senha", key="btn_alterar_senha_adm"):
                if nova_senha and confirma_senha:
                    if nova_senha == confirma_senha:
                        ok, msg = db.atualizar_senha_administrador(adm_id, nova_senha)
                        if ok:
                            st.success(f"✅ Senha de **{adm_selecionado}** atualizada com sucesso!")
                        else:
                            st.error(f"Erro: {msg}")
                    else:
                        st.error("❌ As senhas não coincidem.")
                else:
                    st.error("Preencha os campos de senha.")
        else:
            st.info("Nenhum administrador cadastrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card"><div class="card-title">Enviar Aviso Geral</div>', unsafe_allow_html=True)
        dest_aviso  = st.multiselect("Destinatários", ["Todos os usuários","Alunos","Professores","Inadimplentes"], key="aviso_dest")
        titulo_avis = st.text_input("Assunto do aviso", key="aviso_titulo")
        corpo_avis  = st.text_area("Mensagem", height=120, placeholder="Digite o conteúdo do aviso aqui…", key="aviso_corpo")
        if st.button("Enviar Aviso", key="btn_enviar_aviso"):
            if dest_aviso and titulo_avis and corpo_avis:
                # Busca usuários conforme seleção
                df_usuarios = db.get_usuarios()
                usuarios_selecionados = df_usuarios
                
                # Filtra por categoria
                if "Todos os usuários" not in dest_aviso:
                    filtro_categorias = []
                    if "Alunos" in dest_aviso:
                        filtro_categorias.append("Aluno")
                    if "Professores" in dest_aviso:
                        filtro_categorias.append("Professor")
                    if "Inadimplentes" in dest_aviso:
                        usuarios_selecionados = usuarios_selecionados[usuarios_selecionados["Status"] == "Inadimplente"]
                    else:
                        usuarios_selecionados = usuarios_selecionados[usuarios_selecionados["Categoria"].isin(filtro_categorias)]
                
                # Envia email para cada usuário
                enviados = 0
                falhas = 0
                usuarios_erro = []
                
                corpo_html = f"""
                <h3>{titulo_avis}</h3>
                <p>{corpo_avis}</p>
                <hr>
                <p style="font-size:12px;color:#7A92AD;">Mensagem enviada pela administração do BibSSJ</p>
                """
                
                for _, usuario in usuarios_selecionados.iterrows():
                    if enviar_email(usuario["E-mail"], f"BibSSJ - {titulo_avis}", corpo_html):
                        enviados += 1
                    else:
                        falhas += 1
                        usuarios_erro.append(usuario["Nome"])
                
                # Feedback
                if enviados > 0:
                    st.success(f"✅ Aviso **{titulo_avis}** enviado para {enviados} usuário(s).")
                if falhas > 0:
                    st.warning(f"⚠ {falhas} falha(s) de envio para: {', '.join(usuarios_erro[:5])}")
            else:
                st.error("Preencha todos os campos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card"><div class="card-title">Geração de Relatórios</div>', unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            tipo_rel = st.selectbox("Tipo de Relatório", [
                "Inventário do Acervo","Empréstimos por Período",
                "Usuários Inadimplentes","Arrecadação de Multas","Livros Mais Emprestados",
            ], key="rel_tipo")
            periodo  = st.date_input("Período", value=[date.today() - timedelta(days=30), date.today()], key="rel_periodo")
        with col_r2:
            fmt_rel = st.selectbox("Formato de Exportação", ["CSV","PDF","Excel"], key="rel_fmt")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Gerar Relatório", use_container_width=True, key="btn_gerar_rel"):
                # Gera relatório a partir do banco
                if tipo_rel == "Inventário do Acervo":
                    df_rel = db.get_livros()
                elif tipo_rel == "Usuários Inadimplentes":
                    df_rel = db.get_usuarios()
                    df_rel = df_rel[df_rel["Status"] == "Inadimplente"]
                elif tipo_rel == "Arrecadação de Multas":
                    df_rel = db.get_multas()
                else:
                    df_rel = db.get_emprestimos()

                if fmt_rel == "PDF":
                    pdf_bytes = gerar_pdf_relatorio(df_rel, tipo_rel)
                    st.download_button(
                        f"⬇ Baixar {tipo_rel} (PDF)",
                        pdf_bytes,
                        f"relatorio_{tipo_rel.lower().replace(' ','_')}.pdf",
                        "application/pdf",
                        use_container_width=True,
                        key="btn_download_rel",
                    )
                elif fmt_rel == "CSV":
                    st.download_button(
                        f"⬇ Baixar {tipo_rel} (CSV)",
                        df_rel.to_csv(index=False).encode("utf-8"),
                        f"relatorio_{tipo_rel.lower().replace(' ','_')}.csv",
                        "text/csv",
                        use_container_width=True,
                        key="btn_download_rel",
                    )
                else:  # Excel
                    excel_bytes = BytesIO()
                    with pd.ExcelWriter(excel_bytes, engine='openpyxl') as writer:
                        df_rel.to_excel(writer, index=False)
                    excel_bytes.seek(0)
                    st.download_button(
                        f"⬇ Baixar {tipo_rel} (Excel)",
                        excel_bytes.getvalue(),
                        f"relatorio_{tipo_rel.lower().replace(' ','_')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="btn_download_rel",
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Resumo do Sistema</div>', unsafe_allow_html=True)
        stats = db.get_stats()
        for label, val in [
            ("Total de Livros (títulos)", stats["total_titulos"]),
            ("Total de Exemplares",       stats["total_exemplares"]),
            ("Exemplares Disponíveis",    stats["total_disponiveis"]),
            ("Usuários Ativos",           stats["usuarios_ativos"]),
            ("Empréstimos Ativos",        stats["emprestimos_ativos"]),
            ("Devoluções Atrasadas",      stats["devolucoes_atrasadas"]),
            ("Multas Pendentes",          f"R$ {stats['multas_pendentes']:.2f}"),
        ]:
            st.markdown(f"""
                <div class="status-row">
                    <span style="color:#7A92AD;">{label}</span>
                    <span style="font-weight:600;">{val}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER: ENVIAR EMAIL
# ─────────────────────────────────────────────
def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    """Envia e-mail de notificação"""
    try:
        remetente = "seu_email@gmail.com"
        senha = "sua_senha_aqui"
        
        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="border-bottom: 3px solid #4ECDC4; padding-bottom: 16px; margin-bottom: 20px;">
                        <h2 style="color: #4ECDC4; margin: 0;">📚 BibSSJ</h2>
                        <p style="color: #7A92AD; margin: 4px 0 0 0; font-size: 12px;">Biblioteca Universitária</p>
                    </div>
                    <div style="margin: 20px 0;">
                        {corpo}
                    </div>
                    <div style="border-top: 1px solid #CCCCCC; padding-top: 16px; margin-top: 20px; font-size: 11px; color: #7A92AD;">
                        <p>Esta é uma mensagem automática. Não responda diretamente.</p>
                        <p>© 2025 BibSSJ · Todos os direitos reservados</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# ─────────────────────────────────────────────
# TEMPLATES DE NOTIFICAÇÃO
# ─────────────────────────────────────────────
def gerar_corpo_notificacao(tipo: str, usuario_nome: str, dados: dict = None) -> str:
    """Gera corpo da notificação baseado no tipo"""
    if tipo == "Lembrete de vencimento (2 dias antes)":
        return f"""
        <h3>Olá, {usuario_nome}!</h3>
        <p>Este é um lembrete de que seu empréstimo vence em <strong>2 dias</strong>.</p>
        <div style="background: #F5F5F5; padding: 12px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0;"><strong>Livro:</strong> {dados.get('livro', 'N/A')}</p>
            <p style="margin: 8px 0 0 0;"><strong>Devolver até:</strong> {dados.get('data_devolucao', 'N/A')}</p>
        </div>
        <p>Renove seu empréstimo se necessário antes da data de vencimento.</p>
        """
    
    elif tipo == "Notificação de atraso":
        return f"""
        <h3>Olá, {usuario_nome}!</h3>
        <p style="color: #FF6B6B;"><strong>⚠ AVISO: Seu empréstimo está ATRASADO</strong></p>
        <div style="background: #FFF5F5; padding: 12px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #FF6B6B;">
            <p style="margin: 0;"><strong>Livro:</strong> {dados.get('livro', 'N/A')}</p>
            <p style="margin: 8px 0 0 0;"><strong>Dias de atraso:</strong> {dados.get('dias_atraso', '0')}</p>
            <p style="margin: 8px 0 0 0;"><strong>Multa acumulada:</strong> R$ {dados.get('multa', '0.00')}</p>
        </div>
        <p>Favor devolver o livro com urgência para evitar multas adicionais.</p>
        """
    
    elif tipo == "Cobrança de multa":
        return f"""
        <h3>Olá, {usuario_nome}!</h3>
        <p><strong>Aviso de Cobrança de Multa</strong></p>
        <div style="background: #F5F5F5; padding: 12px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 0;"><strong>Multa pendente:</strong> R$ {dados.get('multa_valor', '0.00')}</p>
            <p style="margin: 8px 0 0 0;"><strong>Motivo:</strong> {dados.get('motivo', 'Atraso na devolução')}</p>
            <p style="margin: 8px 0 0 0;"><strong>Data de vencimento:</strong> {dados.get('data_vencimento', 'N/A')}</p>
        </div>
        <p>Queira procurar a biblioteca para efetuar o pagamento da multa.</p>
        """
    
    elif tipo == "Suspensão de conta":
        return f"""
        <h3>Olá, {usuario_nome}!</h3>
        <p style="color: #FF6B6B;"><strong>⛔ NOTIFICAÇÃO: Sua conta foi SUSPENSA</strong></p>
        <div style="background: #FFF5F5; padding: 12px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #FF6B6B;">
            <p style="margin: 0;">Sua conta foi suspensa devido a:</p>
            <ul style="margin: 8px 0 0 0;">
                <li>Multas em atraso</li>
                <li>Empréstimos não devolvidos</li>
            </ul>
        </div>
        <p>Entre em contato com a biblioteca para regularizar sua situação.</p>
        """
    
    return "<p>Mensagem padrão</p>"

# ─────────────────────────────────────────────
# HELPER: GERA PDF RELATÓRIO
# ─────────────────────────────────────────────
def gerar_pdf_relatorio(df: pd.DataFrame, titulo: str) -> bytes:
    buffer = BytesIO()
    margem = 0.5 * inch
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margem,
        rightMargin=margem,
        topMargin=margem,
        bottomMargin=margem,
    )

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        "Cell", parent=styles["Normal"], fontSize=8, leading=10, alignment=0
    )

    story = []
    titulo_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=3,
        fontName="Helvetica-Bold",
    )
    story.append(Paragraph(f"Relatório: {titulo}", titulo_style))
    story.append(
        Paragraph(
            f"<font size=8 color='#666666'>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</font>",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    dados = [list(df.columns)]
    for _, row in df.iterrows():
        dados.append([str(v) if pd.notna(v) else "" for v in row])

    largura_disponivel = A4[0] - margem * 2
    num_cols = len(df.columns) if len(df.columns) else 1
    col_widths = [largura_disponivel / num_cols] * num_cols

    dados_formatados = []
    for i, linha in enumerate(dados):
        if i == 0:
            dados_formatados.append([Paragraph(str(c), ParagraphStyle("Header", parent=styles["Normal"], fontSize=9, leading=11, spaceAfter=2, fontName="Helvetica-Bold")) for c in linha])
        else:
            dados_formatados.append([Paragraph(c, cell_style) for c in linha])

    table = Table(dados_formatados, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#333333")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
def main():
    inject_css()
    if not st.session_state.logged_in:
        login_page()
        return

    sidebar()

    page = st.session_state.page
    if   page == "Dashboard":      page_dashboard()
    elif page == "Acervo":         page_acervo()
    elif page == "Usuários":       page_usuarios()
    elif page == "Empréstimos":    page_emprestimos()
    elif page == "Financeiro":     page_financeiro()
    elif page == "Administrativo": page_admin()

if __name__ == "__main__":
    main()
