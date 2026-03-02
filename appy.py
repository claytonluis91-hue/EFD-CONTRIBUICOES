import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Portal Fiscal - EFD", layout="wide")

# Mapeamento expandido para renomear quase todas as ABAS
MAPA_BLOCOS = {
    "0000": "Abertura e Identificacao",
    "0001": "Abertura do Bloco 0",
    "0100": "Dados do Contabilista",
    "0110": "Regimes de Apuracao",
    "0111": "Rec Bruta Nao Cumulativa",
    "0140": "Cadastro de Estabelecimento",
    "0150": "Cadastro de Participante",
    "0190": "Unidades de Medida",
    "0200": "Identificacao do Item",
    "0205": "Alteracao do Item",
    "0400": "Natureza da Operacao",
    "0450": "Informacao Complementar",
    "0500": "Plano de Contas",
    "0990": "Encerramento do Bloco 0",
    "1001": "Abertura do Bloco 1",
    "1100": "Controle Creditos PIS",
    "1500": "Controle Creditos COFINS",
    "1990": "Encerramento do Bloco 1",
    "9001": "Abertura do Bloco 9",
    "9900": "Totalizadores",
    "9990": "Encerramento do Bloco 9",
    "9999": "Encerramento do Arquivo",
    "A001": "Abertura do Bloco A",
    "A010": "Identificacao Estabelecimento",
    "A100": "NF de Servico",
    "A170": "Itens da NF de Servico",
    "A990": "Encerramento do Bloco A",
    "C001": "Abertura do Bloco C",
    "C010": "Identificacao Estabelecimento",
    "C100": "NF Entrada e Saida",
    "C110": "Info Complementar NF",
    "C120": "Op de Importacao",
    "C170": "Itens da NF",
    "C180": "Consolidacao de Notas",
    "C190": "Consolidacao de Notas",
    "C395": "Notas Fiscais de Venda",
    "C400": "Equipamento ECF",
    "C405": "Reducao Z",
    "C500": "Energia-Agua-Gas",
    "C501": "PIS Energia-Agua-Gas",
    "C505": "COFINS Energia-Agua-Gas",
    "C990": "Encerramento do Bloco C",
    "D001": "Abertura do Bloco D",
    "D010": "Identificacao Estabelecimento",
    "D100": "Transporte e Comunicacao",
    "D101": "PIS Transp e Comunicacao",
    "D105": "COFINS Transp e Comunicacao",
    "D990": "Encerramento do Bloco D",
    "F001": "Abertura do Bloco F",
    "F010": "Identificacao Estabelecimento",
    "F100": "Demais Operacoes",
    "F130": "Ativo Imobilizado",
    "F990": "Encerramento do Bloco F",
    "I001": "Abertura do Bloco I",
    "I990": "Encerramento do Bloco I",
    "M001": "Abertura do Bloco M",
    "M100": "Credito de PIS",
    "M105": "Base Calc PIS",
    "M200": "Apuracao PIS",
    "M210": "Detalhamento Apuracao PIS",
    "M400": "Receitas Isentas PIS",
    "M410": "Detalhe Rec Isentas PIS",
    "M500": "Credito de COFINS",
    "M505": "Base Calc COFINS",
    "M600": "Apuracao COFINS",
    "M610": "Detalhamento Apuracao COFINS",
    "M800": "Receitas Isentas COFINS",
    "M810": "Detalhe Rec Isentas COFINS",
    "M990": "Encerramento do Bloco M",
    "P001": "Abertura do Bloco P",
    "P990": "Encerramento do Bloco P"
}

# Cabeçalhos Técnicos dos Principais Blocos
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
        
        # MÁGICA DOS CABEÇALHOS
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
    """Gera o Excel com Aba de Menu e botões de voltar."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formatando os Hiperlinks (Azul, sublinhado e negrito)
        link_format = workbook.add_format({
            'font_color': 'blue',
            'underline': True,
            'bold': True
        })
        
        # Criando a Aba MENU PRINCIPAL
        menu_sheet_name = "Menu Principal"
        worksheet_menu = workbook.add_worksheet(menu_sheet_name)
        worksheet_menu.write('A1', 'ÍNDICE DE REGISTROS - EFD', workbook.add_format({'bold': True, 'size': 14}))
        worksheet_menu.write('A2', 'Clique no bloco abaixo para ser direcionado para a aba:')
        
        linha_menu = 3 # A lista de abas começará na linha 4 do Excel
        
        for reg_id in sorted(dfs_dict.keys()):
            df = dfs_dict[reg_id]
            nome_aba = obter_nome_aba(reg_id)
            
            # Escreve o DataFrame a partir da linha 1 (deixando a linha 0 vazia para o botão voltar)
            df.to_excel(writer, sheet_name=nome_aba, index=False, header=True, startrow=1)
            
            worksheet = writer.sheets[nome_aba]
            
            # Escreve o hiperlink na Linha 1 (index 0), Coluna A apontando para o Menu
            worksheet.write_url('A1', f"internal:'{menu_sheet_name}'!A1", string="🔙 Voltar ao Menu Principal", cell_format=link_format)
            
            # Congela as duas primeiras linhas (Botão Voltar e Cabeçalhos)
            worksheet.freeze_panes(2, 0)
            
            # Ajusta largura
            for i, col in enumerate(df.columns):
                worksheet.set_column(i, i, 18)
                
            # Adiciona o link da aba lá na página do Menu Principal
            worksheet_menu.write_url(f'A{linha_menu}', f"internal:'{nome_aba}'!A1", string=f"Bloco {nome_aba}", cell_format=link_format)
            linha_menu += 1
            
        # Alarga a coluna do Menu para caber os links
        worksheet_menu.set_column('A:A', 50)
                
    return output.getvalue()

# --- Configuração de Reset do Sistema ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_app():
    """Altera a chave do uploader para forçar o Streamlit a esvaziar a memória."""
    st.session_state.uploader_key += 1

# --- Interface do Streamlit ---
st.title("📂 Portal Auditoria Fiscal - EFD")
st.info("Leitura de Blocos SPED, com Menu Interativo e Colunas Mapeadas.")

col_upload, col_btn = st.columns([4, 1])

with col_upload:
    # O "key" dinâmico garante que o arquivo é esquecido quando resetamos
    arquivo_upload = st.file_uploader(
        "Selecione o arquivo SPED (TXT)", 
        type=["txt"], 
        key=f"uploader_{st.session_state.uploader_key}"
    )

with col_btn:
    st.write("") # Espaçamento
    st.write("")
    if st.button("🔄 Novo Arquivo", help="Limpar a tela e subir outro TXT"):
        reset_app()
        st.rerun() # Atualiza a tela imediatamente

if arquivo_upload:
    with st.spinner('Mapeando colunas e gerando Menu Interativo...'):
        conteudo = arquivo_upload.read()
        dfs_validados = parse_efd_to_dict(conteudo)
        
        if dfs_validados:
            st.success(f"Sucesso! {len(dfs_validados)} blocos extraídos.")
            
            excel_data = to_excel(dfs_validados)
            st.download_button(
                label="📥 Baixar Planilha Excel com Menu",
                data=excel_data,
                file_name=f"Auditoria_{arquivo_upload.name.replace('.txt', '')}.xlsx",
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
