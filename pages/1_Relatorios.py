import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import urllib.parse

st.set_page_config(page_title="Relatórios Individuais", layout="wide", page_icon="📊")

def get_db():
    return sqlite3.connect('escola.db')

# Função para gerar PDF
def gerar_pdf(nome, info_inicial, registros):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Relatorio de Desenvolvimento: {nome}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Informacoes Iniciais:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, info_inicial)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Historico de Registros:", ln=True)
    
    pdf.set_font("Arial", '', 10)
    for index, row in registros.iterrows():
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"Data: {row['data_hora']} | Autor: {row['autor']}", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 8, row['relato'])
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

st.title("📊 Relatório Individual Completo")

conn = get_db()
df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)

if not df_alunos.empty:
    aluno_sel = st.selectbox("Selecione o Aluno:", df_alunos['nome'])
    aluno_dados = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
    
    # Busca registros
    df_regs = pd.read_sql_query(f"SELECT data_hora, autor, relato FROM registros WHERE aluno_id = {aluno_dados['id']} ORDER BY id DESC", conn)
    
    # Exibição na Tela
    st.markdown(f"### Aluno: {aluno_sel}")
    st.write(f"**Informações Iniciais:** {aluno_dados['info_inicial']}")
    st.divider()
    
    if not df_regs.empty:
        for _, r in df_regs.iterrows():
            with st.container():
                st.caption(f"📅 {r['data_hora']} — ✍️ {r['autor']}")
                st.write(r['relato'])
                st.markdown("---")
        
        # Texto para WhatsApp/Email
        texto_relatorio = f"*Relatório de {aluno_sel}*\n\n"
        texto_relatorio += f"*Info Inicial:* {aluno_dados['info_inicial']}\n\n"
        texto_relatorio += "*Últimos Registros:*\n"
        for _, r in df_regs.head(5).iterrows(): # Pega os 5 últimos para não travar o link
            texto_relatorio += f"- {r['data_hora']}: {r['relato']}\n"

        # --- BOTÕES DE EXPORTAÇÃO ---
        st.subheader("📤 Exportar e Compartilhar")
        
        # Estilização CSS para botões coloridos
        st.markdown("""
            <style>
            .btn-container { display: flex; gap: 10px; margin-bottom: 20px; }
            .btn-custom {
                padding: 12px 24px;
                border-radius: 10px;
                color: white !important;
                text-decoration: none;
                font-weight: bold;
                font-family: sans-serif;
            }
            .wa { background-color: #25D366; }
            .em { background-color: #EA4335; }
            </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        
        with col1:
            msg_encoded = urllib.parse.quote(texto_relatorio)
            st.markdown(f'<a href="https://wa.me/?text={msg_encoded}" target="_blank" class="btn-custom wa">📱 WhatsApp</a>', unsafe_allow_html=True)
        
        with col2:
            assunto = urllib.parse.quote(f"Relatório Escolar: {aluno_sel}")
            corpo_email = urllib.parse.quote(texto_relatorio)
            st.markdown(f'<a href="mailto:?subject={assunto}&body={corpo_email}" class="btn-custom em">📧 E-mail</a>', unsafe_allow_html=True)
            
        with col3:
            pdf_bytes = gerar_pdf(aluno_sel, aluno_dados['info_inicial'], df_regs)
            st.download_button(label="📄 Baixar PDF", data=pdf_bytes, file_name=f"Relatorio_{aluno_sel}.pdf", mime="application/pdf")

    else:
        st.warning("Este aluno ainda não possui registros diários.")
else:
    st.info("Nenhum aluno encontrado.")
