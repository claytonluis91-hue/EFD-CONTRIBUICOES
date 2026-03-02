import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Portal Fiscal - EFD", layout="wide")

# Mapeamento oficial dos principais blocos da EFD Contribuições
MAPA_BLOCOS = {
    "0000": "Abertura e Identificação",
    "0100": "Dados do Contabilista",
    "0110": "Regimes de Apuração",
    "0140": "Cadastro de Estabelecimento",
    "0150": "Cadastro de Participante",
    "0190": "Unidades de Medida",
    "0200": "Identificação do Item",
    "0400": "Natureza da Operação",
    "0500": "Plano de Contas",
    "A100": "NF de Serviço",
    "A170": "Itens da NF de Serviço",
    "C010": "Identific. Estabelecimento",
    "C100": "NF Entrada e Saída",
    "C170": "Itens da NF",
    "C180": "Consolidação de Notas",
    "C190": "Consolidação de Notas",
    "C395": "Notas Fiscais de Venda",
    "C400": "Equipamento ECF",
    "C405": "Redução Z",
    "C500": "Energia/Água/Gás",
    "D100": "Transporte e Comunicação",
    "F100": "Demais Operações",
    "F200": "Operações Imobiliárias",
    "M200": "Apuração PIS",
    "M400": "Receitas Isentas PIS",
    "M600": "Apuração COFINS",
    "M800": "Receitas Isentas COFINS",
    "1100": "Controle Créditos PIS",
    "1500": "Controle Créditos COFINS",
    "9900": "Totalizadores",
    "9999": "Encerramento"
}

def obter_nome_aba(reg_id):
    """Retorna o nome da aba com limite de 31 caracteres para o Excel."""
    descricao = MAPA_BLOCOS.get(reg_id, f"Bloco_{reg_id}")
    nome_completo = f"{reg_id} - {descricao}"
    return nome_completo[:31] # Corta no limite do Excel

def parse_efd_to_dict(file_content):
    """Lê o TXT, parando no bloco 9999 e normalizando as colunas."""
    data_dict = {}
    
    # errors='ignore' evita quebra com a assinatura digital binária
    lines = file_content.decode("latin-1", errors="ignore").splitlines()
    
    for linha in lines:
        if linha.startswith('|'):
            campos = linha.strip().split('|')
            
            if len(campos) > 2:
                reg_id = campos[1]
                conteudo = campos[1:-1]
                
                if reg_id not in data_dict:
                    data_dict[reg_id] = []
                data_dict[reg_id].append(conteudo)
                
                # Trava para ignorar a assinatura digital no fim do arquivo
                if reg_id == '9999':
                    break
    
    dfs_prontos = {}
    for reg, listas in data_dict.items():
        max_cols = max(len(l) for l in listas)
        listas_normalizadas = [l + [''] * (max_cols - len(l)) for l in listas]
        
        df = pd.DataFrame(listas_normalizadas)
        df.columns = [f'Campo_{i}' for i in range(max_cols)]
        dfs_prontos[reg] = df
        
    return dfs_prontos

def to_excel(dfs_dict):
    """Gera o Excel com abas renomeadas."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for reg_id in sorted(dfs_dict.keys()):
            df = dfs_dict[reg_id]
            nome_aba = obter_nome_aba(reg_id)
            
            df.to_excel(writer, sheet_name=nome_aba, index=False)
            
            worksheet = writer.sheets[nome_aba]
            worksheet.freeze_panes(1, 0) # Congela a primeira linha
            for i, col in enumerate(df.columns):
                worksheet.set_column(i, i, 15)
                
    return output.getvalue()

# --- Interface do Streamlit ---
st.title("📂 Analisador Fiscal EFD")
st.info("Leitura inteligente de blocos SPED com remoção de assinatura digital.")

arquivo_upload = st.file_uploader("Selecione o arquivo SPED (TXT)", type=["txt"])

if arquivo_upload:
    with st.spinner('Lendo estruturas e mapeando os blocos...'):
        conteudo = arquivo_upload.read()
        dfs_validados = parse_efd_to_dict(conteudo)
        
        if dfs_validados:
            st.success(f"Sucesso! {len(dfs_validados)} blocos extraídos e mapeados.")
            
            # Botão de Download
            excel_data = to_excel(dfs_validados)
            st.download_button(
                label="📥 Baixar Planilha Excel Formatada",
                data=excel_data,
                file_name=f"EFD_Analisado_{arquivo_upload.name.replace('.txt', '')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.divider()
            
            # Criando uma lista mais amigável para o SelectBox
            opcoes_selectbox = {reg: obter_nome_aba(reg) for reg in dfs_validados.keys()}
            
            bloco_selecionado = st.selectbox(
                "Selecione o bloco para conferência prévia:", 
                options=sorted(dfs_validados.keys()),
                format_func=lambda x: opcoes_selectbox[x] # Mostra o nome mapeado
            )
            
            if bloco_selecionado:
                st.write(f"### Visualizando: {opcoes_selectbox[bloco_selecionado]}")
                st.dataframe(dfs_validados[bloco_selecionado], use_container_width=True)
        else:
            st.error("Estrutura inválida. Verifique se o arquivo é um SPED compatível.")
