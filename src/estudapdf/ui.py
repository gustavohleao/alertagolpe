"""Elementos visuais locais. Dados dinâmicos são escapados antes de virar HTML."""

from base64 import b64encode
from html import escape

import streamlit as st

_PATHS = {
    "book": '<path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1Z"/><path d="M12 6v14"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    "spark": '<path d="m12 3 2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8Z"/><path d="m20 2 .6 1.4L22 4l-1.4.6L20 6l-.6-1.4L18 4l1.4-.6Z"/>',
    "search": '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/>',
    "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
    "layers": '<path d="m12 3 10 5-10 5L2 8Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
    "quote": '<path d="M10 6H4v7h5c0 3-2 5-5 5M21 6h-6v7h5c0 3-2 5-5 5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
}


def icon(name: str, size: int = 20) -> str:
    # st.html restringe SVG inline. A máscara local usa apenas formas estáticas
    # conhecidas e herda a cor, sem buscar arquivos ou fontes na rede.
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>'
    data = b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<span class="ui-icon" style="width:{size}px;height:{size}px;mask-image:url(data:image/svg+xml;base64,{data});-webkit-mask-image:url(data:image/svg+xml;base64,{data})" aria-hidden="true"></span>'


def safe(value: object) -> str:
    return escape(str(value), quote=True)


def html(markup: str) -> None:
    """Somente composição controlada; usar safe() em qualquer dado externo."""
    st.html(markup)


def section_heading(number: str, title: str, subtitle: str = "") -> None:
    html(f'<div class="section-heading"><span class="step-number">{safe(number)}</span><div><h2>{safe(title)}</h2>{f"<p>{safe(subtitle)}</p>" if subtitle else ""}</div></div>')


def brand() -> None:
    html(f'<div class="brand"><span class="brand-mark">{icon("book", 25)}</span><div class="brand-name">Estuda<span>PDF</span><small>LEITURA COM CONTEXTO</small></div></div>')


def hero() -> None:
    html(f'''<section class="hero" aria-labelledby="hero-title">
      <div class="hero-copy"><div class="eyebrow"><span></span> SEU ESPAÇO DE ESTUDO</div>
      <h1 id="hero-title">Menos procura.<br>Mais <em>entendimento.</em></h1>
      <p>Converse com seu material e encontre explicações<br class="desktop-break"> acompanhadas das fontes que você pode conferir.</p>
      <div class="hero-footnote">{icon("file",16)} Seu documento <span>+</span> {icon("spark",16)} Inteligência artificial</div></div>
      <div class="hero-visual" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <div class="paper paper-back"></div><div class="paper paper-front"><span class="paper-file">{icon("file",21)} MATERIAL DE ESTUDO</span>
        <div class="paper-line long"></div><div class="paper-line"></div><div class="paper-highlight"></div><div class="paper-line medium"></div><div class="paper-line short"></div>
        <div class="paper-source">{icon("quote",14)} Uma fonte para cada descoberta</div></div>
        <div class="insight-stamp">{icon("spark",23)}</div><div class="source-sticker">{icon("check",14)} Baseado no seu material</div>
      </div></section>''')


def empty_evidence() -> None:
    html(f'''<div class="empty-evidence"><div class="evidence-illustration"><div class="evidence-paper">{icon("file",47)}<span></span><span></span></div><span class="evidence-search">{icon("search",23)}</span></div>
    <h3>Uma boa resposta começa<br>com uma fonte.</h3><p>Faça sua primeira pergunta.<br>Os trechos encontrados no material<br>vão aparecer aqui para conferência.</p>
    <div class="empty-source-tag">{icon("shield",14)} Evidências sempre à vista</div></div>''')
