import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Leitor EFD Contribuições", layout="wide")

def parse_efd_to_df(file_content):
    """Lê o conteúdo do arquivo e retorna um dicionário de DataFrames por registro."""
    data_dict = {}
    
    # Decodifica o conteúdo do arquivo enviado
    lines = file_content.decode("latin-1").splitlines()
    
    for linha in lines:
        campos = linha.strip().split('|')
        if len(campos) > 2:
            reg = campos[1]
            # Limpa os campos vazios das extremidades do split
            dados = campos[1:-1]
            
            if reg not in data_dict:
                data_dict[reg] = []
            data_dict[reg].append(dados)
    
    # Converte cada lista de registros em um DataFrame do Pandas
    dfs = {reg: pd.DataFrame(lista) for reg, lista in data_dict.items()}
    return dfs

def to_excel(dfs):
    """Gera um arquivo Excel em memória com múltiplas abas."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for reg, df in dfs.items():
            # Nome da aba no Excel (limite de 31 caracteres)
            df.to_sheet_name = f"Registro_{reg}"
            df.to_excel(writer, sheet_name=df.to_sheet_name, index=False, header=False)
    return output.getvalue()

# Interface Streamlit
st.title("📂 Analisador de EFD Contribuições")
st.subheader("Extração de blocos e exportação para Excel")

uploaded_file = st.file_uploader("Selecione o arquivo TXT da EFD", type=["txt"])

if uploaded_file:
    with st.spinner('Processando arquivo...'):
        # Processamento
        conteudo = uploaded_file.read()
        dict_dfs = parse_efd_to_df(conteudo)
        
        if dict_dfs:
            st.success(f"Arquivo processado com sucesso! {len(dict_dfs)} tipos de registros encontrados.")
            
            # Botão de Download para Excel
            excel_data = to_excel(dict_dfs)
            st.download_button(
                label="📥 Baixar tudo em Excel (.xlsx)",
                data=excel_data,
                file_name=f"EFD_Processado_{uploaded_file.name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Visualização no Streamlit
            st.divider()
            registro_selecionado = st.selectbox("Selecione um registro para visualizar:", sorted(dict_dfs.keys()))
            
            if registro_selecionado:
                st.write(f"Exibindo dados do Registro {registro_selecionado}")
                st.dataframe(dict_dfs[registro_selecionado], use_container_width=True)
