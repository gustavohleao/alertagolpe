"""Interface do AlertaGolpe."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import streamlit as st

from .analyzer import MAX_MESSAGE_CHARS, AnalysisError, analyze
from .catalog import BY_ID, CATALOG
from .providers import ProviderConfig, ProviderError, list_models
from .settings import load_settings
from .signals import RULES
from .ui import brand, hero, html, icon, safe, section_heading

EXAMPLES = {
    "Falso parente": "Oi mãe, troquei de número, salva esse aqui. Tô precisando de uma ajuda urgente, consegue me fazer um Pix de R$ 1.200 hoje? O app do meu banco travou, amanhã te devolvo.",
    "Falsa central": "BANCO: Compra de R$ 3.479,00 aprovada no seu cartão final 4410. Se não reconhece, ligue AGORA para a Central de Segurança 0800 591 2034 e informe o código que enviamos para cancelar.",
    "Mensagem normal": "Oi! Passando pra lembrar que a reunião do grupo do trabalho de IA ficou para quinta às 19h, na biblioteca. Leva o notebook que vamos ensaiar a apresentação.",
}

RISK_UI = {
    "alto": ("alert", "RISCO ALTO", "Golpe muito provável", "high"),
    "medio": ("shield", "RISCO MÉDIO", "Suspeita: confirme antes de agir", "mid"),
    "baixo": ("check", "RISCO BAIXO", "Sem sinais fortes de golpe", "low"),
}


def _env_timeout(settings: dict[str, str]) -> int:
    try:
        return max(5, min(300, int(settings.get("LLM_TIMEOUT_SECONDS") or "90")))
    except ValueError:
        return 90


def _ready_config(config: ProviderConfig) -> ProviderConfig:
    if not config.model:
        signature = sha256(config.api_key.encode("utf-8")).hexdigest()
        cached = st.session_state.get("automatic_model")
        if cached and cached[0] == signature:
            model = cached[1]
        else:
            models = list_models("gemini", api_key=config.api_key)
            eligible = [m for m in models if not any(w in m.lower() for w in ("image", "tts", "live", "audio", "robotics"))]
            if not eligible:
                raise ProviderError("O serviço de IA não encontrou um modelo de texto disponível.")
            model = ([m for m in eligible if "flash" in m.lower()] or eligible)[0]
            st.session_state["automatic_model"] = (signature, model)
        config = replace(config, model=model)
    config.validate()
    return config


def _set_example(text: str) -> None:
    st.session_state["message_input"] = text
    st.session_state.pop("analysis", None)


def _sidebar(config: ProviderConfig) -> None:
    history = st.session_state.get("history", [])
    with st.sidebar:
        brand()
        html(f'<div class="sidebar-label">{icon("chat",12)} COMO USAR</div>'
             '<ol class="how-steps"><li>Copie a mensagem suspeita</li><li>Cole no campo ao lado</li><li>Veja os sinais e o que fazer</li></ol>')
        html(f'<div class="sidebar-label">{icon("clock",12)} ANÁLISES DESTA SESSÃO <span class="label-count">{len(history)}</span></div>')
        if not history:
            html('<div class="library-empty"><p>Suas análises aparecem aqui. Nada é gravado em disco.</p></div>')
        for item in reversed(history[-6:]):
            _, label, _, tone = RISK_UI[item["risk"]]
            html(f'<div class="hist-item"><span class="hist-badge {tone}">{label.replace("RISCO ", "")}</span><span class="hist-text">{safe(item["preview"])}</span></div>')
        if config.api_key:
            html(f'<div class="ai-status online"><span class="status-dot"></span><div><strong>IA conectada</strong><small>{safe(config.model or "Modelo automático · Gemini")}</small></div></div>')
        else:
            st.warning("IA não configurada: o app fará apenas a análise local por regras.")
        if st.button("Limpar sessão", use_container_width=True, key="clear_session", icon=":material/restart_alt:"):
            st.session_state.clear()
            st.rerun()
        html('<div class="sidebar-footer">ALERTAGOLPE / PROJETO ACADÊMICO<br>IA Generativa · 2026</div>')


def _risk_banner(analysis) -> None:
    ic, label, sub, tone = RISK_UI[analysis.risk]
    source = "Análise com IA (Gemini) + regras locais" if analysis.used_ai else "Análise local por regras (sem IA)"
    html(f'<div class="risk-banner {tone}"><div class="risk-icon">{icon(ic, 30)}</div><div class="risk-copy">'
         f'<div class="risk-label">{label}</div><div class="risk-sub">{safe(sub)}</div>'
         f'<p>{safe(analysis.summary)}</p><div class="risk-source">{safe(source)}</div></div></div>')


def _result(analysis) -> None:
    _risk_banner(analysis)
    if analysis.divergent:
        st.warning("A IA e as regras automáticas discordaram bastante nesta mensagem. Trate como suspeita e confirme pelo canal oficial.")
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        with st.container(key="findings_panel"):
            html(f'<div class="panel-header">{icon("alert",18)}<h2>Por que é suspeito</h2><span class="panel-count">{len(analysis.findings) if analysis.used_ai else len(analysis.signals)}</span></div>')
            if analysis.used_ai and analysis.findings:
                for n, finding in enumerate(analysis.findings, start=1):
                    html(f'<div class="finding"><span class="finding-num">{n}</span><div><mark class="quote">“{safe(finding.trecho)}”</mark>'
                         f'<p>{safe(finding.explicacao)}</p></div></div>')
            elif not analysis.used_ai and analysis.signals:
                for n, sig in enumerate(analysis.signals, start=1):
                    html(f'<div class="finding"><span class="finding-num">{n}</span><div><mark class="quote">“{safe(sig.trecho)}”</mark>'
                         f'<p><b>{safe(sig.rotulo)}.</b> {safe(sig.explicacao)}</p></div></div>')
            else:
                html('<p class="muted-note">Nenhum sinal de alerta relevante foi encontrado nesta mensagem.</p>')
        with st.container(key="actions_panel"):
            html(f'<div class="panel-header">{icon("check",18)}<h2>O que fazer agora</h2></div>'
                 '<ol class="action-list">' + "".join(f"<li>{safe(a)}</li>" for a in analysis.actions) + "</ol>")
    with right:
        with st.container(key="match_panel"):
            html(f'<div class="panel-header">{icon("book",18)}<h2>Parece com</h2></div>')
            if analysis.scam_id:
                scam = BY_ID[analysis.scam_id]
                score = next((h.score for h in analysis.candidates if h.chunk.id == scam.id), 0)
                html(f'<div class="match-card"><span class="match-id">{scam.id}</span><h3>{safe(scam.nome)}</h3>'
                     f'<p>{safe(scam.como_funciona)}</p><div class="sim-meter"><span>Semelhança</span><div class="sim-track">'
                     f'<i style="--w:{max(6, min(100, round(score * 250)))}%"></i></div><b>{score:.2f}</b></div>'
                     '<div class="sources">Fontes: ' + " · ".join(f'<a href="{safe(u)}" target="_blank" rel="noopener">{i}</a>' for i, u in enumerate(scam.fontes, 1)) + "</div></div>")
            else:
                html('<p class="muted-note">A mensagem não corresponde a nenhum golpe do catálogo.</p>')
        with st.container(key="signals_panel"):
            html(f'<div class="panel-header">{icon("search",18)}<h2>Sinais automáticos</h2><span class="panel-count">{analysis.local_score}/100</span></div>'
                 f'<div class="score-line {analysis.local_level}"><div class="lib-track"><i style="--w:{analysis.local_score}%"></i></div></div>'
                 '<div class="chips">' + ("".join(f'<span class="chip">{safe(s.rotulo)}</span>' for s in analysis.signals) or '<span class="chip off">nenhum</span>') + "</div>"
                 '<p class="muted-note">Detectados por regras fixas, sem IA. Servem de segunda opinião.</p>')
        meta = f"{analysis.elapsed_seconds:.2f} s · {analysis.provider} · {analysis.model}" if analysis.used_ai else f"{analysis.elapsed_seconds:.2f} s · sem chamada de IA"
        html(f'<div class="consultation-meta">{icon("clock",13)} {safe(meta)}</div>')
        st.download_button("Baixar análise (.json)", json.dumps(analysis.export(), ensure_ascii=False, indent=2),
                           file_name="alertagolpe-analise.json", mime="application/json", icon=":material/download:", use_container_width=True)


def _analyze_tab(config: ProviderConfig) -> None:
    with st.container(key="composer"):
        section_heading("01", "Cole a mensagem suspeita", "WhatsApp, SMS, e-mail ou post. Pode colar exatamente como recebeu.")
        message = st.text_area("Mensagem", key="message_input", height=150, max_chars=MAX_MESSAGE_CHARS, label_visibility="collapsed",
                               placeholder="Ex.: Oi, troquei de número, consegue me fazer um Pix urgente?")
        html('<div class="examples-label">OU TESTE COM UM EXEMPLO</div>')
        with st.container(key="examples"):
            for column, (label, text) in zip(st.columns(3), EXAMPLES.items()):
                column.button(label, on_click=_set_example, args=(text,), use_container_width=True)
        submitted = st.button("Analisar mensagem", type="primary", use_container_width=True, icon=":material/shield:")
        st.caption("Ao analisar, a mensagem é enviada à API Gemini. Apague nomes, CPF, números de cartão e outros dados pessoais antes de colar.")
    if submitted:
        st.session_state.pop("analysis", None)
        try:
            active = _ready_config(config) if config.api_key else None
            with st.spinner("Procurando sinais de golpe…"):
                analysis = analyze(message, active)
            st.session_state["analysis"] = analysis
            history = st.session_state.setdefault("history", [])
            history.append({"risk": analysis.risk, "preview": " ".join(analysis.message.split())[:46] + "…"})
        except (AnalysisError, ProviderError) as exc:
            st.error(str(exc))
    analysis = st.session_state.get("analysis")
    if analysis is not None:
        _result(analysis)


def _catalog_tab() -> None:
    section_heading("02", "Golpes conhecidos", f"{len(CATALOG)} golpes frequentes no Brasil, com sinais típicos e o que fazer. É a base usada na comparação.")
    for scam in CATALOG:
        with st.expander(f"{scam.id} · {scam.nome}"):
            html(f'<p class="scam-how">{safe(scam.como_funciona)}</p>'
                 '<div class="scam-cols"><div><div class="mini-label">SINAIS TÍPICOS</div><ul>' + "".join(f"<li>{safe(s)}</li>" for s in scam.sinais) + "</ul></div>"
                 '<div><div class="mini-label next">O QUE FAZER</div><ul>' + "".join(f"<li>{safe(a)}</li>" for a in scam.o_que_fazer) + "</ul></div></div>"
                 f'<div class="mini-label">EXEMPLO FICTÍCIO</div><div class="scam-example">{safe(scam.exemplo)}</div>'
                 '<div class="sources">Fontes: ' + " · ".join(f'<a href="{safe(u)}" target="_blank" rel="noopener">{i}</a>' for i, u in enumerate(scam.fontes, 1)) + "</div>")


def _about_tab() -> None:
    with st.container(key="about_card"):
        section_heading("03", "Como a análise funciona", "Três camadas independentes, combinadas no resultado.")
        stages = [("search", "Regras locais", f"{len(RULES)} sinais clássicos"), ("book", "Catálogo", "busca TF-IDF + cosseno"),
                  ("spark", "Gemini", "explica e classifica"), ("check", "Validação", "trechos e IDs conferidos"), ("shield", "Resultado", "risco + o que fazer")]
        html('<div class="about-flow">' + "".join(f'<div class="flow-step" style="--i:{n}"><span class="flow-icon">{icon(ic,18)}</span><strong>{safe(t)}</strong><small>{safe(d)}</small></div>' for n, (ic, t, d) in enumerate(stages)) + '</div>')
        st.write("**1. Regras locais.** Expressões que identificam pedidos de Pix, códigos, links, urgência, troca de número, prêmios e outros sinais. Funcionam sem internet e geram uma pontuação de 0 a 100.")
        st.write("**2. Busca no catálogo.** A mensagem é comparada aos golpes catalogados por TF-IDF e similaridade do cosseno — a mesma técnica de recuperação usada em sistemas RAG. Os três golpes mais parecidos são enviados à IA como contexto.")
        st.write("**3. IA generativa.** O Gemini recebe a mensagem (como dado não confiável), os sinais e os candidatos, e devolve risco, resumo, sinais com trechos exatos e ações, em JSON.")
        st.write("**4. Validação.** O app recusa golpes fora da lista de candidatos e descarta sinais cujo trecho não existe na mensagem. Se a IA e as regras discordarem muito, um aviso aparece.")
    with st.container(key="about_limits"):
        st.markdown("### Limites")
        st.write("A análise é um apoio, não uma garantia. Golpes novos podem não estar no catálogo, mensagens legítimas podem ser marcadas como suspeitas e vice-versa. Na dúvida, confirme sempre pelo canal oficial da empresa ou ligando para a pessoa.")
        st.markdown("### Privacidade")
        st.write("A mensagem é enviada à API Gemini para a análise com IA. O histórico fica só nesta sessão do navegador e não é gravado em disco. Evite colar dados pessoais.")


def render_app(root: Path) -> None:
    settings = load_settings(root)
    st.set_page_config(page_title="AlertaGolpe · Confira antes de clicar", page_icon="🛡️", layout="wide", initial_sidebar_state="auto")
    st.html(f'<style>{(root / "assets" / "styles.css").read_text(encoding="utf-8")}</style>')
    config = ProviderConfig("gemini", settings["LLM_MODEL"].strip(), settings["GEMINI_API_KEY"].strip(), timeout=_env_timeout(settings))
    status = '<span class="top-pill online"><span class="status-dot"></span>Gemini online</span>' if config.api_key else '<span class="top-pill offline"><span class="status-dot"></span>Somente regras locais</span>'
    html(f'<div class="workspace-topbar"><div class="breadcrumb">{icon("shield",16)} AlertaGolpe <span class="slash">/</span><strong>Analisar mensagem</strong></div><div class="topbar-right"><span class="workspace-label">{icon("check",14)} Sinais explicados</span>{status}</div></div>')
    hero()
    analyze_tab, catalog_tab, about_tab = st.tabs([":material/shield: Analisar mensagem", ":material/menu_book: Golpes conhecidos", ":material/info: Como funciona"])
    with analyze_tab:
        _analyze_tab(config)
    with catalog_tab:
        _catalog_tab()
    with about_tab:
        _about_tab()
    _sidebar(config)
    html('<footer class="workspace-footer"><span><strong>AlertaGolpe</strong> · Na dúvida, não clique e não transfira.</span><span>A IA pode errar. Confirme pelo canal oficial.</span></footer>')
