#!/usr/bin/env python
import RPi.GPIO as GPIO
import requests
from tkinter import *
import time
import os

# Importamos nossos módulos de configuração e comunicação
from config import parametros
from core import comunicacao

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
        self.frame = Frame(width=1, height=1)
        self.frame.bind("<Key>", self.keyup)
        self.frame.pack()
        self.frame.focus_set()
        
        self.photo = PhotoImage(file=parametros.imagemlogo)
        self.lbl = Label(text="", width=60, height=20, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lbl.place(x=0, y=0)
        
        self.labelphoto = Label(image=self.photo, bg='#222B59')
        self.labelphoto.place(x=0, y=0)
        
        self.lblmsgacesso = Label(text="", width=60, height=2, bg='#222B59', fg='#fdfd49', font=("Helvetica", 12))
        self.lblmsgacesso.place(x=0, y=250)

        # Inicia os loops automáticos
        self.atualizadatahora()
        self.ciclo_manutencao() 

    def atualizadatahora(self):
        self.localtime = time.strftime("%d-%m-%Y %H:%M:%S")
        self.lbl.configure(text=self.txtcolegio + self.localtime)
        self.master.after(1000, self.atualizadatahora)

    def ciclo_manutencao(self):
        """ 
        Roda em segundo plano. 
        Envia o sinal de vida (Heartbeat) e baixa os crachás (Sync)
        """
        # Chamando as funções que estão dentro de core/comunicacao.py
        comunicacao.enviar_heartbeat(parametros.unidade_logica, parametros.ip_central)
        comunicacao.sincronizar_offline(parametros.unidade_logica, parametros.ip_central)
        
        # Repete a cada 60 segundos
        self.master.after(60000, self.ciclo_manutencao)

    def telainicial(self):
        self.lbl.configure(bg='#222B59', fg='#fdfd49')
        self.lblmsgacesso.configure(text="", bg='#222B59')
        self.labelphoto.configure(bg='#222B59')

    def keyup(self, e):
        if repr(e.char) == "'\\r'":
            if parametros.leitor == 1:
                self.valida_e_registra()
            else:
                self.registra()
            self.strVar = ""
        else:
            self.strVar += e.char

    def valida_e_registra(self):
        try:
            # Lógica de conversão para leitores de 10 dígitos
            aba10 = int(self.strVar.lstrip('0'))
            step1 = aba10 // 65536
            step2 = aba10 - (step1 * 65536)
            self.strVar = str(str(step1) + str(step2).rjust(5, '0')).rjust(8, '0')
            self.registra()
        except:
            self.strVar = ""

    def registra(self):
        urlTOTVS = f"http://172.16.0.71/ac_registers/rest/{parametros.ponto}/{self.strVar}/{parametros.codevento}"
        
        try:
            # 1. Tenta o sistema principal (TOTVS na rede .71)
            r = requests.post(urlTOTVS, timeout=2)
            res_split = r.text.split('"')
            status_acesso = res_split[19]
            nome_pessoa = res_split[7]
        except:
            # 2. Se falhar, tenta o MODO OFFLINE (Cache Local)
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
        GPIO.output(38, GPIO.HIGH)
        self.lbl.configure(bg='green')
        self.lblmsgacesso.configure(text=f"ACESSO LIBERADO \n\n{nome}", bg='green')
        self.labelphoto.configure(bg='green')
        
        # Mantém o relé aberto conforme o tempo do parâmetro
        self.master.after(int(parametros.tempoAcionamentoRele * 1000), self.outLow)
        # Volta para a tela azul após 3 segundos
        self.master.after(3000, self.telainicial)

    def negar(self):
        self.lbl.configure(bg='red')
        self.lblmsgacesso.configure(text="ACESSO NEGADO", bg='red')
        self.labelphoto.configure(bg='red')
        self.master.after(3000, self.telainicial)

    def outLow(self):
        GPIO.output(38, GPIO.LOW)

if __name__ == "__main__":
    root = Tk()
    app = App(root)
    # Abre em tela cheia
    root.attributes('-fullscreen', True)
    root.mainloop()