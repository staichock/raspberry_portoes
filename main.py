#!/usr/bin/env python
import RPi.GPIO as GPIO
import requests
from tkinter import *
import time
import os

# Importamos nossos módulos de configuração e comunicação
from config import parametros
from core import comunicacao

# --- Configuração física dos Pinos do Raspberry ---
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(38, GPIO.OUT)

class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.strVar = ""
        self.txtcolegio = "COLEGIO SANTO ANJO - REGISTRO \n\n"
        
        # --- Interface Grafica ---
        self.photo = PhotoImage(file=parametros.imagemlogo)
        self.lbl = Label(text="", width=60, height=20, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lbl.place(x=0, y=0)
        
        self.labelphoto = Label(image=self.photo, bg='#222B59')
        self.labelphoto.place(x=0, y=0)
        
        self.lblmsgacesso = Label(text="", width=60, height=2, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lblmsgacesso.place(x=0, y=250)

        # Inicia os loops automáticos de Data/Hora e Manutenção (Sync/Heartbeat)
        self.atualizadatahora()
        self.ciclo_manutencao() 

    def atualizadatahora(self):
        self.localtime = time.strftime("%d-%m-%Y %H:%M:%S")
        self.lbl.configure(text=self.txtcolegio + self.localtime)
        self.master.after(1000, self.atualizadatahora)

    def ciclo_manutencao(self):
        """ Roda em segundo plano a cada 60 segundos. """
        comunicacao.enviar_heartbeat(parametros.unidade_logica, parametros.localizacao, parametros.ip_central)
        comunicacao.sincronizar_offline(parametros.unidade_logica, parametros.ip_central)
        self.master.after(60000, self.ciclo_manutencao)

    def telainicial(self):
        self.lbl.configure(bg='#222B59', fg='#fdfd49')
        self.lblmsgacesso.configure(text="", bg='#222B59')
        self.labelphoto.configure(bg='#222B59')

    def keyup(self, e):
        # Captura o final da leitura do crachá (Enter/Return)
        if e.keysym in ("Return", "KP_Enter") or e.char == '\r':
            if self.strVar:
                if parametros.leitor == 1:
                    self.valida_e_registra()
                else:
                    self.registra()
                self.strVar = "" # Limpa o buffer para a próxima leitura
        else:
            # Adiciona ao buffer apenas se for número
            if e.char.isdigit():
                self.strVar += e.char

    def valida_e_registra(self):
        try:
            # Lógica de conversão Wiegand (10 dígitos para 8)
            aba10 = int(self.strVar.lstrip('0'))
            step1 = aba10 // 65536
            step2 = aba10 - (step1 * 65536)
            self.strVar = str(str(step1) + str(step2).rjust(5, '0')).rjust(8, '0')
            self.registra()
        except:
            self.strVar = ""

    def registra(self):
        # --- NOVO: Lógica de Acesso Restrito (Whitelist Local) ---
        if hasattr(parametros, 'acesso_restrito') and parametros.acesso_restrito:
            if self.strVar not in parametros.crachas_autorizados:
                print(f"BLOQUEIO: Crachá {self.strVar} não está na lista de autorizados deste ponto.")
                self.negar()
                return # Interrompe o processo aqui mesmo

        # Se não for restrito ou se o crachá estiver na lista, segue para o TOTVS
        urlTOTVS = f"http://172.16.0.71/ac_registers/rest/{parametros.ponto}/{self.strVar}/{parametros.codevento}"
        
        try:
            # 1. Tenta o servidor principal (TOTVS)
            r = requests.post(urlTOTVS, timeout=2)
            res_split = r.text.split('"')
            status_acesso = res_split[19]
            nome_pessoa = res_split[7]
        except:
            # 2. Em caso de falha de rede, busca no Cache Offline local
            nome_offline = comunicacao.verificar_cache_offline(self.strVar)
            if nome_offline:
                status_acesso = "Acesso liberado"
                nome_pessoa = nome_offline + " (MODO OFFLINE)"
            else:
                status_acesso = "Acesso Negado"
                nome_pessoa = ""

        if status_acesso == "Acesso liberado":
            self.liberar(nome_pessoa)
        else:
            self.negar()

    def liberar(self, nome):
        GPIO.output(38, GPIO.HIGH) # Abre o portão
        self.lbl.configure(bg='green')
        self.lblmsgacesso.configure(text=f"ACESSO LIBERADO \n\n{nome}", bg='green')
        self.labelphoto.configure(bg='green')
        
        # Mantém o relé aberto conforme o tempo configurado
        self.master.after(int(parametros.tempoAcionamentoRele * 1000), self.outLow)
        # Retorna à tela inicial após 3 segundos
        self.master.after(3000, self.telainicial)

    def negar(self):
        self.lbl.configure(bg='red')
        self.lblmsgacesso.configure(text="ACESSO NEGADO", bg='red')
        self.labelphoto.configure(bg='red')
        self.master.after(3000, self.telainicial)

    def outLow(self):
        GPIO.output(38, GPIO.LOW) # Fecha o portão

if __name__ == "__main__":
    root = Tk()
    app = App(root)
    
    # Vinculamos o evento de tecla diretamente no root (janela principal)
    root.bind("<Key>", app.keyup)
    
    # Configurações de exibição e Foco
    root.attributes('-fullscreen', True)
    root.focus_force() 
    
    root.mainloop()