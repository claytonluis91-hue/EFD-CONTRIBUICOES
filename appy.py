import streamlit as st
import pandas as pd
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Leitor EFD Contribuições", layout="wide")

def parse_efd_to_dict(file_content):
    """
    Lê o conteúdo do arquivo TXT e agrupa os registros em um dicionário.
    Cada chave é um bloco (ex: '0150') e o valor é uma lista de listas (linhas).
    """
    data_dict = {}
    
    # Decodifica o conteúdo (usando latin-1 para evitar erro em caracteres especiais)
    lines = file_content.decode("latin-1").splitlines()
    
    for linha in lines:
        # O SPED usa o pipe | como delimitador
        campos = linha.strip().split('|')
        
        # Registros válidos no SPED começam e terminam com |, gerando campos vazios nas pontas
        if len(campos) > 2:
            registro_id = campos[1]
            # Extraímos os dados entre os pipes principais
            conteudo_registro = campos[1:-1]
            
            if registro_id not in data_dict:
                data_dict[registro_id] = []
            
            data_dict[registro_id].append(conteudo_registro)
            
    return data_dict

def to_excel(data_dict):
    """
    Gera um arquivo Excel em memória com cada registro em uma aba separada.
    """
    output = BytesIO()
    # Engine xlsxwriter é ideal para manipular múltiplas abas e formatação
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for reg_id in sorted(data_dict.keys()):
            # Criamos um DataFrame para o bloco específico
            df = pd.DataFrame(data_dict[reg_id])
            
            # O Excel permite nomes de abas com no máximo 31 caracteres
            nome_aba = f"Bloco_{reg_id}"
            
            # Exporta para o Excel sem o índice do pandas e sem cabeçalho (padrão SPED)
            df.to_excel(writer, sheet_name=nome_aba, index=False, header=False)
            
            # Ajuste automático simples da largura das colunas
            worksheet = writer.sheets[nome_aba]
            for i, col in enumerate(df.columns):
                worksheet.set_column(i, i, 18)
                
    return output.getvalue()

# --- Interface do Streamlit ---

st.title("📂 Analisador EFD Contribuições")
st.markdown("Converta seu arquivo TXT para Excel com abas separadas por bloco de registro.")

# Upload do arquivo
arquivo_upload = st.file_uploader("Arraste seu arquivo TXT aqui", type=["txt"])

if arquivo_upload:
    with st.spinner('Processando os dados...'):
        # 1. Lê e organiza os dados
        conteudo = arquivo_upload.read()
        registros_agrupados = parse_efd_to_dict(conteudo)
        
        if registros_agrupados:
            st.success(f"Sucesso! Identificamos {len(registros_agrupados)} tipos de registros diferentes.")
            
            # 2. Prepara o Excel para download
            dados_excel = to_excel(registros_agrupados)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Baixar Planilha Excel",
                    data=dados_excel,
                    file_name=f"Analise_{arquivo_upload.name.replace('.txt', '')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # 3. Visualização Prévia no Streamlit
            st.divider()
            st.subheader("Pré-visualização dos Blocos")
            
            escolha = st.selectbox(
                "Selecione um registro para visualizar os dados:",
                options=sorted(registros_agrupados.keys()),
                format_func=lambda x: f"Registro {x}"
            )
            
            if escolha:
                df_preview = pd.DataFrame(registros_agrupados[escolha])
                st.dataframe(df_preview, use_container_width=True)
        else:
            st.error("Não foi possível identificar registros válidos no arquivo.")
