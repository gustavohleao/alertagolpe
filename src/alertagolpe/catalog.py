"""Catálogo de golpes conhecidos no Brasil, usado como base de conhecimento (RAG).

Descrições compiladas a partir de alertas públicos de bancos, da Febraban, do
Banco Central e da imprensa (ver campo ``fontes``). Redigido com assistência de
IA e sujeito à revisão do grupo. As mensagens de exemplo são fictícias.
"""

from dataclasses import dataclass
import json
from pathlib import Path

from .models import Chunk

FEBRABAN_TOP = "https://www.opovo.com.br/noticias/economia/2024/04/02/federacao-de-bancos-alerta-para-golpes-a-contas-bancarias-veja-dicas.html"
FEBRABAN_PIX = "https://tecnoblog.net/noticias/febraban-lista-fraudes-golpes-envolvendo-pix/"
FALSA_CENTRAL = "https://meutudo.com.br/blog/noticias/2026/07/09/golpe-da-falsa-central-telefonica-pode-imitar-seu-banco-como-se-proteger/"
CNN_PIX = "https://www.cnnbrasil.com.br/business/caiu-no-golpe-do-pix-saiba-o-que-fazer-e-como-se-proteger/"
CANALTECH_10 = "https://canaltech.com.br/seguranca/estes-sao-os-10-golpes-financeiros-mais-comuns-no-brasil/"
WHATSAPP = "https://consumidormoderno.com.br/golpe-whatsapp-saiba-proteger/"
SERASA = "https://www.serasa.com.br/guias/como-proteger-meu-cpf-de-fraudes/"
BCB_SVR = "https://valoresareceber.bcb.gov.br/"
SVR_GOLPE = "https://olhardigital.com.br/2023/07/06/seguranca/cuidado-golpes-envolvendo-dinheiro-esquecido-voltam-a-acontecer/"
SEBRAE_MEI = "https://agenciasebrae.com.br/cultura-empreendedora/nao-caia-em-golpe-conheca-as-cobrancas-falsas-em-alta-contra-o-mei"
OAB_ADVOGADO = "https://www.oabsp.org.br/jornaldaadvocacia/24-11-04-1434-oab-sp-faz-novos-alertas-para-combater-o-golpe-do-falso-advogado"
FEBRABAN_ADVOGADO = "https://jornaldebrasilia.com.br/noticias/brasil/febraban-alerta-consumidores-sobre-o-golpe-do-falso-advogado/"
PCPR_SEQUESTRO = "https://www.parana.pr.gov.br/aen/Noticia/PCPR-orienta-populacao-sobre-como-identificar-e-evitar-o-golpe-do-falso-sequestro"
SERASA_SEQUESTRO = "https://www.serasa.com.br/premium/blog/como-funciona-o-golpe-do-falso-sequestro/"
SERASA_ALUGUEL = "https://www.serasa.com.br/premium/blog/golpe-aluguel/"
BAND_ALUGUEL = "https://www.band.com.br/bandnews-fm/noticias/golpe-do-aluguel-falso-criminosos-pedem-caucao-antes-de-visita-ao-imovel-202508070854"
GOV_DOACAO = "https://agenciagov.ebc.com.br/noticias/202405/campanha-alerta-sobre-golpes-em-que-os-criminosos-solicitam-doacoes-as-vitimas-das-enchentes-nos-estados-do-rs-e-de-sc-com-chave-pix-falsa"
SANTANDER_DOACAO = "https://www.santander.com.br/blog/golpe-pix-rio-grande-do-sul"
CNH_SUSPENSA = "https://canaltech.com.br/seguranca/golpe-da-cnh-suspensa-usa-sms-falso-alerta-detran-saiba-como-se-proteger/"
MEDICO_CANALTECH = "https://canaltech.com.br/seguranca/falsos-medicos-aplicam-golpes-na-familia-de-pacientes-internados-259922/"
MEDICO_BAND = "https://www.band.com.br/bandnews-fm/noticias/alerta-de-golpe-criminosos-pedem-pix-a-familiares-de-pacientes-internados-202508191105"
SEXTORSAO_ESET = "https://www.welivesecurity.com/br/2019/02/27/campanhas-de-sextorsao-continuam-circulando-por-email/"
SEXTORSAO_TECNOBLOG = "https://tecnoblog.net/466795/golpe-de-falsa-extorsao-no-brasil-ja-roubou-r-15-mil-em-bitcoin/"
INTERMEDIARIO_SERASA = "https://www.serasa.com.br/premium/blog/golpe-na-olx-como-identificar-o-falso-anuncio-de-venda-de-carros/"
INTERMEDIARIO_MEUTUDO = "https://meutudo.com.br/blog/golpe-do-intermediario/"
INSS_GOV = "https://agenciagov.ebc.com.br/noticias/202504/links-falsos-estao-circulando-nas-redes-sociais-para-consulta-a-suposto-direito-de-segurados-do-inss-a-indenizacao"
INSS_CANALTECH = "https://canaltech.com.br/seguranca/inss-alerta-para-golpe-com-link-falso-para-consultar-direito-a-indenizacao/"
INGRESSO_SERASA = "https://www.serasa.com.br/premium/blog/golpe-do-ingresso-falso-o-que-fazer-para-nao-cair-nele/"
INGRESSO_CNN = "https://www.cnnbrasil.com.br/nacional/sudeste/sp/golpe-do-ingresso-falso-veja-dicas-de-como-se-previnir/"
DIVIDA_SERASA = "https://www.serasa.com.br/limpa-nome-online/blog/golpe-do-desenrola-brasil/"
DIVIDA_OLHAR = "https://olhardigital.com.br/2023/07/19/seguranca/desenrola-brasil-golpes-circulam-no-whatsapp-e-facebook-veja-como-se-proteger/"
QRCODE_JC = "https://www.jornaldocomercio.com/economia/2026/10/1267712-golpe-do-qr-code-pode-desviar-pagamentos-por-boleto-e-pix.html"
QRCODE_CANALTECH = "https://canaltech.com.br/seguranca/pix-e-qr-code-os-golpes-invisiveis-que-ainda-fazem-vitimas-no-brasil/"
CONSORCIO_SERASA = "https://www.serasa.com.br/premium/blog/como-identificar-golpe-do-consorcio-contemplado/"
CONSORCIO_OLHAR = "https://olhardigital.com.br/2022/12/01/dicas-e-tutoriais/o-que-e-e-como-funciona-um-golpe-de-consorcio/"
RESERVA_CANALTECH = "https://canaltech.com.br/seguranca/novo-golpe-faz-voce-pagar-em-dobro-pela-sua-reserva-no-booking-e-airbnb/"
RESERVA_TECNOBLOG = "https://tecnoblog.net/noticias/golpe-do-sequestro-de-reserva-usa-dados-reais-de-hoteis-para-enganar-brasileiros/"
GOV_DASN = "https://www.gov.br/pt-br/servicos/declarar-receita-bruta-anual-para-o-mei"
PIX_ERRADO = "https://www.opovo.com.br/noticias/economia/2024/07/11/amp/entenda-o-golpe-do-pix-errado-e-saiba-como-nao-ser-enganado.html"


@dataclass(frozen=True)
class Scam:
    id: str
    nome: str
    como_funciona: str
    sinais: tuple[str, ...]
    exemplo: str
    o_que_fazer: tuple[str, ...]
    fontes: tuple[str, ...]

    def index_text(self) -> str:
        reais = [e.texto for e in REAL_EXAMPLES.get(self.id, ())]
        return " ".join([self.nome, self.como_funciona, *self.sinais, self.exemplo, *reais])


@dataclass(frozen=True)
class RealExample:
    """Mensagem de golpe real, copiada de reportagem ou alerta público (campo ``fonte``)."""
    golpe: str
    texto: str
    fonte: str


REAL_FILE = Path(__file__).with_name("exemplos_reais.json")


def _load_real_examples() -> dict[str, list[RealExample]]:
    if not REAL_FILE.is_file():
        return {}
    out: dict[str, list[RealExample]] = {}
    for item in json.loads(REAL_FILE.read_text(encoding="utf-8"))["exemplos"]:
        out.setdefault(item["golpe"], []).append(RealExample(item["golpe"], item["texto"], item["fonte"]))
    return out


REAL_EXAMPLES = _load_real_examples()


CATALOG: tuple[Scam, ...] = (
    Scam("G01", "Falso parente ou amigo com número novo",
         "O golpista usa a foto de um parente ou amigo, diz que trocou de número e, depois de uma conversa curta, pede um Pix urgente para pagar uma conta ou emergência.",
         ("Diz que trocou de número", "Pede para salvar o novo contato", "Pede dinheiro com urgência", "Evita ligação de voz ou vídeo", "Pede Pix para conta de terceiro"),
         "Oi mãe, troquei de número, salva esse aqui. Tô com um problema, preciso pagar um boleto hoje e meu app do banco tá bloqueado, consegue fazer um Pix pra mim? Depois te devolvo.",
         ("Ligue para o número antigo da pessoa ou faça uma chamada de vídeo antes de qualquer transferência.", "Não transfira para contas em nome de terceiros.", "Denuncie o número no próprio WhatsApp."),
         (FEBRABAN_TOP, WHATSAPP)),
    Scam("G02", "Falsa central de atendimento do banco",
         "Alguém se passa pela central do banco e avisa sobre uma compra suspeita ou invasão. Para 'proteger' a conta, pede senha, código recebido por SMS, transferência para uma 'conta segura' ou instalação de aplicativo.",
         ("Fala em compra suspeita ou conta invadida", "Pede senha, token ou código SMS", "Pede transferência para conta de segurança", "Cria urgência e pressão", "Pede para instalar aplicativo"),
         "Central de Segurança do Banco: identificamos uma compra de R$ 2.890,00 no seu cartão. Se não reconhece, ligue imediatamente para 0800 ou responda com o código que enviamos por SMS para cancelar.",
         ("Desligue e ligue você mesmo para o número oficial do banco, que está no verso do cartão.", "Nenhum banco pede senha, código ou transferência por telefone ou mensagem.", "Não instale aplicativos indicados por quem ligou."),
         (FEBRABAN_TOP, FALSA_CENTRAL)),
    Scam("G03", "Link falso de banco, cartão ou conta (phishing)",
         "Mensagem por SMS, e-mail ou WhatsApp imita o banco, o e-mail, o streaming ou outro serviço, informa bloqueio, pagamento recusado, caixa cheia, pontos a vencer ou atualização cadastral e leva a um site falso que captura senha e dados do cartão.",
         ("Link encurtado ou com endereço estranho", "Bloqueio de conta ou cartão", "Pontos ou milhas prestes a vencer", "Pede atualização de cadastro ou de pagamento", "Conta de e-mail, streaming ou rede social prestes a ser excluída", "Pede dados do cartão ou senha"),
         "BANCO INFORMA: seu cartao foi bloqueado por seguranca. Regularize em ate 24h para evitar cancelamento: https://bit.ly/regulariza-cartao",
         ("Não clique no link; acesse o banco apenas pelo aplicativo oficial ou digitando o endereço.", "Confira o remetente: bancos não enviam links para desbloqueio.", "Se digitou dados, avise o banco imediatamente e troque as senhas."),
         (CANALTECH_10, SERASA)),
    Scam("G04", "Falso entregador ou taxa de entrega pendente",
         "Mensagem fingindo ser dos Correios ou de transportadora informa que uma encomenda está retida e cobra uma pequena taxa, frete ou imposto por link ou Pix para liberar a entrega.",
         ("Encomenda retida ou não entregue", "Taxa alfandegária ou de reentrega", "Valor pequeno para parecer inofensivo", "Link para pagamento", "Prazo curto antes da devolução"),
         "Correios: sua encomenda BR458932 está retida por falta de pagamento da taxa de importação de R$ 12,90. Pague até hoje para evitar devolução: correios-rastreio-entrega.com",
         ("Consulte o rastreio só no site ou aplicativo oficial dos Correios ou da loja.", "Não pague taxas por links recebidos em mensagens.", "Desconfie de cobrança de encomenda que você não esperava."),
         (CANALTECH_10,)),
    Scam("G05", "Boleto falso ou adulterado",
         "O golpista envia um boleto parecido com o verdadeiro, ou altera o código de barras, para que o pagamento caia na conta dele. Comum em cobranças de condomínio, escola, financiamento e renegociação de dívidas.",
         ("Boleto enviado por mensagem ou e-mail inesperado", "Desconto ou renegociação vantajosa demais", "Beneficiário diferente da empresa", "Pressa para pagar"),
         "Prezado cliente, segue boleto atualizado da sua fatura com 40% de desconto para quitação ainda hoje. Após o vencimento o desconto será perdido.",
         ("Antes de pagar, confira se o nome do beneficiário é o da empresa.", "Emita a segunda via só pelo site ou aplicativo oficial.", "Desconfie de descontos para pagamento imediato."),
         (CANALTECH_10, SERASA)),
    Scam("G06", "Falsa vaga de emprego ou tarefa paga",
         "Oferece renda extra fácil para curtir vídeos, avaliar produtos ou fazer tarefas simples. Paga valores pequenos no início e depois exige depósitos para liberar ganhos maiores.",
         ("Renda extra fácil trabalhando de casa", "Pagamento por curtidas ou avaliações", "Pede depósito para liberar comissão", "Contato não solicitado", "Promessa de ganho diário alto"),
         "Olá! Vi seu perfil e temos uma vaga home office: ganhe de R$ 200 a R$ 800 por dia só curtindo vídeos. Para começar, faça a tarefa de ativação com um depósito de R$ 50 e receba R$ 120 de volta.",
         ("Empresas sérias não cobram para você trabalhar.", "Nunca deposite dinheiro para liberar ganhos.", "Pesquise o nome da empresa e o CNPJ antes de qualquer contato."),
         (CANALTECH_10,)),
    Scam("G07", "Investimento com lucro garantido",
         "Promete rendimentos altos e garantidos em pouco tempo, muitas vezes com criptomoedas, robôs de trading ou grupos de investimento. Os primeiros ganhos são falsos e servem para atrair mais depósitos.",
         ("Lucro alto e garantido", "Retorno em poucos dias", "Pressão para entrar logo", "Depoimentos de ganhos", "Indicação de amigos com bônus"),
         "Oportunidade exclusiva: nosso robô de investimento rende 3% ao dia garantido. Invista a partir de R$ 100 e saque em 7 dias. Restam poucas vagas no grupo VIP!",
         ("Não existe investimento com lucro alto e garantido.", "Verifique se a empresa é autorizada pela CVM ou pelo Banco Central.", "Desconfie de pressão para decidir rápido."),
         (CANALTECH_10, SERASA)),
    Scam("G08", "Clonagem de WhatsApp pelo código de verificação",
         "O golpista pede o código de 6 dígitos que chegou por SMS, fingindo ser de uma pesquisa, sorteio, loja ou empresa de entregas. Com o código, ele assume a conta e pede dinheiro aos contatos da vítima.",
         ("Pede código recebido por SMS", "Diz que é para confirmar cadastro, pesquisa ou promoção", "Código de 6 dígitos", "Mensagem de empresa conhecida"),
         "Olá, aqui é da loja onde você comprou. Para confirmar seu cadastro na promoção, enviamos um código de 6 dígitos por SMS, pode me informar qual chegou?",
         ("Nunca compartilhe códigos recebidos por SMS.", "Ative a confirmação em duas etapas no WhatsApp.", "Se perdeu o acesso, avise seus contatos por outro meio."),
         (WHATSAPP, FEBRABAN_PIX)),
    Scam("G09", "Falso prêmio ou sorteio",
         "Informa que a pessoa ganhou um prêmio, carro ou valor em dinheiro em um sorteio do qual não participou e pede uma taxa, dados pessoais ou código para liberar o prêmio.",
         ("Prêmio de sorteio que você não participou", "Taxa para liberar o prêmio", "Pede dados pessoais ou bancários", "Prazo curto para resgatar"),
         "PARABÉNS! Seu número foi sorteado e você ganhou R$ 5.000,00 na promoção de aniversário. Para receber, pague a taxa de liberação de R$ 49,90 até as 18h.",
         ("Prêmios verdadeiros não exigem pagamento para liberar.", "Não informe dados bancários a quem anunciou o prêmio.", "Confirme a promoção no site oficial da empresa."),
         (CANALTECH_10,)),
    Scam("G10", "Comprovante falso ou Pix enviado por engano",
         "Em vendas online, o golpista mostra um comprovante falso ou agendado. Em outra versão, diz que fez um Pix 'por engano' e pede devolução para outra conta, enquanto contesta o Pix original.",
         ("Comprovante enviado por imagem", "Pix agendado apresentado como feito", "Pede devolução de Pix enviado por engano", "Devolução para conta diferente"),
         "Moça, te mandei um Pix de R$ 300 por engano, era pra outra pessoa. Consegue devolver pra essa chave aqui? É urgente, preciso pagar o aluguel.",
         ("Confira o crédito no extrato do banco, não no comprovante.", "Devolva Pix só pela função de devolução do próprio aplicativo, para a mesma conta de origem.", "Não envie mercadoria antes de confirmar o pagamento no extrato."),
         (PIX_ERRADO, FEBRABAN_PIX)),
    Scam("G11", "Loja ou anúncio falso com preço muito baixo",
         "Anúncios em redes sociais ou sites que imitam lojas conhecidas oferecem produtos com desconto muito alto, aceitam só Pix e nunca entregam.",
         ("Preço muito abaixo do mercado", "Pagamento só por Pix", "Site recém-criado ou parecido com loja famosa", "Estoque limitado e pressa"),
         "SUPER QUEIMA: iPhone novo lacrado por R$ 1.499 só hoje! Pagamento exclusivamente via Pix com 10% de desconto. Últimas unidades, chama no direct.",
         ("Desconfie de preços muito abaixo do mercado.", "Pesquise a reputação da loja e confira o CNPJ.", "Prefira meios de pagamento com proteção ao comprador."),
         (FEBRABAN_TOP, CANALTECH_10)),
    Scam("G12", "Falso empréstimo com taxa antecipada",
         "Oferece crédito fácil, mesmo para negativados, e exige o pagamento de uma taxa, seguro ou 'depósito de garantia' antes de liberar o dinheiro, que nunca chega.",
         ("Crédito aprovado sem consulta", "Taxa antecipada para liberar", "Empréstimo para negativado", "Contato por WhatsApp de 'correspondente'"),
         "Seu empréstimo de R$ 10.000 foi APROVADO mesmo com nome negativado. Para liberar hoje, basta pagar a taxa de seguro de R$ 350 via Pix.",
         ("Instituições sérias não cobram para liberar empréstimo.", "Verifique se a empresa é autorizada pelo Banco Central.", "Nunca pague antecipadamente para receber crédito."),
         (SERASA, CANALTECH_10)),
    Scam("G13", "Falso órgão público ou valores a receber",
         "Mensagem em nome da Receita Federal, do INSS, do Detran, do governo ou do Banco Central fala em CPF irregular, restituição, benefício, multa, CNH suspensa, IPVA ou licenciamento pendente, ou 'valores a receber', e pede dados, pagamento por Pix ou clique em link.",
         ("Nome de órgão público ou Banco Central", "CPF irregular ou bloqueado", "Multa, CNH suspensa, IPVA ou licenciamento pendente", "Valores esquecidos ou benefício a receber", "Link para consulta ou regularização", "Taxa para liberar valor"),
         "Banco Central: você possui R$ 1.874,32 em valores a receber esquecidos. Resgate até amanhã informando seu CPF no link: valores-receber-bc.site",
         ("O único site de valores a receber é valoresareceber.bcb.gov.br; o Banco Central não envia links.", "Órgãos públicos não cobram taxas por mensagem.", "Consulte só pelos canais oficiais gov.br; o Detran não cobra multa por Pix nem por mensagem."),
         (BCB_SVR, SVR_GOLPE, CNH_SUSPENSA)),
    Scam("G14", "Acesso remoto ao celular (mão fantasma)",
         "Depois de um contato falso de banco ou suporte, a vítima é convencida a instalar um aplicativo de acesso remoto. O golpista passa a controlar o celular e faz transferências.",
         ("Pede para instalar aplicativo", "Fala em proteger ou atualizar a conta", "Aplicativo de suporte ou acesso remoto", "Pede para deixar a tela ligada"),
         "Para concluir a proteção da sua conta, baixe o aplicativo de suporte que vou te enviar e me passe o número de acesso que aparecer na tela.",
         ("Nunca instale aplicativos a pedido de quem entrou em contato com você.", "Bancos não pedem acesso remoto ao seu celular.", "Se instalou, desligue a internet e procure o banco."),
         (FALSA_CENTRAL, FEBRABAN_TOP)),
    Scam("G15", "Golpe do amor (romance virtual)",
         "Após semanas de conversa afetiva com um perfil falso, geralmente alguém que mora longe ou no exterior, surge uma emergência: taxa de alfândega, passagem, doença. O pedido de dinheiro se repete.",
         ("Relacionamento só virtual", "Pessoa no exterior ou em missão", "Emergência que exige dinheiro", "Evita chamada de vídeo"),
         "Meu amor, estou preso na alfândega com o presente que te mandei e preciso pagar uma taxa de R$ 2.000 para liberar. Assim que chegar no Brasil te devolvo tudo.",
         ("Nunca envie dinheiro a quem conheceu apenas pela internet.", "Desconfie de quem evita chamadas de vídeo.", "Converse com alguém de confiança antes de decidir."),
         (CANALTECH_10,)),
    Scam("G16", "Troca ou clonagem de cartão",
         "O golpista troca o cartão da vítima em caixas eletrônicos ou maquininhas, ou um 'motoboy do banco' vai buscar o cartão 'cancelado'. Também há leitura de dados em maquininhas adulteradas e falsos entregadores que cobram uma 'taxa de entrega' na maquininha, digitando um valor muito maior.",
         ("Motoboy vai buscar cartão", "Pede para cortar o cartão e entregar", "Ajuda não solicitada no caixa eletrônico", "Maquininha com visor escondido", "Entregador cobra taxa extra na maquininha"),
         "Seu cartão foi clonado. Um funcionário do banco vai até a sua casa hoje retirar o cartão para perícia. Corte ao meio, sem danificar o chip, e entregue com a senha anotada.",
         ("O banco nunca busca cartão na sua casa nem pede a senha.", "Não aceite ajuda de estranhos no caixa eletrônico.", "Confira o valor e o próprio cartão ao pagar em maquininhas."),
         (FEBRABAN_TOP, CANALTECH_10)),
    Scam("G17", "Falsa regularização do MEI (assessoria ou guia falsa)",
         "E-mail ou WhatsApp com cara de aviso oficial diz que a declaração anual do MEI ou o CNPJ tem 'pendência' e manda 'regularizar' por um link. O site cobra por um serviço que o governo oferece de graça, ou emite guia falsa; às vezes um rodapé em letra pequena diz que a empresa não tem vínculo com a Receita.",
         ("Fala em pendência, irregularidade ou regularização", "Microempreendedor (MEI), declaração anual ou CNPJ", "Link para um site que não é gov.br", "Usa o nome e o CNPJ da empresa da vítima para parecer oficial", "Assessoria privada 'sem vínculo' com o governo"),
         "DECLARAÇÃO ANUAL: seu MEI possui pendência junto à Receita. Evite multa e o cancelamento do CNPJ. Clique em REGULARIZAR e conclua online: mei-regulariza.com.br",
         ("A declaração anual do MEI é gratuita e feita só no Portal do Empreendedor (gov.br) ou no app MEI.", "Consulte pendências digitando gov.br/mei você mesmo, sem clicar no link.", "Não pague assessorias para um serviço gratuito."),
         (SEBRAE_MEI, GOV_DASN)),
    Scam("G18", "Falso advogado ou processo judicial",
         "Com dados reais de processos, o golpista se passa pelo advogado da vítima ou pelo escritório e diz que um valor (indenização, alvará, ação trabalhista) foi liberado, mas exige o pagamento de custas, taxas ou impostos por Pix para liberar.",
         ("Diz ser advogado ou do escritório", "Alvará, indenização ou ação ganha", "Custas ou taxa para liberar o valor", "Pagamento por Pix para pessoa ou empresa", "Contato por número novo"),
         "Boa tarde, sou do escritório que cuida da sua ação contra a operadora. A indenização de R$ 9.800 saiu, mas para liberar o alvará é preciso pagar as custas de R$ 640 por Pix hoje.",
         ("A Justiça não cobra por Pix para liberar valores; custas são pagas por guia oficial.", "Confirme com seu advogado pelo telefone que você já tinha, ou no fórum.", "Não pague nada a quem fala de um número novo."),
         (OAB_ADVOGADO, FEBRABAN_ADVOGADO)),
    Scam("G19", "Falso sequestro",
         "Ligação ou mensagem diz que um parente foi sequestrado, às vezes com choro ou voz parecida ao fundo, e exige transferência imediata, proibindo a vítima de desligar ou chamar a polícia.",
         ("Parente sequestrado ou em perigo", "Ameaça de violência", "Proíbe chamar a polícia ou desligar", "Exige transferência ou Pix imediato"),
         "Estamos com a sua filha. Se desligar ou chamar a polícia, ela não volta. Faz agora um Pix de R$ 3 mil e não fala com ninguém.",
         ("Desligue e ligue para o parente ou para quem está com ele.", "Combine com a família uma palavra de segurança.", "Não faça transferência; chame a polícia pelo 190."),
         (PCPR_SEQUESTRO, SERASA_SEQUESTRO)),
    Scam("G20", "Aluguel ou imóvel falso",
         "Anúncio de imóvel para alugar com preço abaixo do mercado; o 'dono' ou 'corretor' não pode mostrar o imóvel e pede sinal, caução ou reserva por Pix antes da visita e do contrato.",
         ("Preço muito abaixo do mercado", "Dono no exterior ou sem poder mostrar", "Caução ou sinal antes da visita", "Pressa porque há outros interessados", "Promete mandar as chaves pelo correio"),
         "Casa de 3 quartos por R$ 900. Tem muita gente interessada; para garantir, faça hoje o Pix de R$ 500 de reserva e depois marcamos a visita.",
         ("Nunca pague nada antes de visitar o imóvel e assinar o contrato.", "Peça a matrícula do imóvel e confira quem é o dono.", "Pesquise as fotos do anúncio na internet."),
         (SERASA_ALUGUEL, BAND_ALUGUEL)),
    Scam("G21", "Falsa doação ou vaquinha",
         "Depois de uma tragédia (enchente, incêndio) ou usando a história de um doente, golpistas pedem doações por Pix para uma chave pessoal, ou alteram a chave Pix de campanhas verdadeiras.",
         ("Tragédia recente ou pessoa doente", "Apelo emocional e urgência", "Chave Pix pessoal (e-mail, celular, CPF)", "Nome do recebedor diferente da instituição"),
         "Ajude a pequena Laura a fazer a cirurgia! Faltam só R$ 8 mil. Qualquer valor salva uma vida. Pix: ajudalaura2025@gmail.com",
         ("Doe só pelos canais divulgados pelo governo ou pela instituição.", "Antes de confirmar o Pix, confira se o nome do recebedor é o da instituição.", "Desconfie de chaves Pix de e-mail pessoal ou celular."),
         (GOV_DOACAO, SANTANDER_DOACAO)),
    Scam("G22", "Falso médico ou hospital",
         "Com dados reais de um paciente internado, o golpista liga ou manda mensagem se passando por médico ou pelo hospital e diz que é preciso pagar por Pix um exame, remédio ou procedimento urgente que o hospital 'não cobre'.",
         ("Diz ser médico ou do hospital", "Parente internado ou em cirurgia", "Exame, remédio ou procedimento urgente", "Pagamento por Pix para pessoa física", "Pede segredo ou pressa"),
         "Boa tarde, sou o Dr. Paulo, plantonista da UTI. Seu pai precisa de um exame de urgência que o hospital não cobre. Para não atrasar, faça o Pix de R$ 2.300 para o laboratório agora.",
         ("Hospitais não cobram exames por Pix por mensagem.", "Ligue para o hospital pelo número oficial e confirme com a equipe.", "Não pague antes de falar pessoalmente com o hospital."),
         (MEDICO_CANALTECH, MEDICO_BAND)),
    Scam("G23", "Extorsão por e-mail (falso vídeo íntimo)",
         "E-mail ou mensagem diz que o seu computador ou celular foi invadido e que você foi gravado pela câmera em momento íntimo, às vezes citando uma senha antiga vazada, e exige pagamento em bitcoin ou Pix para não divulgar o vídeo.",
         ("Diz ter invadido o computador ou a câmera", "Ameaça divulgar vídeo íntimo", "Cita uma senha antiga sua", "Pagamento em bitcoin ou Pix com prazo"),
         "Eu hackeei seu dispositivo e gravei você pela câmera enquanto assistia a sites adultos. Pague R$ 2.500 em bitcoin em 48 horas ou envio o vídeo para todos os seus contatos.",
         ("É quase sempre um blefe: não responda nem pague.", "Troque a senha citada em todas as contas em que ela foi usada.", "Se houver ameaça real, registre boletim de ocorrência."),
         (SEXTORSAO_ESET, SEXTORSAO_TECNOBLOG)),
    Scam("G24", "Falso intermediário em venda de carro ou objeto",
         "O golpista copia o anúncio verdadeiro de um carro ou objeto, negocia com o comprador e com o dono ao mesmo tempo e faz o comprador depositar o dinheiro na conta dele, pedindo que ninguém fale de valores na hora da visita.",
         ("Preço abaixo do mercado", "Diz ser parente ou sócio do dono", "Pede depósito em conta de terceiro", "Pede para não falar de valores na visita", "Negocia fora do chat da plataforma"),
         "O carro é do meu primo, eu que estou vendendo. Na visita não comenta valor com ele, pois é uma dívida de família. Faz o depósito na minha conta que já libero o documento.",
         ("Pague só ao dono do bem, em conta no nome dele.", "Converse sobre valores com o vendedor na frente de todos.", "Mantenha a conversa no chat da plataforma."),
         (INTERMEDIARIO_SERASA, INTERMEDIARIO_MEUTUDO)),
    Scam("G25", "Falso ressarcimento do INSS ou de benefício",
         "Mensagem promete devolver descontos indevidos de aposentadorias ou pagar uma indenização do INSS e manda consultar por um link ou pagar uma taxa para liberar o dinheiro.",
         ("Promete devolução ou indenização do INSS", "Descontos indevidos na aposentadoria", "Link para consultar o direito", "Taxa para liberar o valor", "Pede CPF e dados bancários"),
         "INSS: você tem direito ao ressarcimento de R$ 1.380 de descontos indevidos no seu benefício. Consulte e solicite até sexta: inss-ressarcimento.com",
         ("A consulta é só pelo app ou site Meu INSS ou pela Central 135.", "Sites do governo terminam em .gov.br.", "O INSS não cobra taxa para devolver valores."),
         (INSS_GOV, INSS_CANALTECH)),
    Scam("G26", "Ingresso falso",
         "Perfis em redes sociais ou sites falsos vendem ingressos para shows, jogos e festas, geralmente esgotados, recebem por Pix e não entregam, ou entregam ingressos falsos ou já usados.",
         ("Ingresso de evento esgotado", "Venda por rede social ou WhatsApp", "Pagamento só por Pix", "Preço fora do normal", "Não transfere o ingresso para o seu nome"),
         "Tenho 2 ingressos para o show de sábado, pista premium, faço os dois por R$ 500 porque não vou poder ir. Só Pix, te mando o QR code do ingresso por aqui.",
         ("Compre só no site oficial ou na bilheteria.", "Na revenda, use plataformas que transferem o ingresso para o seu CPF.", "Desconfie de quem só aceita Pix."),
         (INGRESSO_SERASA, INGRESSO_CNN)),
    Scam("G27", "Falsa renegociação de dívida",
         "Usando o nome do Desenrola, da Serasa ou de bancos, golpistas oferecem quitar dívidas com descontos enormes por um link ou boleto, ou cobram uma taxa para entrar no programa.",
         ("Desconto enorme para quitar dívida", "Nome do Desenrola, Serasa ou banco", "Link ou boleto enviado por mensagem", "Taxa para participar do programa"),
         "Desenrola Brasil: sua dívida de R$ 4.300 pode ser quitada por R$ 129,90. Oferta válida só hoje. Gere o boleto em desenrola-quitacao.com",
         ("Não há taxa para participar do Desenrola.", "Negocie só pelo app ou site do credor ou da Serasa, digitando o endereço.", "Confira o beneficiário antes de pagar qualquer boleto."),
         (DIVIDA_SERASA, DIVIDA_OLHAR)),
    Scam("G28", "QR code de pagamento adulterado",
         "O golpista troca o QR code de pagamento por um dele: adesivo por cima do código em bares, feiras e estacionamentos, boleto alterado ou QR code enviado por mensagem. O dinheiro vai para outra pessoa.",
         ("QR code colado por cima ou enviado por mensagem", "Nome do recebedor diferente da empresa", "Boleto com QR code diferente", "Pede para pagar rápido sem conferir"),
         "Para pagar a conta da mesa, use o novo QR code que mandamos aqui, o da maquininha está com problema. Pode pagar direto pelo Pix.",
         ("Antes de confirmar, confira no app o nome do recebedor e o valor.", "Desconfie de adesivos colados sobre o QR code.", "Prefira o QR code gerado na maquininha ou no app da empresa."),
         (QRCODE_JC, QRCODE_CANALTECH)),
    Scam("G29", "Consórcio contemplado falso",
         "Anúncios oferecem cartas de consórcio 'já contempladas' para comprar carro ou casa na hora, por preço muito baixo, e pedem uma entrada ou taxa por Pix; a carta não existe.",
         ("Carta de consórcio já contemplada", "Crédito liberado na hora", "Entrada ou taxa por Pix", "Empresa não autorizada pelo Banco Central"),
         "Carta de consórcio CONTEMPLADA de R$ 80 mil para carro, liberação imediata! Basta pagar a entrada de R$ 3.500 hoje e transferimos a cota para o seu nome.",
         ("Confira se a administradora é autorizada pelo Banco Central.", "Confirme a cota direto com a administradora.", "Não pague entrada para pessoas ou contas de terceiros."),
         (CONSORCIO_SERASA, CONSORCIO_OLHAR)),
    Scam("G30", "Falsa cobrança de reserva de hotel",
         "Depois de uma reserva real, a vítima recebe mensagem pelo WhatsApp, e-mail ou até pelo chat da plataforma, com os dados corretos da hospedagem, dizendo que houve problema no pagamento e pedindo para pagar de novo ou 'confirmar o cartão' por um link.",
         ("Cita a reserva, as datas e o hotel corretos", "Problema no pagamento", "Link para confirmar cartão ou pagar de novo", "Ameaça de cancelar a reserva"),
         "Olá, aqui é do Hotel Praia Azul. Sua reserva de 20/12 será cancelada porque o pagamento não foi aprovado. Confirme o cartão em até 12h neste link: reserva-confirmacao.com",
         ("Confira a reserva só pelo app ou site da plataforma.", "Ligue para o hotel pelo telefone do site oficial.", "Não informe dados do cartão por links recebidos."),
         (RESERVA_CANALTECH, RESERVA_TECNOBLOG)),
)

BY_ID = {scam.id: scam for scam in CATALOG}


def catalog_chunks() -> list[Chunk]:
    return [Chunk(id=scam.id, page=index, text=scam.index_text(), location_label="Golpe")
            for index, scam in enumerate(CATALOG, start=1)]
