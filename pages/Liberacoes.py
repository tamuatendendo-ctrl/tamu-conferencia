import os
import json
import re
from datetime import datetime, date

import requests
import gspread

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    SUPABASE_REFRESH_TOKEN
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_CREDENCIAL = "google_oauth.json"
ARQUIVO_TOKEN_GOOGLE = "google_token.json"
ARQUIVO_TOKEN_SUPABASE = "supabase_token.json"

SPREADSHEET_ID = "1DSrif82ExLPDuloafYUk2F8xXKvf0mAkMSDXqfQ3EOs"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]


# ============================================================
# NORMALIZAR CÓDIGO DO APARTAMENTO
# ============================================================

def normalizar_codigo(codigo):

    if codigo is None:
        return ""

    codigo = str(codigo).strip().upper()
    codigo = codigo.replace(" ", "")

    # Exemplos:
    # 161095
    # 161095A
    # 161095B
    # 161095C
    #
    # Todos serão tratados como:
    # 161095

    codigo = re.sub(r"[A-Z]+$", "", codigo)

    return codigo


# ============================================================
# AUTENTICAÇÃO GOOGLE
# ============================================================

def autenticar_google():

    credentials = None

    if os.path.exists(ARQUIVO_TOKEN_GOOGLE):

        credentials = Credentials.from_authorized_user_file(
            ARQUIVO_TOKEN_GOOGLE,
            SCOPES
        )

    if credentials:

        if credentials.expired and credentials.refresh_token:

            credentials.refresh(Request())

    if not credentials or not credentials.valid:

        print(
            "Será necessário autorizar o Google novamente."
        )

        print()

        flow = InstalledAppFlow.from_client_secrets_file(
            ARQUIVO_CREDENCIAL,
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )

        with open(
            ARQUIVO_TOKEN_GOOGLE,
            "w",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(
                credentials.to_json()
            )

    return credentials


# ============================================================
# SALVAR TOKEN SUPABASE
# ============================================================

def salvar_token_supabase(
    access_token,
    refresh_token=None,
    expires_in=None
):

    dados = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "saved_at": datetime.now().isoformat()
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


# ============================================================
# RENOVAR TOKEN SUPABASE
# ============================================================

def renovar_token_supabase():

    print(
        "Renovando sessão do Supabase..."
    )

    url = (
        f"{SUPABASE_URL}/auth/v1/token"
        "?grant_type=refresh_token"
    )

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "refresh_token": SUPABASE_REFRESH_TOKEN
    }

    resposta = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    if resposta.status_code != 200:

        print()
        print(
            "ERRO AO RENOVAR TOKEN DO SUPABASE"
        )

        print(
            f"STATUS HTTP: {resposta.status_code}"
        )

        print(
            resposta.text
        )

        raise Exception(
            "Não foi possível renovar "
            "o token do Supabase."
        )

    dados = resposta.json()

    access_token = dados.get(
        "access_token"
    )

    refresh_token = dados.get(
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

    salvar_token_supabase(
        access_token,
        refresh_token,
        expires_in
    )

    print(
        "Sessão do Supabase renovada com sucesso."
    )

    print()

    return access_token


# ============================================================
# OBTER TOKEN SUPABASE
# ============================================================

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

                print(
                    "Usando sessão Supabase salva."
                )

                return access_token

        except Exception:

            pass

    return renovar_token_supabase()


# ============================================================
# REQUISIÇÃO GET SUPABASE
# ============================================================

def supabase_get(
    endpoint,
    params=None
):

    access_token = (
        obter_access_token_supabase()
    )

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization":
            f"Bearer {access_token}"
    }

    resposta = requests.get(
        endpoint,
        params=params,
        headers=headers,
        timeout=30
    )

    # Se o token expirou,
    # renova e tenta novamente.

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
            or
            "expired" in mensagem
            or
            "token" in mensagem
        ):

            print(
                "Token expirado. Renovando..."
            )

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
# BUSCAR CHECK-INS NA ABA "CHECKINS DO DIA"
# ============================================================

def buscar_checkins():

    print("=" * 70)
    print("1. BUSCANDO CHECK-INS NO GOOGLE SHEETS")
    print("=" * 70)

    print()

    credentials = autenticar_google()

    print(
        "Google autenticado com sucesso!"
    )

    print()

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open_by_key(
        SPREADSHEET_ID
    )

    print(
        f"Planilha encontrada: "
        f"{spreadsheet.title}"
    )

    # ========================================================
    # ABA CORRETA
    # ========================================================

    worksheet = spreadsheet.worksheet(
        "CHECKINS DO DIA"
    )

    print(
        f"Aba encontrada: "
        f"{worksheet.title}"
    )

    print()

    dados = worksheet.get_all_values()

    print(
        f"Linhas encontradas: "
        f"{len(dados)}"
    )

    print()

    # ========================================================
    # A ABA "CHECKINS DO DIA" NÃO POSSUI UM CABEÇALHO
    # PADRÃO.
    #
    # Ela possui os apartamentos organizados em blocos,
    # como:
    #
    # 161117 | Maria Eduarda Silva | 22/08
    # 161095C | Viktoriia | 22/08/2026
    #
    # Portanto procuramos diretamente códigos de apartamento.
    # ========================================================

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

            valor = str(valor).strip()

            if not valor:
                continue

            # ------------------------------------------------
            # Verifica se a célula é um código de apartamento
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Nome do hóspede fica imediatamente à direita
            # ------------------------------------------------

            hospede = ""

            if (
                indice_coluna + 1
                <
                len(linha)
            ):

                possivel_hospede = str(
                    linha[
                        indice_coluna + 1
                    ]
                ).strip()

                if possivel_hospede:

                    eh_data = False

                    formatos_data = [
                        "%d/%m",
                        "%d/%m/%Y",
                        "%d/%m/%y"
                    ]

                    for formato in formatos_data:

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

            # ------------------------------------------------
            # Evita duplicação do mesmo registro
            # ------------------------------------------------

            registro_existente = False

            for registro in checkins:

                if (
                    registro["codigo_original"]
                    ==
                    codigo_original
                    and
                    registro["hospede"]
                    ==
                    hospede
                    and
                    registro["linha"]
                    ==
                    numero_linha
                ):

                    registro_existente = True
                    break

            if registro_existente:
                continue

            checkins.append(
                {
                    "codigo_original":
                        codigo_original,

                    "codigo":
                        codigo,

                    "hospede":
                        hospede,

                    "linha":
                        numero_linha
                }
            )

    # ========================================================
    # RESULTADO
    # ========================================================

    print(
        f"Check-ins encontrados: "
        f"{len(checkins)}"
    )

    print()

    for checkin in checkins:

        print(
            f"  {checkin['codigo_original']} | "
            f"{checkin['hospede']}"
        )

    print()

    return checkins


# ============================================================
# BUSCAR LIMPEZAS DE HOJE
# ============================================================

def buscar_limpezas_hoje():

    hoje = date.today().strftime(
        "%Y-%m-%d"
    )

    print("=" * 70)
    print(
        "2. BUSCANDO LIMPEZAS DE HOJE NO SUPABASE"
    )
    print("=" * 70)

    print()

    endpoint = (
        f"{SUPABASE_URL}/rest/v1/"
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

    print(
        f"STATUS HTTP: "
        f"{resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            resposta.text
        )

        raise Exception(
            "Falha ao consultar "
            "cleaning_schedules."
        )

    limpezas = resposta.json()

    print(
        f"Limpezas encontradas: "
        f"{len(limpezas)}"
    )

    print()

    return limpezas


# ============================================================
# BUSCAR PROPERTIES
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
        f"{SUPABASE_URL}/rest/v1/"
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

    print(
        f"STATUS HTTP: "
        f"{resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            resposta.text
        )

        raise Exception(
            "Falha ao consultar "
            "properties."
        )

    properties = resposta.json()

    mapa = {}

    for property_data in properties:

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


# ============================================================
# BUSCAR TODAS AS PROPERTIES
# ============================================================

def buscar_todas_properties():

    print("=" * 70)
    print(
        "3. LOCALIZANDO UNIDADES PARA "
        "CONSULTA DO HISTÓRICO"
    )
    print("=" * 70)

    print()

    endpoint = (
        f"{SUPABASE_URL}/rest/v1/"
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

    print(
        f"STATUS HTTP: "
        f"{resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            resposta.text
        )

        raise Exception(
            "Falha ao consultar "
            "properties."
        )

    properties = resposta.json()

    mapa = {}

    for property_data in properties:

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

    print(
        f"Properties encontradas: "
        f"{len(mapa)}"
    )

    print()

    return mapa


# ============================================================
# BUSCAR HISTÓRICO DE LIMPEZAS
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
        f"{SUPABASE_URL}/rest/v1/"
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

    print(
        f"STATUS HTTP: "
        f"{resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            resposta.text
        )

        raise Exception(
            "Falha ao consultar "
            "histórico de limpezas."
        )

    historico = resposta.json()

    print(
        f"Registros históricos encontrados: "
        f"{len(historico)}"
    )

    print()

    return historico


# ============================================================
# EXTRAIR DATA DA LIMPEZA
# ============================================================

def extrair_data_limpeza(
    registro
):

    completed_at = (
        registro.get(
            "completed_at"
        )
    )

    scheduled_date = (
        registro.get(
            "scheduled_date"
        )
    )

    started_at = (
        registro.get(
            "started_at"
        )
    )

    # Primeiro tenta completed_at

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

    # Depois tenta started_at

    if started_at and scheduled_date:

        try:

            return datetime.strptime(
                scheduled_date,
                "%Y-%m-%d"
            ).date()

        except Exception:

            pass

    # Finalmente scheduled_date

    if scheduled_date:

        try:

            return datetime.strptime(
                scheduled_date,
                "%Y-%m-%d"
            ).date()

        except Exception:

            pass

    return None


# ============================================================
# MAPEAR ÚLTIMA LIMPEZA POR UNIDADE
# ============================================================

def montar_ultima_limpeza(
    historico,
    properties
):

    ultima_limpeza = {}

    hoje = date.today()

    for registro in historico:

        # Limpeza cancelada não conta.

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
            data_limpeza >
            ultima_limpeza[codigo]
        ):

            ultima_limpeza[codigo] = (
                data_limpeza
            )

    return ultima_limpeza


# ============================================================
# CONFERÊNCIA
# ============================================================

def realizar_conferencia(
    checkins,
    limpezas_hoje,
    properties_hoje,
    todas_properties,
    ultima_limpeza
):

    # --------------------------------------------------------
    # MAPA DAS LIMPEZAS DE HOJE
    # --------------------------------------------------------

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
    # MAPA DOS CHECK-INS
    # --------------------------------------------------------

    codigos_checkin = set(
        checkin["codigo"]
        for checkin in checkins
    )

    # --------------------------------------------------------
    # GRUPO 1:
    # CHECK-IN + LIMPEZA
    # --------------------------------------------------------

    checkins_com_limpeza = [
        checkin
        for checkin in checkins
        if checkin["codigo"]
        in codigos_limpeza_hoje
    ]

    # --------------------------------------------------------
    # GRUPO 2:
    # LIMPEZA + SEM CHECK-IN
    # --------------------------------------------------------

    limpezas_sem_checkin = (
        codigos_limpeza_hoje
        -
        codigos_checkin
    )

    # --------------------------------------------------------
    # GRUPO 3:
    # CHECK-IN + SEM LIMPEZA
    # --------------------------------------------------------

    checkins_sem_limpeza = [
        checkin
        for checkin in checkins
        if checkin["codigo"]
        not in codigos_limpeza_hoje
    ]

    # ========================================================
    # RELATÓRIO
    # ========================================================

    hoje_formatado = date.today().strftime(
        "%d/%m/%Y"
    )

    print()
    print("=" * 70)
    print(
        f"      CONFERÊNCIA — {hoje_formatado}"
    )
    print("=" * 70)
    print()

    # ========================================================
    # RESUMO
    # ========================================================

    apartamentos_checkin = set(
        checkin["codigo"]
        for checkin in checkins
    )

    print("RESUMO")
    print("-" * 70)

    print(
        f"Reservas/check-ins: "
        f"{len(checkins)}"
    )

    print(
        f"Apartamentos com check-in: "
        f"{len(apartamentos_checkin)}"
    )

    print(
        f"Apartamentos com limpeza hoje: "
        f"{len(codigos_limpeza_hoje)}"
    )

    print(
        f"Check-ins + limpeza: "
        f"{len(set(c['codigo'] for c in checkins_com_limpeza))}"
    )

    print(
        f"Check-ins sem limpeza: "
        f"{len(set(c['codigo'] for c in checkins_sem_limpeza))}"
    )

    print(
        f"Limpezas sem check-in: "
        f"{len(limpezas_sem_checkin)}"
    )

    print()

    # ========================================================
    # 1 — CHECK-IN + LIMPEZA
    # ========================================================

    print("=" * 70)
    print("1. 🟢 CHECK-IN + LIMPEZA HOJE")
    print("=" * 70)

    if checkins_com_limpeza:

        apartamentos_mostrados = set()

        for checkin in checkins_com_limpeza:

            codigo = checkin["codigo"]

            if codigo in apartamentos_mostrados:
                continue

            apartamentos_mostrados.add(
                codigo
            )

            print(
                f"  OK | "
                f"{checkin['codigo_original']} | "
                f"{checkin['hospede']}"
            )

            print(
                "       Cronograma de limpeza: SIM"
            )

    else:

        print(
            "  Nenhum apartamento."
        )

    print()

    # ========================================================
    # 2 — LIMPEZA + SEM CHECK-IN
    # ========================================================

    print("=" * 70)
    print("2. 🔵 LIMPEZA HOJE + SEM CHECK-IN")
    print("=" * 70)

    if limpezas_sem_checkin:

        for codigo in sorted(
            limpezas_sem_checkin
        ):

            print(
                f"  OK | {codigo}"
            )

    else:

        print(
            "  Nenhuma."
        )

    print()

    # ========================================================
    # 3 — CHECK-IN + SEM LIMPEZA
    # ========================================================

    print("=" * 70)
    print(
        "3. 🟡 CHECK-IN + SEM LIMPEZA HOJE"
    )
    print("=" * 70)

    if checkins_sem_limpeza:

        apartamentos_mostrados = set()

        for checkin in checkins_sem_limpeza:

            codigo = checkin["codigo"]

            if codigo in apartamentos_mostrados:
                continue

            apartamentos_mostrados.add(
                codigo
            )

            print()

            print(
                f"  ⚠️ APARTAMENTO: "
                f"{checkin['codigo_original']}"
            )

            print(
                f"     Hóspede: "
                f"{checkin['hospede']}"
            )

            print(
                "     Check-in: HOJE"
            )

            print(
                "     Limpeza hoje: NÃO"
            )

            print(
                "     Cronograma de limpeza hoje: NÃO"
            )

            ultima = (
                ultima_limpeza.get(
                    codigo
                )
            )

            if ultima:

                print(
                    "     Última limpeza: "
                    f"{ultima.strftime('%d/%m/%Y')}"
                )

            else:

                print(
                    "     Última limpeza: "
                    "NUNCA ENCONTRADA"
                )

    else:

        print(
            "  Nenhum apartamento."
        )

    print()

    # ========================================================
    # FINAL
    # ========================================================

    print("=" * 70)
    print("CONFERÊNCIA FINALIZADA")
    print("=" * 70)
    print()

    return {
        "checkins_com_limpeza":
            checkins_com_limpeza,

        "limpezas_sem_checkin":
            limpezas_sem_checkin,

        "checkins_sem_limpeza":
            checkins_sem_limpeza
    }


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":

    try:

        # ----------------------------------------------------
        # 1. GOOGLE SHEETS
        # ----------------------------------------------------

        checkins = (
            buscar_checkins()
        )

        # ----------------------------------------------------
        # 2. LIMPEZAS DE HOJE
        # ----------------------------------------------------

        limpezas_hoje = (
            buscar_limpezas_hoje()
        )

        # ----------------------------------------------------
        # 3. PROPERTIES DAS LIMPEZAS DE HOJE
        # ----------------------------------------------------

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
                property_id
                not in property_ids_hoje
            ):

                property_ids_hoje.append(
                    property_id
                )

        properties_hoje = (
            buscar_properties(
                property_ids_hoje
            )
        )

        # ----------------------------------------------------
        # 4. PROPERTIES GERAIS
        # Necessárias para consultar histórico.
        # ----------------------------------------------------

        todas_properties = (
            buscar_todas_properties()
        )

        # ----------------------------------------------------
        # 5. APARTAMENTOS SEM LIMPEZA HOJE
        # ----------------------------------------------------

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

            if property_data:

                codigo = (
                    property_data["codigo"]
                )

                if codigo:

                    codigos_limpeza_hoje.add(
                        codigo
                    )

        codigos_checkin = set(
            checkin["codigo"]
            for checkin in checkins
        )

        codigos_sem_limpeza = (
            codigos_checkin
            -
            codigos_limpeza_hoje
        )

        # ----------------------------------------------------
        # 6. LOCALIZAR PROPERTY IDS
        # DOS APARTAMENTOS SEM LIMPEZA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 7. BUSCAR HISTÓRICO
        # ----------------------------------------------------

        historico = []

        if property_ids_historico:

            print("=" * 70)
            print(
                "4. BUSCANDO HISTÓRICO DAS "
                "UNIDADES SEM LIMPEZA HOJE"
            )
            print("=" * 70)

            print()

            historico = (
                buscar_historico_limpezas(
                    property_ids_historico
                )
            )

        # ----------------------------------------------------
        # 8. MAPA DA ÚLTIMA LIMPEZA
        # ----------------------------------------------------

        ultima_limpeza = (
            montar_ultima_limpeza(
                historico,
                todas_properties
            )
        )

        # ----------------------------------------------------
        # 9. CONFERÊNCIA FINAL
        # ----------------------------------------------------

        realizar_conferencia(
            checkins,
            limpezas_hoje,
            properties_hoje,
            todas_properties,
            ultima_limpeza
        )

    except Exception as erro:

        print()
        print("=" * 70)
        print("ERRO")
        print("=" * 70)
        print()

        print(
            str(erro)
        )

        print()
