import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Portal Fiscal - EFD", layout="wide")

# Mapeamento para renomear as ABAS (sem caracteres especiais)
MAPA_BLOCOS = {
    "0000": "Abertura e Identificacao",
    "0100": "Dados do Contabilista",
    "0110": "Regimes de Apuracao",
    "0140": "Cadastro de Estabelecimento",
    "0150": "Cadastro de Participante",
    "0190": "Unidades de Medida",
    "0200": "Identificacao do Item",
    "0400": "Natureza da Operacao",
    "0500": "Plano de Contas",
    "A100": "NF de Servico",
    "A170": "Itens da NF de Servico",
    "C010": "Identific. Estabelecimento",
    "C100": "NF Entrada e Saida",
    "C170": "Itens da NF",
    "C180": "Consolidacao de Notas",
    "C190": "Consolidacao de Notas",
    "C395": "Notas Fiscais de Venda",
    "C400": "Equipamento ECF",
    "C405": "Reducao Z",
    "C500": "Energia-Agua-Gas",
    "D100": "Transporte e Comunicacao",
    "F100": "Demais Operacoes",
    "F200": "Operacoes Imobiliarias",
    "M200": "Apuracao PIS",
    "M400": "Receitas Isentas PIS",
    "M600": "Apuracao COFINS",
    "M800": "Receitas Isentas COFINS",
    "1100": "Controle Creditos PIS",
    "1500": "Controle Creditos COFINS",
    "9900": "Totalizadores",
    "9999": "Encerramento"
}

# Mapeamento oficial dos CAMPOS (Cabeçalhos das Colunas) baseados no Guia Prático
COLUNAS_SPED = {
    "0000": ["REG", "COD_VER", "TIPO_ESCRIT", "IND_SIT_ESP", "NUM_REC_ANTERIOR", "DT_INI", "DT_FIN", "NOME", "CNPJ", "UF", "COD_MUN", "SUFRAMA", "IND_NAT_PJ", "IND_ATIV"],
    "0100": ["REG", "NOME", "CPF", "CRC", "CNPJ", "CEP", "END", "NUM", "COMPL", "BAIRRO", "FONE", "FAX", "EMAIL", "COD_MUN"],
    "0140": ["REG", "COD_EST", "NOME", "CNPJ", "UF", "IE", "COD_MUN", "IM", "SUFRAMA"],
    "0150": ["REG", "COD_PART", "NOME", "COD_PAIS", "CNPJ", "CPF", "IE", "COD_MUN", "SUFRAMA", "END", "NUM", "COMPL", "BAIRRO"],
    "0200": ["REG", "COD_ITEM", "DESCR_ITEM", "COD_BARRA", "COD_ANT_ITEM", "UNID_INV", "TIPO_ITEM", "COD_NCM", "EX_IPI", "COD_GEN", "COD_LST", "ALIQ_ICMS"],
    "C100": ["REG", "IND_OPER", "IND_EMIT", "COD_PART", "COD_MOD", "COD_SIT", "SER", "NUM_DOC", "CHV_NFE", "DT_DOC", "DT_E_S", "VL_DOC", "IND_PGTO", "VL_DESC", "VL_ABAT_NT", "VL_MERC", "IND_FRT", "VL_FRT", "VL_SEG", "VL_OUT_DA", "VL_BC_ICMS", "VL_ICMS", "VL_BC_ICMS_ST", "VL_ICMS_ST", "VL_IPI", "VL_PIS", "VL_COFINS", "VL_PIS_ST", "VL_COFINS_ST"],
    "C170": ["REG", "NUM_ITEM", "COD_ITEM", "DESCR_COMPL", "QTD", "UNID", "VL_ITEM", "VL_DESC", "IND_MOV", "CST_ICMS", "CFOP", "COD_NAT", "VL_BC_ICMS", "ALIQ_ICMS", "VL_ICMS", "VL_BC_ICMS_ST", "ALIQ_ST", "VL_ICMS_ST", "IND_APUR", "CST_IPI", "COD_ENQ", "VL_BC_IPI", "ALIQ_IPI", "VL_IPI", "CST_PIS", "VL_BC_PIS", "ALIQ_PIS", "QUANT_BC_PIS", "ALIQ_PIS_REAIS", "VL_PIS", "CST_COFINS", "VL_BC_COFINS", "ALIQ_COFINS", "QUANT_BC_COFINS", "ALIQ_COFINS_REAIS", "VL_COFINS", "COD_CTA"]
}

def obter_nome_aba(reg_id):
    """Retorna o nome da aba limpo e com limite de 31 caracteres para o Excel."""
    descricao = MAPA_BLOCOS.get(reg_id, f"Bloco_{reg_id}")
    nome_completo = f"{reg_id} - {descricao}"
    nome_limpo = re.sub(r'[\[\]:*?/\\]', '-', nome_completo)
    return nome_limpo[:31]

def parse_efd_to_dict(file_content):
    """Lê o TXT, parando no bloco 9999 e aplica os nomes das colunas."""
    data_dict = {}
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
                
                if reg_id == '9999':
                    break
    
    dfs_prontos = {}
    for reg, listas in data_dict.items():
        max_cols = max(len(l) for l in listas)
        listas_normalizadas = [l + [''] * (max_cols - len(l)) for l in listas]
        
        df = pd.DataFrame(listas_normalizadas)
        
        # MÁGICA DOS CABEÇALHOS: Aplica o nome oficial ou "Campo_X" como fallback
        colunas_oficiais = COLUNAS_SPED.get(reg, [])
        nomes_finais = []
        for i in range(max_cols):
            if i < len(colunas_oficiais):
                nomes_finais.append(colunas_oficiais[i])
            else:
                nomes_finais.append(f"Campo_{i+1}")
                
        df.columns = nomes_finais
        dfs_prontos[reg] = df
        
    return dfs_prontos

def to_excel(dfs_dict):
    """Gera o Excel com abas renomeadas."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for reg_id in sorted(dfs_dict.keys()):
            df = dfs_dict[reg_id]
            nome_aba = obter_nome_aba(reg_id)
            
            # Exporta com os cabeçalhos (header=True)
            df.to_excel(writer, sheet_name=nome_aba, index=False, header=True)
            
            worksheet = writer.sheets[nome_aba]
            worksheet.freeze_panes(1, 0)
            for i, col in enumerate(df.columns):
                worksheet.set_column(i, i, 18)
                
    return output.getvalue()

# --- Interface do Streamlit ---
st.title("📂 Analisador Fiscal EFD")
st.info("Leitura inteligente de blocos SPED, com colunas mapeadas e remoção de assinatura digital.")

arquivo_upload = st.file_uploader("Selecione o arquivo SPED (TXT)", type=["txt"])

if arquivo_upload:
    with st.spinner('Mapeando colunas e processando dados...'):
        conteudo = arquivo_upload.read()
        dfs_validados = parse_efd_to_dict(conteudo)
        
        if dfs_validados:
            st.success(f"Sucesso! {len(dfs_validados)} blocos extraídos.")
            
            excel_data = to_excel(dfs_validados)
            st.download_button(
                label="📥 Baixar Planilha Excel Formatada",
                data=excel_data,
                file_name=f"EFD_Analisado_{arquivo_upload.name.replace('.txt', '')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.divider()
            opcoes_selectbox = {reg: obter_nome_aba(reg) for reg in dfs_validados.keys()}
            bloco_selecionado = st.selectbox(
                "Selecione o bloco para conferência prévia:", 
                options=sorted(dfs_validados.keys()),
                format_func=lambda x: opcoes_selectbox[x]
            )
            
            if bloco_selecionado:
                st.write(f"### Visualizando: {opcoes_selectbox[bloco_selecionado]}")
                st.dataframe(dfs_validados[bloco_selecionado], use_container_width=True)
        else:
            st.error("Estrutura inválida. Verifique se o arquivo é um SPED compatível.")
