import requests
import json
import os

def enviar_heartbeat(unidade, local, ip_central):
    """ Avisa a Central que este Raspberry está vivo e onde ele está """
    try:
        url = f"http://{ip_central}:8000/heartbeat"
        
        # AJUSTE AQUI: Adicionamos o campo "local" no JSON enviado
        dados = {
            "unidade": unidade,
            "local": local
        }
        
        requests.post(url, json=dados, timeout=2)
        return True
    except Exception as e:
        print(f"Erro Heartbeat: {e}")
        return False

def sincronizar_offline(unidade, ip_central):
    """ Baixa a lista de crachás permitidos na queda de rede """
    try:
        url = f"http://{ip_central}:8000/sync_offline/{unidade}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            # Garante que a pasta data existe para salvar o cache
            if not os.path.exists("data"): 
                os.makedirs("data")
            
            with open("data/crachas_contingencia.json", "w") as f:
                json.dump(r.json(), f)
            return True
    except Exception as e:
        print(f"Erro Sync: {e}")
        return False

def verificar_cache_offline(cartao_lido):
    """ Busca o nome do colaborador no arquivo local caso o servidor caia """
    try:
        caminho = "data/crachas_contingencia.json"
        if os.path.exists(caminho):
            with open(caminho, "r") as f:
                cache = json.load(f)
                for item in cache:
                    if item['cartao'] == cartao_lido:
                        return item['nome']
    except Exception as e:
        print(f"Erro Leitura Cache: {e}")
    return None