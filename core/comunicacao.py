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
        # 1. Tratamos o nome da unidade para a URL (ex: 'SANTA FELICIDADE' vira 'SANTA%20FELICIDADE')
        unidade_url = quote(unidade.upper().strip())
        url = f"http://{ip_central}:8000/sync_offline/{unidade_url}"
        
        r = requests.get(url, timeout=5)
        
        if r.status_code == 200:
            dados_novos = r.json()
            
            # 2. Garante que a pasta data existe
            if not os.path.exists("data"): 
                os.makedirs("data", exist_ok=True)
            
            # 3. Salva o arquivo com indentação para facilitar sua conferência
            caminho = "data/crachas_contingencia.json"
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados_novos, f, ensure_ascii=False, indent=4)
            
            print(f"✅ Sync OK! {len(dados_novos)} crachás salvos para {unidade}")
            return True
        else:
            print(f"❌ Erro na Central: Status {r.status_code} para unidade {unidade}")
            return False
            
    except Exception as e:
        print(f"⚠️ Erro Sync: {e}")
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