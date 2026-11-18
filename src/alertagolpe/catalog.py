"""Catálogo de golpes conhecidos no Brasil, usado como base de conhecimento (RAG).

Descrições compiladas a partir de alertas públicos de bancos, da Febraban, do
Banco Central e da imprensa (ver campo ``fontes``). Redigido com assistência de
IA e sujeito à revisão do grupo. As mensagens de exemplo são fictícias.
"""

from dataclasses import dataclass

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
        return " ".join([self.nome, self.como_funciona, *self.sinais, self.exemplo])


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
    Scam("G03", "Link falso de banco ou cartão (phishing)",
         "Mensagem por SMS, e-mail ou WhatsApp imita o banco, informa bloqueio, pontos a vencer ou atualização cadastral e leva a um site falso que captura senha e dados do cartão.",
         ("Link encurtado ou com endereço estranho", "Bloqueio de conta ou cartão", "Pontos ou milhas prestes a vencer", "Pede atualização de cadastro", "Pede dados do cartão ou senha"),
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
         "Mensagem em nome da Receita Federal, do INSS, do governo ou do Banco Central fala em CPF irregular, restituição, benefício ou 'valores a receber' e pede dados, taxa ou clique em link.",
         ("Nome de órgão público ou Banco Central", "CPF irregular ou bloqueado", "Valores esquecidos ou benefício a receber", "Link para consulta ou regularização", "Taxa para liberar valor"),
         "Banco Central: você possui R$ 1.874,32 em valores a receber esquecidos. Resgate até amanhã informando seu CPF no link: valores-receber-bc.site",
         ("O único site de valores a receber é valoresareceber.bcb.gov.br; o Banco Central não envia links.", "Órgãos públicos não cobram taxas por mensagem.", "Consulte só pelos canais oficiais gov.br."),
         (BCB_SVR, SVR_GOLPE)),
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
         "O golpista troca o cartão da vítima em caixas eletrônicos ou maquininhas, ou um 'motoboy do banco' vai buscar o cartão 'cancelado'. Também há leitura de dados em maquininhas adulteradas.",
         ("Motoboy vai buscar cartão", "Pede para cortar o cartão e entregar", "Ajuda não solicitada no caixa eletrônico", "Maquininha com visor escondido"),
         "Seu cartão foi clonado. Um funcionário do banco vai até a sua casa hoje retirar o cartão para perícia. Corte ao meio, sem danificar o chip, e entregue com a senha anotada.",
         ("O banco nunca busca cartão na sua casa nem pede a senha.", "Não aceite ajuda de estranhos no caixa eletrônico.", "Confira o valor e o próprio cartão ao pagar em maquininhas."),
         (FEBRABAN_TOP, CANALTECH_10)),
    Scam("G17", "Falsa regularização do MEI (assessoria ou guia falsa)",
         "E-mail ou WhatsApp com cara de aviso oficial diz que a declaração anual do MEI ou o CNPJ tem 'pendência' e manda 'regularizar' por um link. O site cobra por um serviço que o governo oferece de graça, ou emite guia falsa; às vezes um rodapé em letra pequena diz que a empresa não tem vínculo com a Receita.",
         ("Fala em pendência, irregularidade ou regularização", "Microempreendedor (MEI), declaração anual ou CNPJ", "Link para um site que não é gov.br", "Usa o nome e o CNPJ da empresa da vítima para parecer oficial", "Assessoria privada 'sem vínculo' com o governo"),
         "DECLARAÇÃO ANUAL: seu MEI possui pendência junto à Receita. Evite multa e o cancelamento do CNPJ. Clique em REGULARIZAR e conclua online: mei-regulariza.com.br",
         ("A declaração anual do MEI é gratuita e feita só no Portal do Empreendedor (gov.br) ou no app MEI.", "Consulte pendências digitando gov.br/mei você mesmo, sem clicar no link.", "Não pague assessorias para um serviço gratuito."),
         (SEBRAE_MEI, GOV_DASN)),
)

BY_ID = {scam.id: scam for scam in CATALOG}


def catalog_chunks() -> list[Chunk]:
    return [Chunk(id=scam.id, page=index, text=scam.index_text(), location_label="Golpe")
            for index, scam in enumerate(CATALOG, start=1)]
