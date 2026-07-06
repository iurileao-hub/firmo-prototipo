"""Smoke visual do protótipo: dirige o fluxo no navegador e captura as cenas
para o vídeo / evidência da 4.4.1. Requer o runserver no ar em :8010.
"""
import pathlib
import time

from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent / "evidencia"
OUT.mkdir(exist_ok=True)
EXE = "/home/ubuntu/.cache/ms-playwright/chromium-1217/chrome-linux/chrome"
URL = "http://127.0.0.1:8010/"


def clic(pg, nome):
    pg.get_by_role("button", name=nome).last.click()
    pg.wait_for_timeout(450)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE, headless=True)

    # --- cena 1+2: saudação e trilha Formalizar (benefícios) ---
    ctx = b.new_context(viewport={"width": 430, "height": 880})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    time.sleep(0.4)
    pg.screenshot(path=str(OUT / "01-saudacao.png"))
    clic(pg, "Abrir/organizar minha firma")
    clic(pg, "Ainda não tenho CNPJ")
    pg.screenshot(path=str(OUT / "02-beneficios.png"), full_page=True)

    # --- cena 3+4: trilha Gerir (venda -> confirmação -> Firmô ✅) ---
    ctx2 = b.new_context(viewport={"width": 430, "height": 880})
    pg2 = ctx2.new_page()
    pg2.goto(URL, wait_until="networkidle")
    time.sleep(0.3)
    clic(pg2, "Cuidar das contas")
    clic(pg2, "Registrar venda")
    pg2.fill("input[name=texto]", "300")
    pg2.click(".entrada button")
    pg2.wait_for_timeout(450)
    pg2.screenshot(path=str(OUT / "03-confirma.png"), full_page=True)
    clic(pg2, "✅ Confirmar")
    pg2.screenshot(path=str(OUT / "04-firmo-ok.png"), full_page=True)

    # --- cena 5: Comprar Junto (interesse confirmado + quadro da feira) ---
    ctx3 = b.new_context(viewport={"width": 430, "height": 880})
    pg3 = ctx3.new_page()
    pg3.goto(URL, wait_until="networkidle")
    time.sleep(0.3)
    clic(pg3, "Comprar junto com a feira")
    clic(pg3, "Quero participar")
    clic(pg3, "Embalagens")
    pg3.fill("input[name=texto]", "50")
    pg3.click(".entrada button")
    pg3.wait_for_timeout(450)
    clic(pg3, "✅ Confirmar")
    clic(pg3, "Ver quadro da feira")
    pg3.screenshot(path=str(OUT / "05-comprar-junto.png"), full_page=True)

    # --- cena 6: retrato do negócio (venda + despesa -> retrato) ---
    ctx4 = b.new_context(viewport={"width": 430, "height": 880})
    pg4 = ctx4.new_page()
    pg4.goto(URL, wait_until="networkidle")
    time.sleep(0.3)
    clic(pg4, "Cuidar das contas")
    clic(pg4, "Registrar venda")
    pg4.fill("input[name=texto]", "300")
    pg4.click(".entrada button")
    pg4.wait_for_timeout(450)
    clic(pg4, "✅ Confirmar")
    clic(pg4, "Registrar despesa")
    pg4.fill("input[name=texto]", "80")
    pg4.click(".entrada button")
    pg4.wait_for_timeout(450)
    clic(pg4, "✅ Confirmar")
    clic(pg4, "Ver meu retrato")
    pg4.screenshot(path=str(OUT / "06-retrato.png"), full_page=True)

    b.close()

print("cenas capturadas em", OUT)
