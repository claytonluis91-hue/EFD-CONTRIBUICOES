import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Portal Fiscal - EFD", layout="wide")

def parse_efd_to_dict(file_content):
    """Lê o TXT, para no bloco 9999 para evitar a assinatura digital e normaliza as colunas."""
    data_dict = {}
    
    # Usando errors='ignore' para não quebrar a leitura se a assinatura digital tiver bytes inválidos
    lines = file_content.decode("latin-1", errors="ignore").splitlines()
    
    for linha in lines:
        # Garante que só vamos ler linhas que comecem com o padrão SPED
        if linha.startswith('|'):
            campos = linha.strip().split('|')
            
            if len(campos) > 2:
                reg_id = campos[1]
                conteudo = campos[1:-1]
                
                if reg_id not in data_dict:
                    data_dict[reg_id] = []
                data_dict[reg_id].append(conteudo)
                
                # A MÁGICA AQUI: Se for o registro 9999, o arquivo fiscal acabou.
                # O comando 'break' interrompe a leitura e ignora a assinatura digital.
                if reg_id == '9999':
                    break
    
    # Normalização: Garante que todas as linhas de um bloco tenham o mesmo número de colunas
    dfs_prontos = {}
    for reg, listas in data_dict.items():
        max_cols = max(len(l) for l in listas)
        # Preenche com string vazia as colunas faltantes para deixar a tabela quadrada
        listas_normalizadas = [l + [''] * (max_cols - len(l)) for l in listas]
        
        # Cria o DataFrame com nomes de colunas genéricos (Campo_0, Campo_1...)
        df = pd.DataFrame(listas_normalizadas)
        df.columns = [f'Campo_{i}' for i in range(max_cols)]
        dfs_prontos[reg] = df
        
    return dfs_prontos

def to_excel(dfs_dict):
    """Gera o Excel com abas separadas."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for reg_id in sorted(dfs_dict.keys()):
            df = dfs_dict[reg_id]
            nome_aba = f"Bloco_{reg_id}"
            
            df.to_excel(writer, sheet_name=nome_aba, index=False)
            
            worksheet = writer.sheets[nome_aba]
            worksheet.freeze_panes(1, 0)
            for i, col in enumerate(df.columns):
                worksheet.set_column(i, i, 15)
                
    return output.getvalue()

# --- Interface ---
st.title("📂 Analisador Fiscal EFD")
st.info("Otimizado para leitura de arquivos SPED (ignora assinatura digital).")

arquivo_upload = st.file_uploader("Selecione o arquivo TXT", type=["txt"])

if arquivo_upload:
    with st.spinner('Lendo estruturas e removendo assinatura digital...'):
        conteudo = arquivo_upload.read()
        dfs_validados = parse_efd_to_dict(conteudo)
        
        if dfs_validados:
            st.success(f"Arquivo lido com sucesso! {len(dfs_validados)} blocos extraídos.")
            
            # Download
            excel_data = to_excel(dfs_validados)
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_data,
                file_name=f"EFD_Processado_{arquivo_upload.name.replace('.txt', '')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.divider()
            
            bloco = st.selectbox("Selecione o bloco para conferência prévia:", sorted(dfs_validados.keys()))
            
            if bloco:
                st.write(f"### Detalhes do Registro {bloco}")
                st.dataframe(dfs_validados[bloco], use_container_width=True)
        else:
            st.error("Erro ao processar a estrutura do arquivo. Verifique se é um arquivo SPED válido.")
