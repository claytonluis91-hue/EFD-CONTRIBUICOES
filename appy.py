import os

def ler_blocos_efd(caminho_arquivo):
    """
    Lê um arquivo da EFD Contribuições e agrupa os registros por bloco/tipo.
    """
    blocos_dados = {}
    
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado.")
        return None

    try:
        with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
            for linha in arquivo:
                # Remove espaços em branco e divide a linha pelo delimitador '|'
                campos = linha.strip().split('|')
                
                # Registros válidos começam e terminam com '|', resultando em campos vazios nas pontas
                # O identificador do registro (ex: 0000, 0150, C100) fica na posição campos[1]
                if len(campos) > 2:
                    registro_id = campos[1]
                    
                    if registro_id not in blocos_dados:
                        blocos_dados[registro_id] = []
                    
                    # Armazena os dados do registro (removendo os vazios das pontas)
                    blocos_dados[registro_id].append(campos[1:-1])
                    
        return blocos_dados
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo: {e}")
        return None

# --- Exemplo de Uso ---
arquivo_txt = 'DRT.txt'  # Certifique-se de que o arquivo está na mesma pasta
dados_extraidos = ler_blocos_efd(arquivo_txt)

if dados_extraidos:
    # Exemplo: Lendo dados do cabeçalho (Registro 0000)
    if '0000' in dados_extraidos:
        header = dados_extraidos['0000'][0]
        print(f"Empresa: {header[7]} | CNPJ: {header[8]}") # [cite: 1, 1832, 1833]

    # Exemplo: Listando alguns fornecedores/clientes (Registro 0150)
    print("\n--- Primeiros 5 Participantes (Bloco 0150) ---")
    for participante in dados_extraidos.get('0150', [])[:5]:
        print(f"ID: {participante[1]} | Nome: {participante[2]}") # [cite: 5, 6, 7]

    # Exemplo: Notas Fiscais de Entrada/Saída (Registro C100)
    if 'C100' in dados_extraidos:
        total_notas = len(dados_extraidos['C100'])
        print(f"\nTotal de registros C100 encontrados: {total_notas}")
