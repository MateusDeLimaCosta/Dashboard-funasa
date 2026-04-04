import pandas as pd

def obter_dados_visao_executiva():
    # Agora ele lê direto do arquivo congelado, sem precisar de senha ou internet
    df = pd.read_csv('dados_funasa.csv')
    return df