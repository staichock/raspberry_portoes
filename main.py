#!/usr/bin/env python
import RPi.GPIO as GPIO
import requests
from tkinter import *
import time
import os

# Importamos nossos módulos de configuração e comunicação
from config import parametros
from core import comunicacao

# Configuração de GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(38, GPIO.OUT)

class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.strVar = ""
        self.txtcolegio = "COLEGIO SANTO ANJO - REGISTRO \n\n"
        
        # --- Interface Gráfica ---
        # Vincula a captura de teclas à janela principal (root) para não perder o foco
        self.master.bind("<Key>", self.keyup)
        
        self.photo = PhotoImage(file=parametros.imagemlogo)
        
        # Label de Fundo / Data e Hora
        self.lbl = Label(text="", width=60, height=20, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lbl.place(x=0, y=0)
        
        # Label da Logo
        self.labelphoto = Label(image=self.photo, bg='#222B59')
        self.labelphoto.place(x=0, y=0)
        
        # Label de Mensagem de Acesso
        self.lblmsgacesso = Label(text="", width=60, height=2, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lblmsgacesso.place(x=0, y=250)

        # Garante que a janela tenha o foco do teclado imediatamente
        self.master.after(100, self.forcar_foco)

        # Inicia os loops automáticos
        self.atualizadatahora()
        self.ciclo_manutencao() 

    def forcar_foco(self):
        """ Força o foco na janela para o leitor USB funcionar de cara """
        self.master.focus_force()

    def atualizadatahora(self):
        self.localtime = time.strftime("%d-%m-%Y %H:%M:%S")
        self.lbl.configure(text=self.txtcolegio + self.localtime)
        self.master.after(1000, self.atualizadatahora)

    def ciclo_manutencao(self):
        """ Heartbeat para a Central e Sincronização de Crachás """
        comunicacao.enviar_heartbeat(parametros.unidade_logica, parametros.ip_central)
        comunicacao.sincronizar_offline(parametros.unidade_logica, parametros.ip_central)
        # Repete a cada 60 segundos
        self.master.after(60000, self.ciclo_manutencao)

    def telainicial(self):
        """ Reseta a tela para o padrão azul """
        self.lbl.configure(bg='#222B59', fg='#fdfd49')
        self.lblmsgacesso.configure(text="", bg='#222B59')
        self.labelphoto.configure(bg='#222B59')

    def keyup(self, e):
        """ Captura a entrada do leitor (teclado USB) """
        # Verifica se a tecla pressionada é um "Enter" (\r ou a tecla Return/Enter)
        if e.keysym in ("Return", "KP_Enter") or repr(e.char) == "'\\r'":
            if self.strVar: # Só processa se houver algo no buffer
                if parametros.leitor == 1:
                    self.valida_e_registra()
                else:
                    self.registra()
                self.strVar = "" # Limpa para a próxima leitura
        else:
            # Filtra apenas caracteres válidos (números/letras) e ignora teclas como Shift/Alt
            if len(e.char) == 1:
                self.strVar += e.char

    def valida_e_registra(self):
        """ Conversão de 10 dígitos (Padrão Wiegand/Aba) """
        try:
            aba10 = int(self.strVar.lstrip('0'))
            step1 = aba10 // 65536
            step2 = aba10 - (step1 * 65536)
            self.strVar = str(str(step1) + str(step2).rjust(5, '0')).rjust(8, '0')
            self.registra()
        except:
            self.strVar = ""

    def registra(self):
        """ Lógica principal de validação (Online com Fallback Offline) """
        urlTOTVS = f"http://172.16.0.71/ac_registers/rest/{parametros.ponto}/{self.strVar}/{parametros.codevento}"
        
        try:
            # 1. Tentativa Online (Sistema TOTVS .71)
            r = requests.post(urlTOTVS, timeout=2)
            res_split = r.text.split('"')
            status_acesso = res_split[19]
            nome_pessoa = res_split[7]
        except:
            # 2. Tentativa Offline (Cache Local) se a rede ou o sistema .71 falhar
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
        """ Aciona relé e atualiza interface para Verde """
        GPIO.output(38, GPIO.HIGH)
        self.lbl.configure(bg='green')
        self.lblmsgacesso.configure(text=f"ACESSO LIBERADO \n\n{nome}", bg='green')
        self.labelphoto.configure(bg='green')
        
        # Tempo de abertura conforme parametros.py
        self.master.after(int(parametros.tempoAcionamentoRele * 1000), self.outLow)
        # Retorna à tela inicial após 3 segundos
        self.master.after(3000, self.telainicial)

    def negar(self):
        """ Atualiza interface para Vermelho """
        self.lbl.configure(bg='red')
        self.lblmsgacesso.configure(text="ACESSO NEGADO", bg='red')
        self.labelphoto.configure(bg='red')
        self.master.after(3000, self.telainicial)

    def outLow(self):
        """ Desliga o pulso do relé """
        GPIO.output(38, GPIO.LOW)

if __name__ == "__main__":
    root = Tk()
    # Remove a barra de títulos e coloca em tela cheia
    root.attributes('-fullscreen', True)
    # Esconde o cursor do mouse (opcional, bom para totens)
    # root.config(cursor="none")
    
    app = App(root)
    root.mainloop()