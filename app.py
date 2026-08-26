# -*- coding: utf-8 -*-

import os
import json
import re
from datetime import datetime, date

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyTDYZhj_w0S3wpKUAPOHMBWgQ8iXxpjjIOVyYTaJ78veFoJOozROVSQOyPSebZ5JI36g/"
    "exec"
)

ARQUIVO_TOKEN_SUPABASE = "supabase_token.json"


# ============================================================
# CONFIGURAÇÕES DO SUPABASE
# ============================================================

def obter_config_supabase():

    # --------------------------------------------
    # STREAMLIT CLOUD
    # --------------------------------------------

    try:

        if "SUPABASE_URL" in st.secrets:

            return (
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_ANON_KEY"],
                st.secrets["SUPABASE_REFRESH_TOKEN"]
            )

    except Exception:
        pass


    # --------------------------------------------
    # LOCAL
    # --------------------------------------------

    try:

        from config import (
            SUPABASE_URL,
            SUPABASE_ANON_KEY,
            SUPABASE_REFRESH_TOKEN
        )

        return (
            SUPABASE_URL,
            SUPABASE_ANON_KEY,
            SUPABASE_REFRESH_TOKEN
        )

    except Exception:

        raise Exception(
            "As credenciais do Supabase não foram configuradas."
        )


SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_REFRESH_TOKEN = (
    obter_config_supabase()
)


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="TAMU — Conferência de Operações",
    page_icon="🏠",
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
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

#MainMenu,
footer,
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

    margin-bottom: 22px;

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

    min-height: 52px;

    border: none;

    border-radius: 12px;

    background:
        linear-gradient(
            135deg,
            #ff3344,
            #ff5964
        );

    color: white;

    font-size: 15px;

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
   ÁREA DOS 3 CARDS
========================================================== */

.cards-wrapper {

    display: grid;

    grid-template-columns:
        repeat(3, minmax(0, 1fr));

    gap: 18px;

    margin-top: 24px;

    align-items: start;
}


/* ==========================================================
   CARD
========================================================== */

.status-card {

    background: white;

    border-radius: 18px;

    overflow: hidden;

    border: 1px solid #e5e7eb;

    box-shadow:
        0 8px 25px rgba(15, 23, 42, 0.06);
}


/* ==========================================================
   CABEÇALHO
========================================================== */

.status-header {

    display: flex;

    align-items: center;

    gap: 11px;

    padding: 15px 16px;

    border-bottom: 1px solid #edf0f4;
}

.status-icon {

    width: 32px;

    height: 32px;

    min-width: 32px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 17px;

    font-weight: 900;
}

.status-title {

    font-size: 16px;

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
   AZUL
========================================================== */

.blue-card {
    border-color: #cfe0f8;
}

.blue-card .status-header {
    background: #eff6ff;
}

.blue-card .status-icon {
    background: #2563eb;
    color: white;
}

.blue-card .status-title {
    color: #1d4ed8;
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
   LINHA DO APARTAMENTO
========================================================== */

.apt-row {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 10px;

    padding: 9px 14px;

    border-bottom: 1px solid #f0f2f5;

    min-height: 43px;
}

.apt-row:last-child {
    border-bottom: none;
}

.apt-left {

    display: flex;

    align-items: center;

    gap: 9px;

    min-width: 0;
}

.apt-code {

    font-size: 14px;

    font-weight: 800;

    color: #111827;

    white-space: nowrap;
}

.apt-description {
    font-size: 15px;
    font-weight: 800;
    color: #475569;
    white-space: nowrap;
    text-align: right;
}

/* Destaque — cronograma diário */
.green-card .apt-description {
    color: #15803d;
    font-size: 15px;
    font-weight: 800;
}

/* Destaque — última limpeza */
.red-card .apt-description {
    color: #dc2626;
    font-size: 15px;
    font-weight: 800;
}

.small-icon {

    width: 24px;

    height: 24px;

    min-width: 24px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 12px;

    font-weight: 900;
}

.green-small {
    background: #dcfce7;
    color: #15803d;
}

.blue-small {
    background: #dbeafe;
    color: #1d4ed8;
}

.red-small {
    background: #fee2e2;
    color: #dc2626;
}


/* ==========================================================
   CARD VAZIO
========================================================== */

.empty-card {

    padding: 20px;

    text-align: center;

    color: #94a3b8;

    font-size: 13px;
}


/* ==========================================================
   FOOTER
========================================================== */

.footer {

    text-align: center;

    color: #94a3b8;

    font-size: 13px;

    margin-top: 28px;

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

    codigo = codigo.replace(" ", "")

    codigo = re.sub(
        r"[A-Z]+$",
        "",
        codigo
    )

    return codigo


# ============================================================
# GOOGLE SHEETS VIA APPS SCRIPT
# ============================================================

def buscar_checkins():

    resposta = requests.get(
        APP_SCRIPT_URL,
        timeout=60,
        allow_redirects=True
    )

    if resposta.status_code != 200:

        raise Exception(
            "Não foi possível consultar "
            "a aba CHECKINS DO DIA.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"
        )

    try:

        dados = resposta.json()

    except Exception:

        raise Exception(
            "O Apps Script não retornou "
            "um JSON válido."
        )

    if not dados.get("sucesso"):

        raise Exception(
            "O Apps Script retornou um erro:\n\n"
            + str(dados)
        )

    linhas = dados.get(
        "dados",
        []
    )

    checkins = []

    padrao_apartamento = re.compile(
        r"^\d{6}[A-Z]?$",
        re.IGNORECASE
    )

    for numero_linha, linha in enumerate(
        linhas,
        start=1
    ):

        if not isinstance(
            linha,
            list
        ):
            continue

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

            # Pela estrutura atual da aba:
            #
            # apartamento | hóspede | data
            #
            # Portanto o hóspede está na
            # coluna imediatamente seguinte.

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

                    # Não considerar data como hóspede
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
# SUPABASE — SALVAR TOKEN
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

    try:

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

    except Exception:
        # No Streamlit Cloud o arquivo pode
        # não ser persistente. Nesse caso
        # continuamos usando a sessão atual.
        pass


# ============================================================
# SUPABASE — OBTER REFRESH TOKEN
# ============================================================

def obter_refresh_token_supabase():

    # Primeiro tenta o token salvo localmente.

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

            refresh_token = (
                dados.get(
                    "refresh_token"
                )
            )

            if refresh_token:

                return refresh_token

        except Exception:
            pass


    # No Streamlit Cloud usa Secrets.

    try:

        if (
            "SUPABASE_REFRESH_TOKEN"
            in st.secrets
        ):

            return st.secrets[
                "SUPABASE_REFRESH_TOKEN"
            ]

    except Exception:
        pass


    return SUPABASE_REFRESH_TOKEN


# ============================================================
# SUPABASE — RENOVAR TOKEN
# ============================================================

def renovar_token_supabase():

    refresh_token = (
        obter_refresh_token_supabase()
    )

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
            f"HTTP {resposta.status_code} "
            f"{resposta.text}"
        )

    dados = resposta.json()

    access_token = (
        dados.get(
            "access_token"
        )
    )

    novo_refresh_token = (
        dados.get(
            "refresh_token"
        )
    )

    expires_in = (
        dados.get(
            "expires_in"
        )
    )

    if not access_token:

        raise Exception(
            "Supabase não retornou "
            "um access token."
        )

    salvar_token_supabase(
        access_token,
        novo_refresh_token or refresh_token,
        expires_in
    )

    # Mantém o token atualizado na sessão
    # atual do Streamlit.

    st.session_state[
        "supabase_access_token"
    ] = access_token

    st.session_state[
        "supabase_refresh_token"
    ] = (
        novo_refresh_token
        or refresh_token
    )

    return access_token


# ============================================================
# SUPABASE — ACCESS TOKEN
# ============================================================

def obter_access_token_supabase():

    if (
        "supabase_access_token"
        in st.session_state
    ):

        return st.session_state[
            "supabase_access_token"
        ]


    # Tenta arquivo local

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

            access_token = (
                dados.get(
                    "access_token"
                )
            )

            if access_token:

                st.session_state[
                    "supabase_access_token"
                ] = access_token

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
# LIMPEZAS DE HOJE
# ============================================================

def buscar_limpezas_hoje():

    hoje = date.today().strftime(
        "%Y-%m-%d"
    )

    endpoint = (
        f"{SUPABASE_URL}"
        f"/rest/v1/"
        f"cleaning_schedules"
    )

    parametros = {

        "select": (
            "id,"
            "reservation_id,"
            "property_id,"
            "priority,"
            "assigned_extra_id,"
            "assigned_equipe_id,"
            "status,"
            "scheduled_date,"
            "completed_at,"
            "cancelled_at"
        ),

        "scheduled_date":
            f"eq.{hoje}",

        "status":
            "eq.active",

        "order":
            "priority.asc"
    }

    resposta = supabase_get(
        endpoint,
        parametros
    )

    if resposta.status_code != 200:

        raise Exception(
            "Falha ao consultar "
            "cleaning_schedules.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"
        )

    return resposta.json()


# ============================================================
# PROPERTIES
# ============================================================

def buscar_properties(
    property_ids
):

    if not property_ids:
        return {}

    lista_ids = ",".join(
        property_ids
    )

    endpoint = (
        f"{SUPABASE_URL}"
        f"/rest/v1/"
        f"properties"
    )

    parametros = {

        "select": (
            "id,"
            "code,"
            "street,"
            "number,"
            "complement"
        ),

        "id":
            f"in.({lista_ids})"
    }

    resposta = supabase_get(
        endpoint,
        parametros
    )

    if resposta.status_code != 200:

        raise Exception(
            "Falha ao consultar "
            "properties.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"
        )

    mapa = {}

    for property_data in resposta.json():

        property_id = (
            property_data.get("id")
        )

        codigo_original = str(
            property_data.get(
                "code",
                ""
            )
        ).strip()

        codigo = normalizar_codigo(
            codigo_original
        )

        mapa[property_id] = {

            "codigo_original":
                codigo_original,

            "codigo":
                codigo,

            "endereco": (
                f"{property_data.get('street', '')}, "
                f"{property_data.get('number', '')} "
                f"{property_data.get('complement', '')}"
            ).strip()
        }

    return mapa


def buscar_todas_properties():

    endpoint = (
        f"{SUPABASE_URL}"
        f"/rest/v1/"
        f"properties"
    )

    parametros = {

        "select": (
            "id,"
            "code,"
            "street,"
            "number,"
            "complement"
        )
    }

    resposta = supabase_get(
        endpoint,
        parametros
    )

    if resposta.status_code != 200:

        raise Exception(
            "Falha ao consultar "
            "properties.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"
        )

    mapa = {}

    for property_data in resposta.json():

        codigo_original = str(
            property_data.get(
                "code",
                ""
            )
        ).strip()

        codigo = normalizar_codigo(
            codigo_original
        )

        if not codigo:
            continue

        mapa[
            property_data["id"]
        ] = {

            "codigo_original":
                codigo_original,

            "codigo":
                codigo,

            "endereco": (
                f"{property_data.get('street', '')}, "
                f"{property_data.get('number', '')} "
                f"{property_data.get('complement', '')}"
            ).strip()
        }

    return mapa


# ============================================================
# HISTÓRICO
# ============================================================

def buscar_historico_limpezas(
    property_ids
):

    if not property_ids:
        return []

    lista_ids = ",".join(
        property_ids
    )

    endpoint = (
        f"{SUPABASE_URL}"
        f"/rest/v1/"
        f"cleaning_schedules"
    )

    parametros = {

        "select": (
            "id,"
            "property_id,"
            "status,"
            "scheduled_date,"
            "completed_at,"
            "cancelled_at,"
            "started_at"
        ),

        "property_id":
            f"in.({lista_ids})",

        "order":
            "scheduled_date.desc"
    }

    resposta = supabase_get(
        endpoint,
        parametros
    )

    if resposta.status_code != 200:

        raise Exception(
            "Falha ao consultar "
            "histórico de limpezas.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"
        )

    return resposta.json()


def extrair_data_limpeza(
    registro
):

    completed_at = registro.get(
        "completed_at"
    )

    scheduled_date = registro.get(
        "scheduled_date"
    )

    started_at = registro.get(
        "started_at"
    )

    if completed_at:

        try:

            return datetime.fromisoformat(
                completed_at.replace(
                    "Z",
                    "+00:00"
                )
            ).date()

        except Exception:
            pass

    if started_at and scheduled_date:

        try:

            return datetime.strptime(
                scheduled_date,
                "%Y-%m-%d"
            ).date()

        except Exception:
            pass

    if scheduled_date:

        try:

            return datetime.strptime(
                scheduled_date,
                "%Y-%m-%d"
            ).date()

        except Exception:
            pass

    return None


def montar_ultima_limpeza(
    historico,
    properties
):

    ultima_limpeza = {}

    hoje = date.today()

    for registro in historico:

        if registro.get(
            "cancelled_at"
        ):
            continue

        property_id = (
            registro.get(
                "property_id"
            )
        )

        property_data = (
            properties.get(
                property_id
            )
        )

        if not property_data:
            continue

        codigo = (
            property_data["codigo"]
        )

        if not codigo:
            continue

        data_limpeza = (
            extrair_data_limpeza(
                registro
            )
        )

        if data_limpeza is None:
            continue

        if data_limpeza > hoje:
            continue

        if (
            codigo not in ultima_limpeza
            or
            data_limpeza
            > ultima_limpeza[codigo]
        ):

            ultima_limpeza[codigo] = (
                data_limpeza
            )

    return ultima_limpeza


# ============================================================
# CONFERÊNCIA
# ============================================================

def executar_conferencia():

    # --------------------------------------------------------
    # CHECK-INS
    # Agora vêm exclusivamente do Apps Script.
    # --------------------------------------------------------

    checkins = (
        buscar_checkins()
    )

    # --------------------------------------------------------
    # LIMPEZAS
    # --------------------------------------------------------

    limpezas_hoje = (
        buscar_limpezas_hoje()
    )

    property_ids_hoje = []

    for limpeza in limpezas_hoje:

        property_id = (
            limpeza.get(
                "property_id"
            )
        )

        if (
            property_id
            and
            property_id not in property_ids_hoje
        ):

            property_ids_hoje.append(
                property_id
            )

    properties_hoje = (
        buscar_properties(
            property_ids_hoje
        )
    )

    codigos_limpeza_hoje = set()

    for limpeza in limpezas_hoje:

        property_id = (
            limpeza.get(
                "property_id"
            )
        )

        property_data = (
            properties_hoje.get(
                property_id
            )
        )

        if not property_data:
            continue

        codigo = (
            property_data["codigo"]
        )

        if codigo:

            codigos_limpeza_hoje.add(
                codigo
            )

    # --------------------------------------------------------
    # COMPARAÇÃO
    # --------------------------------------------------------

    codigos_checkin = set(
        checkin["codigo"]
        for checkin in checkins
    )

    checkins_com_limpeza = [
        checkin
        for checkin in checkins
        if checkin["codigo"]
        in codigos_limpeza_hoje
    ]

    limpezas_sem_checkin = (
        codigos_limpeza_hoje
        -
        codigos_checkin
    )

    checkins_sem_limpeza = [
        checkin
        for checkin in checkins
        if checkin["codigo"]
        not in codigos_limpeza_hoje
    ]

    codigos_sem_limpeza = (
        codigos_checkin
        -
        codigos_limpeza_hoje
    )

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    todas_properties = {}

    if codigos_sem_limpeza:

        todas_properties = (
            buscar_todas_properties()
        )

    property_ids_historico = []

    for property_id, property_data in (
        todas_properties.items()
    ):

        if (
            property_data["codigo"]
            in codigos_sem_limpeza
        ):

            property_ids_historico.append(
                property_id
            )

    historico = []

    if property_ids_historico:

        historico = (
            buscar_historico_limpezas(
                property_ids_historico
            )
        )

    ultima_limpeza = (
        montar_ultima_limpeza(
            historico,
            todas_properties
        )
    )

    return {

        "checkins":
            checkins,

        "checkins_com_limpeza":
            checkins_com_limpeza,

        "limpezas_sem_checkin":
            limpezas_sem_checkin,

        "checkins_sem_limpeza":
            checkins_sem_limpeza,

        "ultima_limpeza":
            ultima_limpeza,

        "cronograma_hoje":
            codigos_limpeza_hoje
    }


# ============================================================
# HERO
# ============================================================

hoje = date.today()

hero_html = f"""
<div class="hero">

    <div class="hero-title">
        TAMU — Conferência de Operações
    </div>

    <div class="hero-subtitle">
        Conferência automática de check-ins × limpezas
    </div>

    <div class="hero-date">
        📅 {hoje.strftime("%d/%m/%Y")}
    </div>

</div>
"""

st.html(hero_html)


# ============================================================
# BOTÃO
# ============================================================

col_esq, col_botao, col_dir = st.columns(
    [1, 1.2, 1]
)

with col_botao:

    verificar = st.button(
        "🔄  FAZER VERIFICAÇÃO",
        use_container_width=True
    )


# ============================================================
# EXECUTAR
# ============================================================

if verificar:

    with st.spinner(
        "Realizando conferência..."
    ):

        try:

            resultado = (
                executar_conferencia()
            )

            st.session_state[
                "resultado_conferencia"
            ] = resultado

            st.session_state[
                "ultima_verificacao"
            ] = datetime.now()

        except Exception as erro:

            st.error(
                f"Erro durante a conferência:\n\n{erro}"
            )

            st.stop()


# ============================================================
# RESULTADO INICIAL
# ============================================================

if (
    "resultado_conferencia"
    not in st.session_state
):

    inicial_html = """
    <div style="
        background:white;
        border:1px solid #e5e7eb;
        border-radius:18px;
        padding:38px 25px;
        text-align:center;
        margin-top:24px;
    ">

        <div style="
            font-size:42px;
            margin-bottom:10px;
        ">
            🧹
        </div>

        <div style="
            font-size:21px;
            font-weight:800;
            color:#111827;
        ">
            Pronto para realizar a conferência
        </div>

        <div style="
            font-size:14px;
            color:#64748b;
            margin-top:8px;
        ">
            Clique em "FAZER VERIFICAÇÃO" para consultar
            os check-ins e limpezas do dia.
        </div>

    </div>
    """

    st.html(inicial_html)


# ============================================================
# RESULTADO
# ============================================================

else:

    resultado = (
        st.session_state[
            "resultado_conferencia"
        ]
    )

    checkins_com_limpeza = (
        resultado[
            "checkins_com_limpeza"
        ]
    )

    limpezas_sem_checkin = (
        resultado[
            "limpezas_sem_checkin"
        ]
    )

    checkins_sem_limpeza = (
        resultado[
            "checkins_sem_limpeza"
        ]
    )

    ultima_limpeza = (
        resultado[
            "ultima_limpeza"
        ]
    )

    cronograma_hoje = (
        resultado[
            "cronograma_hoje"
        ]
    )


    # ========================================================
    # 3 CARDS
    # ========================================================

    html = """
    <div class="cards-wrapper">


        <!-- VERDE -->

        <div class="status-card green-card">

            <div class="status-header">

                <div class="status-icon">
                    ✓
                </div>

                <div class="status-title">
                    Check-in + limpeza hoje
                </div>

            </div>
    """


    # ========================================================
    # CARD VERDE
    # ========================================================

    if checkins_com_limpeza:

        apartamentos_mostrados = set()

        for checkin in checkins_com_limpeza:

            codigo = checkin["codigo"]

            if codigo in apartamentos_mostrados:
                continue

            apartamentos_mostrados.add(
                codigo
            )

            codigo_exibicao = (
                checkin["codigo_original"]
            )

            if codigo in cronograma_hoje:

                descricao = (
                    "Está no cronograma diário"
                )

            else:

                descricao = (
                    "Fora do cronograma diário"
                )

            html += f"""
            <div class="apt-row">

                <div class="apt-left">

                    <div class="small-icon green-small">
                        ✓
                    </div>

                    <div class="apt-code">
                        {codigo_exibicao}
                    </div>

                </div>

                <div class="apt-description">
                    {descricao}
                </div>

            </div>
            """

    else:

        html += """
        <div class="empty-card">
            Nenhum apartamento
        </div>
        """


    html += """
        </div>


        <!-- AZUL -->

        <div class="status-card blue-card">

            <div class="status-header">

                <div class="status-icon">
                    ✓
                </div>

                <div class="status-title">
                    Limpezas + sem check-in
                </div>

            </div>
    """


    # ========================================================
    # CARD AZUL
    # ========================================================

    if limpezas_sem_checkin:

        for codigo in sorted(
            limpezas_sem_checkin
        ):

            html += f"""
            <div class="apt-row">

                <div class="apt-left">

                    <div class="small-icon blue-small">
                        ✓
                    </div>

                    <div class="apt-code">
                        {codigo}
                    </div>

                </div>

            </div>
            """

    else:

        html += """
        <div class="empty-card">
            Nenhum apartamento
        </div>
        """


    html += """
        </div>


        <!-- VERMELHO -->

        <div class="status-card red-card">

            <div class="status-header">

                <div class="status-icon">
                    !
                </div>

                <div class="status-title">
                    Check-in + sem limpeza hoje
                </div>

            </div>
    """


    # ========================================================
    # CARD VERMELHO
    # ========================================================

    if checkins_sem_limpeza:

        apartamentos_mostrados = set()

        for checkin in checkins_sem_limpeza:

            codigo = checkin["codigo"]

            if codigo in apartamentos_mostrados:
                continue

            apartamentos_mostrados.add(
                codigo
            )

            codigo_exibicao = (
                checkin["codigo_original"]
            )

            ultima = (
                ultima_limpeza.get(
                    codigo
                )
            )

            if ultima:

                data_texto = (
                    "Última limpeza: "
                    +
                    ultima.strftime(
                        "%d/%m/%Y"
                    )
                )

            else:

                data_texto = (
                    "Última limpeza: "
                    "NUNCA ENCONTRADA"
                )

            html += f"""
            <div class="apt-row">

                <div class="apt-left">

                    <div class="small-icon red-small">
                        !
                    </div>

                    <div class="apt-code">
                        {codigo_exibicao}
                    </div>

                </div>

                <div class="apt-description">
                    {data_texto}
                </div>

            </div>
            """

    else:

        html += """
        <div class="empty-card">
            Nenhum apartamento
        </div>
        """


    html += """
        </div>

    </div>
    """


    st.html(html)


    # ========================================================
    # FOOTER
    # ========================================================

    if (
        "ultima_verificacao"
        in st.session_state
    ):

        horario = (
            st.session_state[
                "ultima_verificacao"
            ].strftime(
                "%H:%M:%S"
            )
        )

        footer_html = f"""
        <div class="footer">

            Última verificação: {horario}

            &nbsp; • &nbsp;

            TAMU — Conferência de Operações

        </div>
        """

        st.html(footer_html)
