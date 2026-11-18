"""Sinais de alerta detectados localmente, por regras explicáveis (sem IA).

Cada regra corresponde a um padrão recorrente nos alertas de bancos e órgãos
públicos. A pontuação é heurística: não é uma probabilidade calibrada.
"""

from dataclasses import dataclass
import re

_I = re.IGNORECASE


@dataclass(frozen=True)
class Rule:
    key: str
    rotulo: str
    explicacao: str
    peso: int
    pattern: re.Pattern


@dataclass(frozen=True)
class Signal:
    key: str
    rotulo: str
    explicacao: str
    peso: int
    trecho: str


RULES: tuple[Rule, ...] = (
    Rule("codigo_senha", "Pede código, senha ou token",
         "Bancos e empresas nunca pedem senha ou códigos recebidos por SMS.", 25,
         re.compile(r"\b(c[oó]digo|senha|token|cvv|c[oó]digo de verifica[cç][aã]o)\b", _I)),
    Rule("numero_novo", "Diz que trocou de número",
         "É a abertura típica do golpe do falso parente.", 25,
         re.compile(r"(troquei de (?:n[uú]mero|celular|chip)|n[uú]mero novo|novo n[uú]mero|salv[ae] (?:esse|este|meu|o) (?:n[uú]mero|contato))", _I)),
    Rule("instalar_app", "Pede para instalar aplicativo ou dar acesso",
         "Aplicativos de acesso remoto permitem que o golpista controle o celular.", 25,
         re.compile(r"((?:instal|baix)\w* (?:o |um |esse |este )?(?:aplicativo|app)|acesso remoto|anydesk|teamviewer)", _I)),
    Rule("pix", "Pede Pix, transferência ou depósito",
         "Pedidos de dinheiro por mensagem são o objetivo da maioria dos golpes.", 20,
         re.compile(r"\b(pix|transfer[eêi]\w*|dep[oó]sit\w*|chave pix)\b", _I)),
    Rule("link", "Contém link",
         "Links em mensagens inesperadas podem levar a sites falsos.", 20,
         re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|site|online|xyz|top|info|club|shop|link|ly)(?:\.br)?(?:/\S*)?)", _I)),
    Rule("dinheiro_facil", "Promete prêmio, lucro ou dinheiro fácil",
         "Ganhos fáceis, garantidos ou inesperados são isca frequente.", 20,
         re.compile(r"(ganhou|sortead[oa]|pr[eê]mio|valores? a receber|dinheiro esquecido|renda extra|lucro garantido|rend\w* \d+ ?% ?ao dia|ganhe (?:de |at[eé] )?r\$)", _I)),
    Rule("taxa_antecipada", "Cobra taxa para liberar algo",
         "Cobrar para liberar prêmio, empréstimo, encomenda ou ganho é sinal clássico de golpe.", 20,
         re.compile(r"\b(taxa|frete|seguro|ativa[cç][aã]o)\b[^.!?]{0,60}\b(liberar|libera[cç][aã]o|receber|resgatar|evitar devolu[cç][aã]o)\b", _I)),
    Rule("urgencia", "Cria urgência ou ameaça",
         "Pressa e ameaça de bloqueio impedem a vítima de pensar e conferir.", 15,
         re.compile(r"\b(urgente|imediatamente|at[eé] hoje|s[oó] hoje|ainda hoje|[uú]ltimas? (?:horas|unidades|vagas)|em at[eé] \d+ ?h|bloquead[oa]|suspens[ao]|evitar (?:o )?cancelamento|restam poucas)\b", _I)),
    Rule("dados_pessoais", "Pede dados pessoais ou do cartão",
         "CPF e dados do cartão permitem fraudes em seu nome.", 15,
         re.compile(r"\b(cpf|dados do cart[aã]o|n[uú]mero do cart[aã]o|data de nascimento)\b", _I)),
    Rule("instituicao", "Usa o nome de banco, empresa ou órgão público",
         "Golpistas se passam por instituições conhecidas para ganhar confiança.", 10,
         re.compile(r"\b(banco central|banco|central de (?:seguran[cç]a|atendimento)|receita federal|receita|correios|inss|gov\.br|mei|cnpj|serasa|caixa|nubank|ita[uú]|bradesco|santander)\b", _I)),
    Rule("pendencia", "Fala em pendência ou regularização",
         "Avisos de 'pendência' com link para 'regularizar' são isca comum de golpes com nome de órgão público.", 15,
         re.compile(r"\b(pend[eê]ncias?|irregularidades?|irregular|regularizar|regulariza[cç][aã]o)\b", _I)),
    # Sinal de legitimidade (peso negativo): só vale quando a mensagem não tem link.
    Rule("canal_oficial", "Orienta usar o aplicativo ou canal oficial",
         "Mandar a pessoa ao aplicativo oficial, sem link, é típico de avisos legítimos.", -15,
         re.compile(r"((?:acessando|acesse|abra|abrindo|use|usando|pelo|no seu|pelo seu|pelo pr[oó]prio) (?:o )?(?:app|aplicativo)\b(?! (?:de suporte|que (?:vou|vamos) (?:te )?enviar))|n[uú]mero (?:no|do) verso do (?:seu )?cart[aã]o|canais oficiais)", _I)),
)

LEVELS = (("alto", 55), ("medio", 25), ("baixo", 0))


def detect(message: str) -> list[Signal]:
    found = []
    for rule in RULES:
        match = rule.pattern.search(message)
        if match:
            found.append(Signal(rule.key, rule.rotulo, rule.explicacao, rule.peso, match.group(0)))
    # Um golpista também pode citar o app e, junto, mandar link ou pedir código, Pix ou dados:
    # nesses casos o "sinal de legitimidade" não vale.
    if any(s.key in ("link", "instalar_app", "codigo_senha", "pix", "dados_pessoais", "taxa_antecipada") for s in found):
        found = [s for s in found if s.peso > 0]
    return found


def alerts(signals: list[Signal]) -> list[Signal]:
    """Só os sinais de alerta (peso positivo), sem os sinais de legitimidade."""
    return [s for s in signals if s.peso > 0]


def local_score(signals: list[Signal]) -> int:
    return max(0, min(100, sum(signal.peso for signal in signals)))


def local_level(score: int) -> str:
    return next(level for level, minimum in LEVELS if score >= minimum)
