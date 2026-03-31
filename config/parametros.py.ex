#!/usr/bin/env python

# --- Configurações Originais ---

tempoAcionamentoRele = 2
ponto = "46"                # Ponto criado no filaescola
codevento = "0"            # 0-Saida, 1-Entrada
leitor = 1                  # 1-Novo (10 dig), 0-Antigo
imagemlogo = "/home/pi/raspberry_portoes/assets/logo.png"
# --- Configuração do novo DASHBOARD Central ---

unidade_logica = "BARIGUI"
ip_central = "172.16.0.196" # IP da Central

# Se for True, apenas os crachás na lista abaixo abrem o portão
acesso_restrito = False

# Lista de crachás autorizados (coloque os números de 8 dígitos)
crachas_autorizados = [
    "00123456", 
    "00887766",
    "00554433"
]

