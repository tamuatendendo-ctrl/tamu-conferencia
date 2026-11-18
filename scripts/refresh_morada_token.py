import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

PANEL_URL = "https://check.moradacarioca.com.br/reservas/limpeza/plano_diario"
USERNAME = os.environ["MORADA_USER"]
PASSWORD = os.environ["MORADA_PASSWORD"]
APP_SCRIPT_URL = os.environ["APP_SCRIPT_URL"]
INTEGRATION_KEY = os.environ["TAMU_INTEGRATION_KEY"]


def find_refresh_token(value):
    """Find a refresh_token field in nested browser storage values."""
    if isinstance(value, dict):
        token = value.get("refresh_token")
        if isinstance(token, str) and token.strip():
            return token.strip()
        for nested in value.values():
            found = find_refresh_token(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = find_refresh_token(nested)
            if found:
                return found
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return find_refresh_token(parsed)
    return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(PANEL_URL, wait_until="domcontentloaded", timeout=60000)
        page.locator("input").first.wait_for(state="visible", timeout=30000)

        visible_inputs = []
        for locator in page.locator("input").all():
            try:
                if locator.is_visible():
                    visible_inputs.append(locator)
            except Exception:
                pass

        password_input = page.locator('input[type="password"]').first
        if not visible_inputs or password_input.count() == 0:
            raise RuntimeError("Não foi possível identificar os campos de login.")

        user_input = None
        for locator in visible_inputs:
            try:
                input_type = (locator.get_attribute("type") or "text").lower()
                if input_type not in ("password", "hidden", "submit", "button"):
                    user_input = locator
                    break
            except Exception:
                continue

        if user_input is None:
            raise RuntimeError("Campo de usuário não encontrado.")

        user_input.fill(USERNAME)
        password_input.fill(PASSWORD)

        submit = page.locator('button:visible').filter(
            has_text=re.compile(r"entrar|acessar|login|continuar", re.I)
        ).first
        if submit.count():
            submit.click()
        else:
            password_input.press("Enter")

        # Aguarda a autenticação e a gravação da sessão no armazenamento do navegador.
        page.wait_for_timeout(8000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        storage = page.evaluate("""() => {
            const result = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                result.push(localStorage.getItem(key));
            }
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                result.push(sessionStorage.getItem(key));
            }
            return result;
        }""")

        refresh_token = find_refresh_token(storage)
        if not refresh_token:
            raise RuntimeError(
                "Login concluído, mas nenhum refresh_token foi encontrado "
                "no localStorage/sessionStorage. Nenhum dado foi enviado."
            )

        browser.close()

    response = requests.post(
        APP_SCRIPT_URL,
        json={
            "action": "save_token",
            "api_key": INTEGRATION_KEY,
            "refresh_token": refresh_token,
        },
        timeout=45,
    )
    response.raise_for_status()

    # ContentService do Apps Script pode redirecionar a resposta; valida o JSON final.
    result = response.json()
    if not result.get("sucesso"):
        raise RuntimeError("Apps Script recusou a gravação do token.")

    print("Login realizado e refresh token atualizado no Apps Script.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Falha na atualização automática: {exc}", file=sys.stderr)
        sys.exit(1)
