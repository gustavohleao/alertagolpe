"""Workspace do EstudaPDF: interface separada da recuperação e da geração."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import streamlit as st

from .demo import DEMO_NAME, demo_pages
from .document import DocumentError, extract_pdf, split_pages
from .providers import ProviderConfig, ProviderError, list_models
from .retrieval import DocumentIndex
from .service import run_query
from .settings import load_settings
from .summary import SummaryError, prepare_summary, summarize
from .tutor import progress_rows
from .tutor_ui import render_tutor
from .ui import brand, empty_evidence, hero, html, icon, safe, section_heading, stat


def _env_timeout(settings: dict[str, str]) -> int:
    try:
        return max(5, min(300, int(settings.get("LLM_TIMEOUT_SECONDS") or "90")))
    except ValueError:
        return 90


def _set_example(question: str) -> None:
    st.session_state["question_input"] = question


DEMO_KEY = "demo-v1"
MAX_LIBRARY = 6


def _config(settings: dict[str, str]) -> ProviderConfig:
    return ProviderConfig("gemini", settings["LLM_MODEL"].strip(), settings["GEMINI_API_KEY"].strip(), timeout=_env_timeout(settings))


def _library() -> dict:
    """Materiais desta sessão, do mais antigo ao mais recente. Nada é gravado em disco."""
    return st.session_state.setdefault("library", {})


def _entry_id(key: str) -> str:
    return sha256(key.encode("utf-8")).hexdigest()[:12]


def _open_material(key: str) -> None:
    library = _library()
    if key in library:
        library[key] = library.pop(key)  # move para o topo dos recentes
        st.session_state["active_material"] = key


def _remove_material(key: str) -> None:
    _library().pop(key, None)
    if key == DEMO_KEY:
        st.session_state["use_demo"] = False
    if st.session_state.get("active_material") == key:
        st.session_state.pop("active_material", None)


def _toggle_demo() -> None:
    if st.session_state.get("use_demo"):
        st.session_state["active_material"] = DEMO_KEY
    else:
        _remove_material(DEMO_KEY)


def _progress(history) -> tuple[int, int, int]:
    rows = progress_rows(history)
    answers = sum(row["Respostas avaliadas"] for row in rows)
    percent = round(sum(row["Critérios atendidos (%)"] * row["Respostas avaliadas"] for row in rows) / answers) if answers else 0
    return len(rows), answers, percent


def _sidebar(config: ProviderConfig) -> None:
    library, active = _library(), st.session_state.get("active_material")
    with st.sidebar:
        brand()
        html(f'<div class="sidebar-label">{icon("book",12)} MATERIAIS ESTUDADOS <span class="label-count">{len(library)}</span></div>')
        if not library:
            html(f'<div class="library-empty">{icon("file",20)}<p>Nenhum material ainda. Carregue um PDF no centro da página para começar.</p></div>')
        for key in reversed(list(library)):
            entry, current = library[key], key == active
            topics, answers, percent = _progress(entry["history"])
            unit = "seções" if entry["is_demo"] else "páginas"
            progress_line = (f'{answers} {"resposta" if answers == 1 else "respostas"} · {topics} {"assunto" if topics == 1 else "assuntos"}'
                             if answers else "Ainda sem revisão")
            now = '<span class="lib-now">ATIVO</span>' if current else ""
            # O nome do arquivo só entra em HTML escapado, nunca em rótulo de botão (que aceita Markdown).
            with st.container(key=f"{'libactive' if current else 'lib'}_{_entry_id(key)}"):
                html(f'<div class="lib-item"><div class="lib-top"><span class="lib-icon">{icon("spark" if entry["is_demo"] else "file",16)}</span>'
                     f'<div class="lib-copy"><div class="lib-name">{safe(entry["name"])}</div><div class="lib-meta">{len(entry["pages"])} {unit} · {safe(entry["kind"])}</div></div>{now}</div>'
                     f'<div class="lib-progress"><div class="lib-track"><i style="--w:{percent}%"></i></div><b>{percent}%</b></div>'
                     f'<div class="lib-foot">{safe(progress_line)}</div></div>')
                open_col, remove_col = st.columns([3, 1])
                if not current:
                    open_col.button("Abrir", key=f"open_{_entry_id(key)}", on_click=_open_material, args=(key,), use_container_width=True, icon=":material/play_arrow:")
                remove_col.button(":material/close:", key=f"remove_{_entry_id(key)}", on_click=_remove_material, args=(key,), help="Remover da lista desta sessão", use_container_width=True)
        st.caption("A lista vale só para esta sessão. Os materiais ficam em memória e não são gravados em disco.")
        if not config.api_key:
            st.warning("O serviço de IA está aguardando configuração pelo responsável do aplicativo.")
        else:
            html(f'<div class="ai-status online"><span class="status-dot"></span><div><strong>IA conectada</strong><small>{safe(config.model or "Modelo automático · Gemini")}</small></div></div>')
        if st.button("Limpar sessão", use_container_width=True, key="clear_session", icon=":material/restart_alt:"):
            next_nonce = st.session_state.get("upload_nonce", 0) + 1
            st.session_state.clear()
            st.session_state["upload_nonce"] = next_nonce
            st.rerun()
        html('<div class="sidebar-footer">ESTUDAPDF / PROJETO ACADÊMICO<br>IA Generativa · 2026</div>')


def _ready_config(config: ProviderConfig) -> ProviderConfig:
    if not config.api_key:
        raise ProviderError("O serviço de IA está aguardando configuração pelo responsável do aplicativo.")
    if not config.model:
        signature = sha256(config.api_key.encode("utf-8")).hexdigest()
        cached = st.session_state.get("automatic_model")
        if cached and cached[0] == signature:
            model = cached[1]
        else:
            models = list_models("gemini", api_key=config.api_key)
            eligible = [model for model in models if not any(word in model.lower() for word in ("image", "tts", "live", "audio", "robotics"))]
            preferred = [model for model in eligible if "flash" in model.lower()]
            if not eligible:
                raise ProviderError("O serviço de IA não encontrou um modelo de texto disponível.")
            model = (preferred or eligible)[0]
            st.session_state["automatic_model"] = (signature, model)
        config = replace(config, model=model)
    config.validate()
    return config


def _index_material(pages):
    chunks = split_pages(pages)
    return {"pages": pages, "chunks": chunks, "index": DocumentIndex(chunks), "history": []}


def _add_material(key: str, entry: dict) -> None:
    library = _library()
    library[key] = entry
    st.session_state["active_material"] = key
    while len(library) > MAX_LIBRARY:
        library.pop(next(k for k in library if k != key))
        st.toast("O material mais antigo saiu da lista para liberar memória.", icon=":material/info:")


def _upload_panel():
    has_library = bool(_library())
    with st.container(key="upload_panel"):
        copy_col, drop_col = st.columns([1, 1.35], gap="large", vertical_alignment="center")
        with copy_col:
            section_heading("+", "Adicionar outro material" if has_library else "Comece pelo seu material",
                            "Envie um PDF da disciplina. Ele aparece na barra lateral junto com seu progresso.")
            st.session_state.setdefault("use_demo", True)
            st.checkbox("Usar material de demonstração", key="use_demo", on_change=_toggle_demo)
            st.caption("PDF com texto selecionável, até 15 MB e 150 páginas. Use um material que você tem autorização para processar.")
        with drop_col:
            uploaded = st.file_uploader("Carregar um PDF", type=["pdf"], key=f"uploaded_pdf_{st.session_state.get('upload_nonce', 0)}",
                                        label_visibility="collapsed", help="Processamento em memória, sem gravação em disco.")
    return uploaded


def _load_material(uploaded):
    library = _library()
    if uploaded is not None:
        data = uploaded.getvalue()
        key = f"pdf:{sha256(data).hexdigest()}:{uploaded.name}"
        if key in library:
            _open_material(key)
        elif st.session_state.get("failed_upload", ("",))[0] != key:
            try:
                with st.spinner("Organizando seu material para consulta…"):
                    entry = _index_material(extract_pdf(data))
            except (DocumentError, ValueError) as exc:
                st.session_state["failed_upload"] = (key, str(exc))
            else:
                _add_material(key, {**entry, "name": uploaded.name, "kind": "Seu documento", "is_demo": False})
        failed = st.session_state.get("failed_upload")
        if failed and failed[0] == key:
            st.error(failed[1])
        else:
            # Esvazia a área de envio para o próximo arquivo; o material já está na biblioteca.
            st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1
            st.rerun()
    if st.session_state.get("use_demo") and DEMO_KEY not in library:
        library[DEMO_KEY] = {**_index_material(demo_pages()), "name": DEMO_NAME, "kind": "Material de demonstração", "is_demo": True}
        st.session_state.setdefault("active_material", DEMO_KEY)
    active = st.session_state.get("active_material")
    if active not in library:
        active = next(reversed(library), None)
        st.session_state["active_material"] = active
    if active is None:
        return None
    entry = library[active]
    if st.session_state.get("document_key") != active:
        for state_key in list(st.session_state):
            if state_key.startswith("tutor_"):
                del st.session_state[state_key]
        st.session_state.pop("result", None)
        st.session_state.pop("summary_result", None)
        st.session_state.pop("summary_scope", None)
        # A lista do histórico é a mesma da biblioteca: o progresso fica guardado por material.
        st.session_state.update(document_key=active, pages=entry["pages"], chunks=entry["chunks"], index=entry["index"], tutor_history=entry["history"])
    return entry


def _material_bar(entry):
    pages, chunks, demo = entry["pages"], entry["chunks"], entry["is_demo"]
    meta = "Texto educativo dividido em seções" if demo else "Texto extraído por página · pronto para consulta"
    html(f'<div class="material-bar"><div class="document-info"><div class="document-icon">{icon("file",22)}</div>'
         f'<div class="document-copy"><div class="doc-label"><span class="ready-dot"></span>Estudando agora · {safe(entry["kind"])}</div>'
         f'<div class="doc-name">{safe(entry["name"])}</div><div class="doc-meta">{safe(meta)}</div></div></div>'
         f'<div class="stat-group">{stat("book", len(pages), "Seções" if demo else "Páginas com texto")}'
         f'{stat("layers", len(chunks), "Trechos indexados")}</div></div>')


def _answer(result, source_name):
    with st.container(key="answer_panel"):
        generated = result.status == "generated"
        label = "Resposta com IA" if generated else "Resultado da consulta"
        badge = "IA GENERATIVA" if generated else "BUSCA NO MATERIAL"
        html(f'<div class="response-header"><h2>{icon("spark" if generated else "search",20)} {label}</h2><span class="response-type">{badge}</span></div>')
        html(f'<div class="result-question">{safe(result.question)}</div>')
        if generated:
            # Permanecer em texto simples: respostas não podem carregar imagens/HTML.
            st.text(result.text)
            html(f'<div class="consultation-meta">{icon("clock",13)} {result.elapsed_seconds:.2f} s <span class="separator">/</span> {safe(result.provider)} <span class="separator">/</span> {safe(result.model)}</div>')
            st.caption(result.warning)
        elif result.status in {"provider_error", "invalid_citations"}:
            st.error(result.text)
            st.caption("Os trechos encontrados continuam disponíveis. Você pode conferi-los mesmo sem uma resposta gerada.")
        else:
            st.info(result.text)
            html(f'<div class="consultation-meta">{icon("clock",13)} {result.elapsed_seconds:.2f} s <span class="separator">/</span> Recuperação local · sem geração</div>')
        with st.expander("Registro e transparência"):
            st.caption("O registro contém pergunta, trechos e resposta, quando houver. Revise o conteúdo antes de compartilhar. Sua chave não é incluída.")
            st.download_button("Baixar registro desta consulta", json.dumps(result.export(source_name), ensure_ascii=False, indent=2), file_name="estudapdf-consulta.json", mime="application/json", use_container_width=True)


def _evidence(result):
    with st.container(key="evidence_panel"):
        count = str(len(result.hits)) if result is not None else "FONTES"
        html(f'<div class="panel-header">{icon("quote",18)}<h2>Evidências do material</h2><span class="panel-count">{count}</span></div>')
        if result is None:
            empty_evidence()
            return
        if not result.hits:
            st.caption("Nenhum trecho atingiu o limiar da busca. Tente reformular a pergunta usando termos presentes no material.")
            return
        st.caption("Confira se os trechos sustentam a resposta. Similaridade indica correspondência lexical, não confiança.")
        for position, hit in enumerate(result.hits):
            with st.expander(f"{hit.chunk.location_label} {hit.chunk.page} · [{hit.chunk.id}]", expanded=position == 0):
                html(f'<div class="sim-meter"><span>Similaridade</span><div class="sim-track"><i style="--w:{max(4, min(100, round(hit.score * 100)))}%"></i></div><b>{hit.score:.2f}</b></div>')
                st.text(hit.chunk.text)
                st.caption(f"Similaridade lexical: {hit.score:.3f} · consulte o contexto original.")


def _about():
    with st.container(key="about_card"):
        section_heading("01", "Do material à explicação", "O caminho percorrido por cada consulta.")
        stages = [("file", "Seu PDF", "Texto extraído"), ("layers", "Trechos", "Divisão do texto"), ("search", "Busca", "TF-IDF + cosseno"), ("quote", "Contexto", "Até 3 passagens"), ("spark", "Resposta", "Gemini com citações")]
        html('<div class="about-flow">' + "".join(f'<div class="flow-step" style="--i:{n}"><span class="flow-icon">{icon(ic,18)}</span><strong>{safe(t)}</strong><small>{safe(d)}</small></div>' for n, (ic, t, d) in enumerate(stages)) + '</div>')
        st.write("O texto é extraído por página e dividido em trechos. TF-IDF representa as palavras e pares de palavras; a similaridade do cosseno seleciona até três passagens para o contexto. Quando a resposta com IA está ativada, o modelo recebe esses trechos e a pergunta, com instruções para reconhecer lacunas e citar evidências.")
        st.info("A recuperação é lexical, sem embeddings semânticos. Não há treinamento de classificador nem alteração dos pesos do modelo de linguagem.")
        st.markdown("### Uma visão geral do material")
        st.write("A aba Resumir material usa outro fluxo: percorre todo o texto extraído do intervalo selecionado, produz resumos por partes e os combina em uma síntese. Esse processo não depende dos três trechos da busca. A interface informa o volume e o limite de chamadas antes de iniciar; um resumo pode omitir detalhes, então confira as fontes.")
    with st.container(key="about_limits"):
        st.markdown("### O que vale conferir")
        st.write("Sinônimos e perguntas vagas podem prejudicar a recuperação. PDFs escaneados precisam de OCR, fora deste protótipo; tabelas e colunas podem perder estrutura. Uma referência válida não garante interpretação correta. Confira sempre o trecho e seu contexto.")
        st.markdown("### Seus dados e o uso de IA")
        st.write("PDFs e consultas não são gravados automaticamente no disco. O material fica no estado da sessão, sem cache global. Limpar a sessão remove suas referências no aplicativo, sem promessa de eliminação forense. Gemini recebe a pergunta e os trechos mediante autorização. Um registro baixado pode conter conteúdo documental.")
        st.caption("O material de demonstração, o código e os textos foram elaborados com assistência de IA e precisam de revisão do grupo. Instruções no prompt não eliminam o risco de conteúdo malicioso no documento.")


def _summary_tab(mode: str, config: ProviderConfig, source_name: str):
    pages = st.session_state["pages"]
    location = "seções" if pages[0].location_label == "Seção" else "páginas"
    with st.container(key="summary_composer"):
        section_heading("02", "Uma visão geral do seu material", "Resumo do texto selecionado, com os conceitos principais e referências.")
        st.caption("O resumo percorre o texto em partes. Imagens e páginas sem texto selecionável ficam fora da análise; detalhes podem ser omitidos na síntese.")
        first, last = min(page.number for page in pages), max(page.number for page in pages)
        if first != last:
            start, end = st.slider(f"Intervalo de {location}", min_value=first, max_value=last, value=(first, last), key=f"summary_range_{st.session_state['document_key']}")
        else:
            start, end = first, last
            st.caption(f"{pages[0].location_label} {first}: todo o texto disponível será considerado.")
        selected = [page for page in pages if start <= page.number <= end]
        scope = f"{st.session_state['document_key']}:{start}:{end}"
        if st.session_state.get("summary_scope") != scope:
            st.session_state.pop("summary_result", None)
            st.session_state["summary_scope"] = scope
        try:
            plan = prepare_summary(selected)
        except SummaryError as exc:
            st.warning(str(exc))
            st.caption("Escolha um intervalo menor. Nenhum texto é enviado e nenhuma página é cortada silenciosamente.")
            return
        total_chars = f"{plan.characters:,}".replace(",", ".")
        page_label = ("seção" if location == "seções" else "página") if len(plan.pages) == 1 else location
        call_label = "chamada" if plan.max_calls == 1 else "chamadas"
        html(f'<div class="summary-facts"><span>{icon("file",15)} {len(plan.pages)} {safe(page_label)} com texto</span><span>{icon("layers",15)} {total_chars} caracteres</span><span>{icon("spark",15)} Até {plan.max_calls} {call_label} de IA</span></div>')
        st.caption("O número de chamadas depende do tamanho do texto e das sínteses intermediárias. Se o Gemini estiver sobrecarregado (erro 503), cada chamada é repetida automaticamente até 3 vezes. Documentos maiores podem levar vários minutos.")
        allow_external = True
        if mode != "Resposta com IA":
            st.info("Selecione Resposta com IA na barra lateral para gerar um resumo. A busca simples continua disponível na Sala de estudo.")
        submitted = st.button("Gerar resumo do material", type="primary", use_container_width=True, disabled=mode != "Resposta com IA")
        if submitted:
            st.session_state.pop("summary_result", None)
            progress = None
            try:
                config = _ready_config(config)
                progress = st.progress(0.0, text="Preparando a leitura do material…")

                def report(completed: int, maximum: int, message: str):
                    progress.progress(min(completed / max(maximum, 1), 0.95), text=f"{message} · {completed} de até {maximum} chamadas concluídas")

                result = summarize(plan, config, allow_external=allow_external, on_progress=report)
                st.session_state["summary_result"] = result
                progress.progress(1.0, text="Resumo concluído.")
            except (SummaryError, ProviderError) as exc:
                st.error(str(exc))
                st.caption("O resumo não foi concluído. Nenhuma síntese parcial será apresentada como resumo completo.")
            finally:
                if progress is not None:
                    progress.empty()
    result = st.session_state.get("summary_result")
    if result is None:
        return
    summary_col, sources_col = st.columns([1.65, 1], gap="large")
    with summary_col:
        with st.container(key="summary_output"):
            html(f'<div class="response-header"><h2>{icon("book",20)} Resumo do material</h2><span class="response-type">SÍNTESE COM IA</span></div>')
            parts = getattr(result, "parts", ())
            if parts:
                html(f'<div class="mini-label">{icon("spark",12)} VISÃO GERAL</div>')
                st.text(result.overview)
                html(f'<div class="mini-label next">{icon("layers",12)} RESUMO POR PARTES · {len(parts)} PARTES</div>')
                for part in parts:
                    # Texto do modelo permanece em st.text; o rótulo do expander é gerado pelo app.
                    with st.expander(f"Parte {part['parte']} · {part['local']}", expanded=part["parte"] == 1):
                        st.text(part["texto"])
            else:
                st.text(result.text)
            summary_warning = getattr(result, "warning", "")
            if summary_warning:
                st.warning(summary_warning)
            page_label = ("seção" if location == "seções" else "página") if len(result.pages) == 1 else location
            processed_label = "processada" if len(result.pages) == 1 else "processadas"
            call_label = "chamada" if result.calls_completed == 1 else "chamadas"
            st.caption(f"{len(result.pages)} {page_label} com texto {processed_label} · {result.calls_completed} {call_label} · {result.elapsed_seconds:.2f} s · {result.provider} · {result.model}")
            st.caption("O resumo é do texto extraído, não uma garantia de cobertura de todas as ideias ou de interpretação correta. Confira as referências no material original.")
            text_col, record_col = st.columns(2)
            with text_col:
                download_text = f"Aviso: {summary_warning}\n\n{result.text}" if summary_warning else result.text
                st.download_button("Baixar resumo (.txt)", download_text, file_name="estudapdf-resumo.txt", mime="text/plain", use_container_width=True)
            with record_col:
                st.download_button("Baixar registro (.json)", json.dumps(result.export(source_name), ensure_ascii=False, indent=2), file_name="estudapdf-resumo-registro.json", mime="application/json", use_container_width=True)
            st.caption("Os downloads contêm conteúdo do material. Revise antes de compartilhar; a chave não é incluída no registro.")
    with sources_col:
        with st.container(key="summary_evidence"):
            cited = set(result.citations)
            if cited:
                html(f'<div class="panel-header">{icon("quote",18)}<h2>Fontes citadas no resumo</h2><span class="panel-count">{len(cited)}</span></div>')
                st.caption("Os identificadores R pertencem ao resumo; são diferentes dos identificadores T usados nas perguntas.")
                for position, chunk in enumerate(chunk for chunk in result.source_chunks if chunk.id in cited):
                    with st.expander(f"{chunk.location_label} {chunk.page} · [{chunk.id}]", expanded=position == 0):
                        st.text(chunk.text)
            else:
                html(f'<div class="panel-header">{icon("file",18)}<h2>Texto processado</h2><span class="panel-count">{len(result.source_chunks)}</span></div>')
                st.caption("O modelo não vinculou afirmações a referências. Os trechos abaixo mostram o texto de entrada, sem atribuir citações ou comprovar as afirmações do resumo.")
                options = [f"{chunk.location_label} {chunk.page} · [{chunk.id}]" for chunk in result.source_chunks]
                selected_source = st.selectbox("Consultar trecho processado", options)
                st.text(result.source_chunks[options.index(selected_source)].text)


def render_app(root: Path) -> None:
    settings = load_settings(root)
    st.set_page_config(page_title="EstudaPDF · Seu espaço de estudo", page_icon="📖", layout="wide", initial_sidebar_state="auto")
    st.html(f'<style>{(root / "assets" / "styles.css").read_text(encoding="utf-8")}</style>')
    config, mode = _config(settings), "Resposta com IA"
    status = '<span class="top-pill online"><span class="status-dot"></span>Gemini online</span>' if config.api_key else '<span class="top-pill offline"><span class="status-dot"></span>IA aguardando configuração</span>'
    html(f'<div class="workspace-topbar"><div class="breadcrumb">{icon("book",16)} Workspace <span class="slash">/</span><strong>Sala de estudo</strong></div><div class="topbar-right"><span class="workspace-label">{icon("shield",14)} Respostas com evidências</span>{status}</div></div>')
    hero()
    uploaded = _upload_panel()
    entry = _load_material(uploaded)
    _sidebar(config)
    if entry is None:
        st.info("Carregue um PDF ou ative o material de demonstração para começar.")
        st.stop()
    source_name = entry["name"]
    _material_bar(entry)
    tutor_tab, study_tab, summary_tab, about_tab = st.tabs([":material/school: Revisão ativa", ":material/manage_search: Consultar material", ":material/summarize: Resumir material", ":material/info: Como funciona"])
    with tutor_tab:
        render_tutor(config, _ready_config, source_name)
    with study_tab:
        workspace, evidence = st.columns([1.65, 1], gap="large")
        with workspace:
            with st.container(key="composer"):
                section_heading("01", "O que você quer descobrir?", "Faça uma pergunta sobre o material selecionado.")
                with st.form("question_form", border=False):
                    question = st.text_area("Sua pergunta", key="question_input", label_visibility="collapsed", placeholder="Ex.: Como o material explica este conceito?", max_chars=1200, height=132)
                    hint_col, action_col = st.columns([1.15, 1], vertical_alignment="center")
                    with hint_col:
                        st.caption("Cada pergunta é uma nova consulta.")
                    with action_col:
                        submitted = st.form_submit_button("Buscar e responder" if mode == "Resposta com IA" else "Encontrar trechos", type="primary", use_container_width=True)
                if entry["is_demo"]:
                    st.caption("PARA COMEÇAR")
                    with st.container(key="question_examples"):
                        examples = [
                            ("Como funciona o RAG?", "Como funciona o RAG?"),
                            ("Comparar conceitos", "Qual a diferença entre aprendizado supervisionado e não supervisionado?"),
                            ("Limites da busca", "Quais são os limites da busca por TF-IDF?"),
                        ]
                        for column, (label, example) in zip(st.columns(3), examples):
                            column.button(label, on_click=_set_example, args=(example,), use_container_width=True)
            if submitted:
                st.session_state.pop("result", None)
                can_run = True
                active_config = config if mode == "Resposta com IA" else None
                if active_config is not None:
                    try:
                        active_config = _ready_config(active_config)
                    except ProviderError as exc:
                        st.error(str(exc))
                        can_run = False
                if can_run:
                    try:
                        message = "Consultando o modelo com as evidências encontradas. A geração pode levar alguns minutos…" if active_config else "Encontrando trechos no seu material…"
                        with st.spinner(message):
                            st.session_state["result"] = run_query(question, st.session_state["index"], active_config)
                    except ValueError as exc:
                        st.warning(str(exc))
            result = st.session_state.get("result")
            if result is not None:
                _answer(result, source_name)
            else:
                html(f'<div class="insight-note">{icon("shield",17)} As respostas são um ponto de partida. O material original continua sendo sua referência.</div>')
        with evidence:
            _evidence(st.session_state.get("result"))
    with about_tab:
        _about()
    with summary_tab:
        _summary_tab(mode, config, source_name)
    html('<footer class="workspace-footer"><span><strong>EstudaPDF</strong> · Aprender começa com uma boa pergunta.</span><span>IA pode errar. Confira as fontes.</span></footer>')
