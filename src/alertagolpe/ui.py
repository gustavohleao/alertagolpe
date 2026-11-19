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
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "bolt": '<path d="M13 2 4 14h7l-1 8 9-12h-7Z"/>',
    "circle": '<circle cx="12" cy="12" r="8"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "upload": '<path d="M12 16V4m-5 5 5-5 5 5M4 20h16"/>',
    "alert": '<path d="M12 3 2 20h20Z"/><path d="M12 10v4M12 17h.01"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4Z"/><path d="M8 9h8M8 12h5"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
}


def icon(name: str, size: int = 20) -> str:
    # st.html restringe SVG inline. A máscara local usa apenas formas estáticas
    # conhecidas e herda a cor, sem buscar arquivos ou fontes na rede.
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>'
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
    html(f'<div class="brand"><span class="brand-mark">{icon("shield", 22)}</span><div class="brand-name">Alerta<span>Golpe</span><small>CONFIRA ANTES DE CLICAR</small></div></div>')


def stat(icon_name: str, value: int, label: str) -> str:
    """Indicador numérico com contagem animada (CSS); o valor final fica no atributo."""
    number = int(value)
    return (f'<div class="stat-card"><span class="stat-icon">{icon(icon_name, 18)}</span><div>'
            f'<div class="stat-value" style="--n:{number}" aria-label="{number}"></div>'
            f'<div class="stat-label">{safe(label)}</div></div></div>')


def score_ring(score: int, total: int = 2, label: str = "Critérios atendidos") -> str:
    percent = round(100 * score / max(total, 1))
    tone = "good" if score == total else ("mid" if score else "low")
    return (f'<div class="score-block {tone}"><div class="score-ring" style="--p:{percent}"><span>{int(score)}<small>/{int(total)}</small></span></div>'
            f'<div><div class="score-label">{safe(label)}</div><div class="score-hint">'
            f'{"Excelente! Todos os critérios foram atendidos." if tone == "good" else "Bom começo. Veja o que faltou abaixo." if tone == "mid" else "Vale revisar este ponto no material."}'
            f'</div></div></div>')


def criteria_list(criteria, met) -> str:
    items = "".join(
        f'<li class="{"met" if ok else "missed"}"><span class="crit-icon">{icon("check" if ok else "circle", 14)}</span>{safe(text)}</li>'
        for text, ok in zip(criteria, met))
    return f'<ul class="criteria-list">{items}</ul>'


def hero() -> None:
    html(f'''<section class="hero" aria-labelledby="hero-title">
      <div class="hero-bg" aria-hidden="true"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span><span class="hero-grid"></span></div>
      <div class="hero-copy"><div class="eyebrow"><span class="pulse"></span> DETECTOR DE GOLPES COM IA</div>
      <h1 id="hero-title">Recebeu uma mensagem estranha?<br><em>Confira antes de clicar.</em></h1>
      <p>Cole a mensagem de WhatsApp, SMS ou e-mail. O AlertaGolpe mostra os sinais de alerta, com qual golpe conhecido ela se parece e o que fazer agora.</p>
      <div class="hero-chips"><span>{icon("alert",15)} Sinais explicados</span><span>{icon("book",15)} 21 golpes catalogados</span><span>{icon("check",15)} O que fazer agora</span></div></div>
      <div class="hero-visual" aria-hidden="true">
        <div class="float-card card-chat"><div class="fc-label">{icon("chat",13)} MENSAGEM RECEBIDA</div>
          <div class="chat-bubble">Oi mãe, troquei de número 😅 consegue me fazer um <mark>Pix urgente</mark>?</div></div>
        <div class="float-card card-risk"><span class="risk-dot"></span><div><strong>RISCO ALTO</strong><small>golpe muito provável</small></div></div>
        <div class="float-card card-source">{icon("alert",13)} Pede Pix · <b>urgência</b></div>
        <div class="float-card card-plan"><div class="fc-label">{icon("shield",13)} PARECE COM</div>
          <div class="match-name">Falso parente com número novo</div><div class="bar-row"><span>semelhança</span><i style="--w:86%"></i></div></div>
      </div></section>''')


def empty_evidence() -> None:
    html(f'''<div class="empty-evidence"><div class="evidence-illustration"><div class="evidence-paper">{icon("file",40)}<span></span><span></span></div><span class="evidence-search">{icon("search",21)}</span></div>
    <h3>Uma boa resposta começa<br>com uma fonte.</h3><p>Faça sua primeira pergunta.<br>Os trechos encontrados no material<br>vão aparecer aqui para conferência.</p>
    <div class="empty-source-tag">{icon("shield",14)} Evidências sempre à vista</div></div>''')


def empty_state(icon_name: str, title: str, text: str) -> None:
    html(f'<div class="empty-state"><span class="empty-icon">{icon(icon_name, 24)}</span><div><strong>{safe(title)}</strong><p>{safe(text)}</p></div></div>')
