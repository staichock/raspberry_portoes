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

# --- LÓGICA DE CAMINHO ABSOLUTO ---
# Isso descobre a pasta real onde o script está, independente de como foi iniciado
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DATA = os.path.join(BASE_DIR, "data")
ARQUIVO_JSON = os.path.join(PASTA_DATA, "crachas_contingencia.json")

def sincronizar_offline(unidade, ip_central):
    """ Baixa a lista de crachás e garante a criação da pasta no local correto """
    try:
        # 1. Tenta criar a pasta usando o caminho absoluto
        if not os.path.exists(PASTA_DATA):
            os.makedirs(PASTA_DATA, exist_ok=True)
            print(f"📂 Pasta criada em: {PASTA_DATA}")

        url = f"http://{ip_central}:8000/sync_offline/{unidade}"
        r = requests.get(url, timeout=5)
        
        if r.status_code == 200:
            dados = r.json()
            
            # 2. Grava o arquivo usando o caminho absoluto
            with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Sync OK: {len(dados)} crachás salvos em {ARQUIVO_JSON}")
            return True
        else:
            print(f"⚠️ Erro Central: Status {r.status_code}")
            return False

    except Exception as e:
        print(f"❌ Falha Crítica no Sync: {e}")
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