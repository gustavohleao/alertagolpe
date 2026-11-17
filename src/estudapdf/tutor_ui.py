"""Interface de prática, feedback e acompanhamento em memória da sessão."""

from dataclasses import asdict
import json
import streamlit as st

from .providers import ProviderError
from .tutor import TutorError, create_round, evaluate, progress_rows
from .ui import criteria_list, empty_state, html, icon, safe, score_ring, section_heading, stat


def _round_header(topic: str, answers: dict) -> None:
    steps = "".join(
        f'<span class="round-step {"done" if i in answers else "current" if i == len(answers) else ""}">'
        f'{icon("check", 12) if i in answers else i + 1}</span>' for i in range(3))
    html(f'<div class="round-header"><div><div class="round-kicker">{icon("target",13)} RODADA ATIVA</div>'
         f'<h3>{safe(topic)}</h3></div><div class="round-steps">{steps}</div></div>')


def render_tutor(config, ready_config, source_name):
    history = st.session_state.setdefault("tutor_history", [])
    with st.container(key="tutor_setup"):
        section_heading("01", "Descubra o que precisa revisar", "Escolha um assunto, responda sem consultar o gabarito e confira as evidências depois.")
        topic = st.text_input("Qual assunto você quer praticar?", max_chars=200, placeholder="Ex.: RAG, aprendizado supervisionado ou TF-IDF", key="tutor_topic")
        st.caption("A rodada usa até três trechos encontrados por assunto, sem prometer cobertura de todo o PDF. Até quatro chamadas de IA: uma para preparar e uma por resposta.")
        if st.button("Preparar rodada de revisão", type="primary", use_container_width=True, icon=":material/bolt:"):
            try:
                with st.spinner("Preparando perguntas e critérios com base no material…"):
                    previous = [h["exercise"]["question"] for h in history if h["topic"] == topic.strip()]
                    new_round = create_round(topic, st.session_state["index"], ready_config(config), authorized=True, previous=previous)
                st.session_state["tutor_round"] = new_round
                st.session_state["tutor_answers"] = {}
                st.session_state["tutor_round_nonce"] = st.session_state.get("tutor_round_nonce", 0) + 1
            except (TutorError, ProviderError) as exc:
                st.error(str(exc))
    active = st.session_state.get("tutor_round")
    if active:
        answers = st.session_state.setdefault("tutor_answers", {})
        nonce = st.session_state.get("tutor_round_nonce", 0)
        completed = len(answers)
        with st.container(key="tutor_round_box"):
            _round_header(active.topic, answers)
            st.progress(completed / 3, text=f"{completed} de 3 respostas avaliadas")
        for i, exercise in enumerate(active.exercises):
            done = i in answers
            with st.container(key=f"tutor_q_{nonce}_{i}"):
                status = f'<span class="q-status done">{icon("check",12)} Avaliada</span>' if done else '<span class="q-status pending">Aguardando resposta</span>'
                html(f'<div class="q-head"><span class="q-num">{i + 1}</span><span class="q-label">PERGUNTA {i + 1} DE 3</span>{status}</div>')
                st.text(exercise.question)
                if not done:
                    with st.form(f"tutor_answer_{nonce}_{i}", border=False):
                        answer = st.text_area("Sua resposta", max_chars=4000, key=f"tutor_text_{nonce}_{i}", placeholder="Explique com suas palavras, sem consultar o material…", height=120)
                        submitted = st.form_submit_button("Avaliar minha resposta", type="primary", icon=":material/task_alt:")
                    if submitted:
                        try:
                            with st.spinner("Conferindo a resposta com os critérios e as fontes…"):
                                result = evaluate(exercise, answer, active.hits, ready_config(config), authorized=True)
                            record = {"topic": active.topic, "exercise": asdict(exercise), "answer": answer.strip(), "evaluation": result,
                                      "evidence": [asdict(h.chunk) for h in active.hits if h.chunk.id in exercise.sources]}
                            answers[i] = record
                            history.append(record)
                            st.rerun()
                        except (TutorError, ProviderError) as exc:
                            st.error(str(exc))
                else:
                    record = answers[i]
                    result = record["evaluation"]
                    html('<div class="mini-label">SUA RESPOSTA</div>')
                    with st.container(key=f"tutor_ans_{nonce}_{i}"):
                        st.text(record["answer"])
                    if result["assessable"]:
                        html(score_ring(result["score"]) + criteria_list(exercise.criteria, result["met"]))
                    else:
                        st.warning("A IA não conseguiu sustentar esta correção. Ela ficou fora do indicador de desempenho.")
                    with st.container(key=f"tutor_fb_{nonce}_{i}"):
                        html(f'<div class="mini-label">{icon("spark",12)} FEEDBACK</div>')
                        st.text(result["feedback"])
                        html(f'<div class="mini-label next">{icon("arrow",12)} PRÓXIMO PASSO</div>')
                        st.text(result["next_step"])
                    with st.expander("Conferir resposta esperada e fontes", icon=":material/fact_check:"):
                        st.text(exercise.expected)
                        for hit in active.hits:
                            if hit.chunk.id in exercise.sources:
                                st.caption(f"{hit.chunk.location_label} {hit.chunk.page} · [{hit.chunk.id}]")
                                st.text(hit.chunk.text)
        if len(answers) == 3:
            st.success("Rodada concluída. Veja as prioridades abaixo e prepare outra rodada sobre o assunto que precisar revisar.", icon=":material/celebration:")
    with st.container(key="tutor_plan"):
        section_heading("02", "Seu plano de revisão", "Prioridades calculadas a partir das respostas desta sessão.")
        rows = progress_rows(history)
        if rows:
            assessed = sum(row["Respostas avaliadas"] for row in rows)
            average = round(sum(row["Critérios atendidos (%)"] * row["Respostas avaliadas"] for row in rows) / max(assessed, 1))
            html(f'<div class="stat-group plan-stats">{stat("target", len(rows), "Assuntos praticados")}{stat("check", assessed, "Respostas avaliadas")}{stat("chart", average, "% de critérios atendidos")}</div>')
            st.dataframe(rows, hide_index=True, use_container_width=True, column_config={
                "Critérios atendidos (%)": st.column_config.ProgressColumn("Critérios atendidos", min_value=0, max_value=100, format="%d%%"),
            })
            st.caption("Prioridade baseada nos critérios das respostas desta sessão, não em uma medição validada de domínio. Rodadas diferentes podem ter dificuldades diferentes.")
            st.info(f"Comece por: {rows[0]['Assunto']}. Reveja as evidências e prepare outra rodada nesse assunto.", icon=":material/flag:")
        else:
            empty_state("chart", "Seu plano aparece aqui", "Responda às perguntas para construir seu plano. Correções não sustentadas ficam fora dos indicadores.")
        if history:
            st.download_button("Baixar histórico de revisão", json.dumps({"aplicacao": "EstudaPDF", "fonte": source_name,
                                "versao_prompt": "tutor-v1", "historico": history, "plano": rows}, ensure_ascii=False, indent=2),
                               file_name="estudapdf-revisao.json", mime="application/json", icon=":material/download:")
        st.caption("A IA pode errar na pergunta, no gabarito e na correção. Confira as fontes e discuta divergências com seu professor. Histórico mantido apenas nesta sessão; o download contém suas respostas e trechos do material.")
