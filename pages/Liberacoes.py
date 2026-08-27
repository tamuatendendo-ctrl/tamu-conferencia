# -*- coding: utf-8 -*-

import os
import json
import re
import textwrap
from datetime import datetime, date

import requests
import gspread
import streamlit as st

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
SUPABASE_REFRESH_TOKEN = st.secrets["SUPABASE_REFRESH_TOKEN"]


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_CREDENCIAL = "google_oauth.json"
ARQUIVO_TOKEN_GOOGLE = "google_token.json"
ARQUIVO_TOKEN_SUPABASE = "supabase_token.json"

SPREADSHEET_ID = "1DSrif82ExLPDuloafYUk2F8xXKvf0mAkMSDXqfQ3EOs"

ABA_CHECKINS = "CHECKINS DO DIA"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]


# ============================================================
# CONFIGURAÇÃO STREAMLIT
# ============================================================

st.set_page_config(
    page_title="TAMU — Conferência de Liberações",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CSS
# ============================================================

CSS = """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(99, 102, 241, 0.06),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(239, 68, 68, 0.05),
            transparent 30%
        ),
        #f7f8fc;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}


/* ==========================================================
   HERO
========================================================== */

.hero {
    position: relative;
    overflow: hidden;

    background:
        radial-gradient(
            circle at 90% 10%,
            rgba(239, 68, 68, 0.30),
            transparent 30%
        ),
        linear-gradient(
            110deg,
            #0b1425 0%,
            #111827 55%,
            #351827 100%
        );

    border-radius: 22px;

    padding: 42px 48px;

    margin-bottom: 24px;

    box-shadow:
        0 20px 45px rgba(15, 23, 42, 0.16);
}

.hero-title {
    color: white;

    font-size: 38px;

    font-weight: 800;

    letter-spacing: -1px;

    margin-bottom: 8px;
}

.hero-subtitle {
    color: #cbd5e1;

    font-size: 17px;

    margin-bottom: 24px;
}

.hero-date {
    display: inline-flex;

    align-items: center;

    gap: 10px;

    background: rgba(255,255,255,0.09);

    border: 1px solid rgba(255,255,255,0.08);

    color: white;

    border-radius: 12px;

    padding: 10px 16px;

    font-size: 16px;

    font-weight: 700;
}


/* ==========================================================
   BOTÃO
========================================================== */

div.stButton > button {

    width: 100%;

    min-height: 55px;

    border: none;

    border-radius: 12px;

    background:
        linear-gradient(
            135deg,
            #ff3344,
            #ff5964
        );

    color: white;

    font-size: 16px;

    font-weight: 800;

    letter-spacing: 0.2px;

    box-shadow:
        0 10px 25px rgba(255, 51, 68, 0.20);

    transition: all 0.2s ease;
}

div.stButton > button:hover {

    transform: translateY(-1px);

    box-shadow:
        0 14px 30px rgba(255, 51, 68, 0.28);

    background:
        linear-gradient(
            135deg,
            #f51f31,
            #ff4c59
        );
}


/* ==========================================================
   MÉTRICAS
========================================================== */

.metric-card {

    background: white;

    border-radius: 18px;

    padding: 22px;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 8px 25px rgba(15, 23, 42, 0.06);

    text-align: center;
}

.metric-label {

    color: #64748b;

    font-size: 14px;

    font-weight: 700;

    margin-bottom: 8px;
}

.metric-value {

    color: #111827;

    font-size: 34px;

    font-weight: 900;
}


/* ==========================================================
   CARDS
========================================================== */

.cards-wrapper {

    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 18px;

    margin-top: 24px;

    align-items: start;
}

.status-card {

    background: white;

    border-radius: 18px;

    overflow: hidden;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 8px 25px rgba(15, 23, 42, 0.06);
}

.status-header {

    display: flex;

    align-items: center;

    gap: 11px;

    padding: 16px 18px;

    border-bottom: 1px solid #edf0f4;
}

.status-icon {

    width: 36px;

    height: 36px;

    min-width: 36px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 18px;

    font-weight: 900;
}

.status-title {

    font-size: 18px;

    font-weight: 800;

    line-height: 1.2;
}


/* ==========================================================
   VERDE
========================================================== */

.green-card {
    border-color: #ccebd7;
}

.green-card .status-header {
    background: #f0fdf4;
}

.green-card .status-icon {
    background: #22c55e;
    color: white;
}

.green-card .status-title {
    color: #15803d;
}


/* ==========================================================
   VERMELHO
========================================================== */

.red-card {
    border-color: #fecaca;
}

.red-card .status-header {
    background: #fff1f2;
}

.red-card .status-icon {
    background: #ef4444;
    color: white;
}

.red-card .status-title {
    color: #dc2626;
}


/* ==========================================================
   APARTAMENTOS
========================================================== */

.apt-row {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 12px;

    padding: 13px 16px;

    border-bottom: 1px solid #f0f2f5;
}

.apt-row:last-child {
    border-bottom: none;
}

.apt-left {

    display: flex;

    align-items: center;

    gap: 10px;

    min-width: 0;
}

.apt-code {

    font-size: 16px;

    font-weight: 800;

    color: #111827;

    white-space: nowrap;
}

.apt-description {

    font-size: 14px;

    color: #64748b;

    text-align: right;
}


/* ==========================================================
   ÍCONES PEQUENOS
========================================================== */

.small-icon {

    width: 26px;

    height: 26px;

    min-width: 26px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 13px;

    font-weight: 900;
}

.green-small {
    background: #dcfce7;
    color: #15803d;
}

.red-small {
    background: #fee2e2;
    color: #dc2626;
}


/* ==========================================================
   CARD VAZIO
========================================================== */

.empty-card {

    padding: 35px 20px;

    text-align: center;

    color: #94a3b8;

    font-size: 15px;
}


/* ==========================================================
   SUCESSO
========================================================== */

.success-box {

    margin-top: 24px;

    background: #f0fdf4;

    border: 1px solid #bbf7d0;

    border-radius: 16px;

    padding: 24px;

    text-align: center;

    color: #15803d;

    font-size: 20px;

    font-weight: 800;
}


/* ==========================================================
   FOOTER
========================================================== */

.footer {

    text-align: center;

    color: #94a3b8;

    font-size: 13px;

    margin-top: 32px;

    padding-bottom: 10px;
}


/* ==========================================================
   RESPONSIVO
========================================================== */

@media (max-width: 900px) {

    .cards-wrapper {

        grid-template-columns: 1fr;
    }

    .hero {

        padding: 30px 25px;
    }

    .hero-title {

        font-size: 28px;
    }

    .apt-description {

        white-space: normal;
    }
}

</style>
"""

st.markdown(
    CSS,
    unsafe_allow_html=True
)


# ============================================================
# NORMALIZAR CÓDIGO DO APARTAMENTO
# ============================================================

def normalizar_codigo(codigo):

    if codigo is None:
        return ""

    codigo = str(codigo).strip().upper()

    codigo = codigo.replace(
        " ",
        ""
    )

    codigo = re.sub(
        r"[A-Z]+$",
        "",
        codigo
    )

    return codigo


# ============================================================
# AUTENTICAÇÃO GOOGLE
# ============================================================

def autenticar_google():

    credentials = None

    # Streamlit Cloud:
    # utiliza o token do Google salvo em Secrets.
    try:

        if "GOOGLE_TOKEN_JSON" in st.secrets:

            dados_token = st.secrets[
                "GOOGLE_TOKEN_JSON"
            ]

            if isinstance(
                dados_token,
                str
            ):

                dados_token = json.loads(
                    dados_token
                )

            credentials = (
                Credentials
                .from_authorized_user_info(
                    dict(dados_token),
                    SCOPES
                )
            )

    except Exception as erro:

        raise Exception(
            "Não foi possível carregar "
            "GOOGLE_TOKEN_JSON do Streamlit Secrets. "
            f"Detalhes: {erro}"
        )

    # Ambiente local (VS Code):
    # mantém o mesmo funcionamento através do arquivo local.
    if (
        credentials is None
        and os.path.exists(
            ARQUIVO_TOKEN_GOOGLE
        )
    ):

        credentials = (
            Credentials
            .from_authorized_user_file(
                ARQUIVO_TOKEN_GOOGLE,
                SCOPES
            )
        )

    if credentials:

        if (
            credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(
                Request()
            )

    if (
        not credentials
        or not credentials.valid
    ):

        raise Exception(
            "Credenciais do Google não encontradas. "
            "No Streamlit Cloud, configure "
            "GOOGLE_TOKEN_JSON em Secrets. "
            "Localmente, mantenha o arquivo "
            "google_token.json."
        )

    return credentials

# ============================================================
# TOKEN SUPABASE
# ============================================================

def salvar_token_supabase(
    access_token,
    refresh_token=None,
    expires_in=None
):

    dados = {

        "access_token":
            access_token,

        "refresh_token":
            refresh_token,

        "expires_in":
            expires_in,

        "saved_at":
            datetime.now().isoformat()
    }

    with open(
        ARQUIVO_TOKEN_SUPABASE,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            indent=4,
            ensure_ascii=False
        )


def renovar_token_supabase():

    url = (
        f"{SUPABASE_URL}"
        f"/auth/v1/token"
        f"?grant_type=refresh_token"
    )

    headers = {

        "apikey":
            SUPABASE_ANON_KEY,

        "Content-Type":
            "application/json"
    }

    refresh_token = None

    if os.path.exists(
        ARQUIVO_TOKEN_SUPABASE
    ):

        try:

            with open(
                ARQUIVO_TOKEN_SUPABASE,
                "r",
                encoding="utf-8"
            ) as arquivo:

                dados_token = json.load(
                    arquivo
                )

            refresh_token = dados_token.get(
                "refresh_token"
            )

        except Exception:

            refresh_token = None

    if not refresh_token:

        refresh_token = (
            SUPABASE_REFRESH_TOKEN
        )

    payload = {

        "refresh_token":
            refresh_token
    }

    resposta = requests.post(

        url,

        headers=headers,

        json=payload,

        timeout=30
    )

    if resposta.status_code != 200:

        raise Exception(

            "Não foi possível renovar "
            "a sessão do Supabase.\n\n"

            f"HTTP {resposta.status_code}\n"

            f"{resposta.text}"
        )

    dados = resposta.json()

    access_token = dados.get(
        "access_token"
    )

    novo_refresh_token = dados.get(
        "refresh_token"
    )

    expires_in = dados.get(
        "expires_in"
    )

    if not access_token:

        raise Exception(

            "Supabase não retornou "
            "um access token."
        )

    if not novo_refresh_token:

        novo_refresh_token = refresh_token

    salvar_token_supabase(

        access_token,

        novo_refresh_token,

        expires_in
    )

    return access_token


def obter_access_token_supabase():

    if os.path.exists(
        ARQUIVO_TOKEN_SUPABASE
    ):

        try:

            with open(
                ARQUIVO_TOKEN_SUPABASE,
                "r",
                encoding="utf-8"
            ) as arquivo:

                dados = json.load(
                    arquivo
                )

            access_token = dados.get(
                "access_token"
            )

            if access_token:

                return access_token

        except Exception:

            pass

    return renovar_token_supabase()


# ============================================================
# SUPABASE GET
# ============================================================

def supabase_get(
    endpoint,
    params=None
):

    access_token = (
        obter_access_token_supabase()
    )

    headers = {

        "apikey":
            SUPABASE_ANON_KEY,

        "Authorization":
            f"Bearer {access_token}"
    }

    resposta = requests.get(

        endpoint,

        params=params,

        headers=headers,

        timeout=30
    )

    if resposta.status_code == 401:

        try:

            erro = resposta.json()

        except Exception:

            erro = {}

        mensagem = str(
            erro.get(
                "message",
                ""
            )
        ).lower()

        if (
            "jwt" in mensagem
            or "expired" in mensagem
            or "token" in mensagem
        ):

            access_token = (
                renovar_token_supabase()
            )

            headers = {

                "apikey":
                    SUPABASE_ANON_KEY,

                "Authorization":
                    f"Bearer {access_token}"
            }

            resposta = requests.get(

                endpoint,

                params=params,

                headers=headers,

                timeout=30
            )

    return resposta


# ============================================================
# BUSCAR CHECK-INS DA PLANILHA
# ============================================================

def buscar_checkins():

    credentials = (
        autenticar_google()
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet = (
        client.open_by_key(
            SPREADSHEET_ID
        )
    )

    worksheet = (
        spreadsheet.worksheet(
            ABA_CHECKINS
        )
    )

    dados = (
        worksheet.get_all_values()
    )

    padrao_apartamento = re.compile(
        r"^\d{6}[A-Z]?$",
        re.IGNORECASE
    )

    checkins = []

    for numero_linha, linha in enumerate(
        dados,
        start=1
    ):

        for indice_coluna, valor in enumerate(
            linha
        ):

            if valor is None:
                continue

            valor = str(
                valor
            ).strip()

            if not valor:
                continue

            if not padrao_apartamento.fullmatch(
                valor
            ):
                continue

            codigo_original = valor

            codigo = normalizar_codigo(
                codigo_original
            )

            if not codigo:
                continue

            hospede = ""

            if (
                indice_coluna + 1
                < len(linha)
            ):

                possivel_hospede = str(
                    linha[
                        indice_coluna + 1
                    ]
                ).strip()

                if possivel_hospede:

                    eh_data = False

                    for formato in (

                        "%d/%m",

                        "%d/%m/%Y",

                        "%d/%m/%y"

                    ):

                        try:

                            datetime.strptime(
                                possivel_hospede,
                                formato
                            )

                            eh_data = True

                            break

                        except ValueError:

                            continue

                    if not eh_data:

                        hospede = (
                            possivel_hospede
                        )

            registro_existente = False

            for registro in checkins:

                if (

                    registro[
                        "codigo_original"
                    ]
                    == codigo_original

                    and

                    registro[
                        "hospede"
                    ]
                    == hospede

                    and

                    registro[
                        "linha"
                    ]
                    == numero_linha

                ):

                    registro_existente = True

                    break

            if registro_existente:
                continue

            checkins.append({

                "codigo_original":
                    codigo_original,

                "codigo":
                    codigo,

                "hospede":
                    hospede,

                "linha":
                    numero_linha
            })

    return checkins


# ============================================================
# BUSCAR LIBERAÇÕES NO SUPABASE
# ============================================================

def buscar_liberacoes_hoje():

    hoje = date.today().strftime(
        "%Y-%m-%d"
    )

    endpoint = (
        f"{SUPABASE_URL}"
        f"/rest/v1/"
        f"reservations"
    )

    parametros = {

        "select":
            (
                "id,"
                "checkin_date,"
                "checkin_time,"
                "checkout_date,"
                "checkout_time,"
                "status,"
                "properties("
                    "id,"
                    "code"
                "),"
                "reservation_tenants("
                    "is_primary,"
                    "tenants("
                        "full_name"
                    ")"
                ")"
            ),

        "status":
            "eq.active",

        "checkin_date":
            f"eq.{hoje}",

        "order":
            "checkin_time.asc"
    }

    resposta = supabase_get(
        endpoint,
        parametros
    )

    if resposta.status_code != 200:

        raise Exception(

            "Falha ao consultar "
            "as liberações.\n\n"

            f"HTTP {resposta.status_code}\n"

            f"{resposta.text}"
        )

    return resposta.json()


# ============================================================
# EXTRAIR DADOS DA LIBERAÇÃO
# ============================================================

def extrair_dados_liberacao(
    reserva
):

    properties = reserva.get(
        "properties"
    )

    if isinstance(
        properties,
        list
    ):

        if properties:
            properties = properties[0]

        else:
            properties = {}

    if not isinstance(
        properties,
        dict
    ):

        properties = {}

    codigo_original = str(
        properties.get(
            "code",
            ""
        )
    ).strip()

    codigo = normalizar_codigo(
        codigo_original
    )

    hospede = ""

    reservation_tenants = reserva.get(
        "reservation_tenants",
        []
    )

    if isinstance(
        reservation_tenants,
        list
    ):

        principal = None

        for item in reservation_tenants:

            if item.get(
                "is_primary"
            ):

                principal = item

                break

        if principal is None:

            if reservation_tenants:
                principal = reservation_tenants[0]

        if principal:

            tenant = principal.get(
                "tenants",
                {}
            )

            if isinstance(
                tenant,
                list
            ):

                if tenant:
                    tenant = tenant[0]

                else:
                    tenant = {}

            if isinstance(
                tenant,
                dict
            ):

                hospede = str(
                    tenant.get(
                        "full_name",
                        ""
                    )
                ).strip()

    return {

        "codigo_original":
            codigo_original,

        "codigo":
            codigo,

        "hospede":
            hospede,

        "checkin_time":
            reserva.get(
                "checkin_time",
                ""
            )
    }


# ============================================================
# CONFERÊNCIA
# ============================================================

def conferir_liberacoes():

    checkins = buscar_checkins()

    reservas = buscar_liberacoes_hoje()

    liberacoes = []

    for reserva in reservas:

        dados = extrair_dados_liberacao(
            reserva
        )

        if dados["codigo"]:

            liberacoes.append(
                dados
            )

    codigos_liberacoes = set(

        liberacao["codigo"]

        for liberacao in liberacoes

        if liberacao["codigo"]
    )

    checkins_com_liberacao = []

    checkins_sem_liberacao = []

    for checkin in checkins:

        if (
            checkin["codigo"]
            in codigos_liberacoes
        ):

            checkins_com_liberacao.append(
                checkin
            )

        else:

            checkins_sem_liberacao.append(
                checkin
            )

    return (

        checkins,

        liberacoes,

        checkins_com_liberacao,

        checkins_sem_liberacao
    )


# ============================================================
# HERO
# ============================================================

hoje_formatado = date.today().strftime(
    "%d/%m/%Y"
)

st.markdown(
    f'<div class="hero">'
    f'<div class="hero-title">🔐 Conferência de Liberações</div>'
    f'<div class="hero-subtitle">Verifique automaticamente se todos os check-ins do dia possuem liberação cadastrada.</div>'
    f'<div class="hero-date">📅 {hoje_formatado}</div>'
    f'</div>',
    unsafe_allow_html=True
)


# ============================================================
# BOTÕES DE NAVEGAÇÃO E CONFERÊNCIA
# ============================================================

# Botão de voltar permanece à esquerda, logo abaixo do HERO.
col_voltar, _ = st.columns([1, 4])

with col_voltar:

    if st.button(
        "← VOLTAR À CONFERÊNCIA",
        key="voltar_conferencia"
    ):

        st.switch_page(
            "app.py"
        )


# Botão principal centralizado visualmente na página.
# A coluna central recebe largura maior e o botão ocupa toda essa coluna.
_, col_conferir, _ = st.columns([2, 3, 2])

with col_conferir:

    iniciar_conferencia = st.button(
        "🔍 CONFERIR LIBERAÇÕES DO DIA",
        key="conferir_liberacoes",
        use_container_width=True
    )


if iniciar_conferencia:

    try:

        with st.spinner(
            "Consultando check-ins e liberações..."
        ):

            (

                checkins,

                liberacoes,

                checkins_com_liberacao,

                checkins_sem_liberacao

            ) = conferir_liberacoes()


        # ====================================================
        # MÉTRICAS
        # ====================================================

        total_checkins = len(
            checkins
        )

        total_liberacoes = len(
            set(
                liberacao["codigo"]

                for liberacao in liberacoes
            )
        )

        total_pendencias = len(
            checkins_sem_liberacao
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.markdown(

                f"""

                <div class="metric-card">

                    <div class="metric-label">
                        CHECK-INS DO DIA
                    </div>

                    <div class="metric-value">
                        {total_checkins}
                    </div>

                </div>

                """,

                unsafe_allow_html=True
            )


        with col2:

            st.markdown(

                f"""

                <div class="metric-card">

                    <div class="metric-label">
                        LIBERAÇÕES ENCONTRADAS
                    </div>

                    <div class="metric-value">
                        {total_liberacoes}
                    </div>

                </div>

                """,

                unsafe_allow_html=True
            )


        with col3:

            st.markdown(

                f"""

                <div class="metric-card">

                    <div class="metric-label">
                        PENDÊNCIAS
                    </div>

                    <div class="metric-value">
                        {total_pendencias}
                    </div>

                </div>

                """,

                unsafe_allow_html=True
            )


        # ====================================================
        # SUCESSO TOTAL
        # ====================================================

        if not checkins_sem_liberacao:

            st.markdown(

                """

                <div class="success-box">

                    🟢 TODAS AS LIBERAÇÕES DOS
                    CHECK-INS DE HOJE ESTÃO CADASTRADAS!

                </div>

                """,

                unsafe_allow_html=True
            )


        # ====================================================
        # LISTAS
        # ====================================================

        html = """

        <div class="cards-wrapper">

        """


        # ====================================================
        # VERDE
        # ====================================================

        html += """

        <div class="status-card green-card">

            <div class="status-header">

                <div class="status-icon">
                    ✓
                </div>

                <div class="status-title">

                    Check-ins com liberação

                </div>

            </div>

        """


        if checkins_com_liberacao:

            codigos_mostrados = set()

            for checkin in sorted(
                checkins_com_liberacao,
                key=lambda x: x["codigo"]
            ):

                codigo = checkin["codigo"]

                if codigo in codigos_mostrados:
                    continue

                codigos_mostrados.add(
                    codigo
                )

                hospede = (
                    checkin["hospede"]
                    or "Hóspede não identificado"
                )

                html += f"""

                <div class="apt-row">

                    <div class="apt-left">

                        <div class="small-icon green-small">
                            ✓
                        </div>

                        <div class="apt-code">
                            {checkin["codigo_original"]}
                        </div>

                    </div>

                    <div class="apt-description">

                        {hospede}

                    </div>

                </div>

                """

        else:

            html += """

            <div class="empty-card">

                Nenhum check-in com
                liberação encontrado.

            </div>

            """


        html += """

        </div>

        """


        # ====================================================
        # VERMELHO
        # ====================================================

        html += """

        <div class="status-card red-card">

            <div class="status-header">

                <div class="status-icon">
                    !
                </div>

                <div class="status-title">

                    Check-ins sem liberação

                </div>

            </div>

        """


        if checkins_sem_liberacao:

            codigos_mostrados = set()

            for checkin in sorted(
                checkins_sem_liberacao,
                key=lambda x: x["codigo"]
            ):

                codigo = checkin["codigo"]

                if codigo in codigos_mostrados:
                    continue

                codigos_mostrados.add(
                    codigo
                )

                hospede = (
                    checkin["hospede"]
                    or "Hóspede não identificado"
                )

                html += f"""

                <div class="apt-row">

                    <div class="apt-left">

                        <div class="small-icon red-small">
                            !
                        </div>

                        <div class="apt-code">
                            {checkin["codigo_original"]}
                        </div>

                    </div>

                    <div class="apt-description">

                        {hospede}

                    </div>

                </div>

                """

        else:

            html += """

            <div class="empty-card">

                🟢 Nenhuma pendência encontrada.

            </div>

            """


        html += """

        </div>

        </div>

        """


        st.markdown(

            html,

            unsafe_allow_html=True
        )


    except Exception as erro:

        st.error(

            "❌ Ocorreu um erro durante "
            "a conferência."
        )

        st.exception(
            erro
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(

    """

    <div class="footer">

        TAMU • Conferência automática de liberações

    </div>

    """,

    unsafe_allow_html=True
)
