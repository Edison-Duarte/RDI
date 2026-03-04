import streamlit as st
import pandas as pd
import sqlite3
import json
import urllib.parse
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Relatórios e Backup", layout="wide", page_icon="📊")

# Garantir que o banco existe nesta página
def get_db():
    conn = sqlite3.connect('escola.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, info_inicial TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_hora TEXT, autor TEXT, relato TEXT)')
    conn.commit()
    return conn

# --- FUNÇÃO PDF ---
def gerar_pdf(nome, info_ini, registros):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Relatorio: {nome}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Informacoes Iniciais:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 8, info_ini.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Historico de Evolucao:", ln=True)
    
    for _, r in registros.iterrows():
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 7, f"Data: {r['data_hora']} | Prof: {r['autor']}", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, r['relato'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACE ---
st.title("📊 Gestão de Relatórios e Dados")
conn = get_db()

abas = st.tabs(["📄 Relatório por Aluno", "💾 Backup e Segurança"])

with abas[0]:
    df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)
    if not df_alunos.empty:
        aluno_sel = st.selectbox("Escolha o aluno:", df_alunos['nome'])
        dados = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
        
        df_regs = pd.read_sql_query(f"SELECT data_hora, autor, relato FROM registros WHERE aluno_id={dados['id']} ORDER BY id DESC", conn)
        
        st.subheader(f"Histórico Completo: {aluno_sel}")
        st.caption(f"Info Inicial: {dados['info_inicial']}")
        
        for _, r in df_regs.iterrows():
            with st.expander(f"{r['data_hora']} - {r['autor']}"):
                st.write(r['relato'])

        # Botões de Envio
        st.markdown("### 📤 Exportar")
        col1, col2, col3 = st.columns(3)
        
        texto_share = f"Relatório: {aluno_sel}\n\nHistorico:\n" + "\n".join([f"- {r['relato']}" for _, r in df_regs.head(3).iterrows()])
        msg_enc = urllib.parse.quote(texto_share)

        with col1:
            st.markdown(f'<a href="https://wa.me/?text={msg_enc}" target="_blank" style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-decoration:none;display:block;text-align:center;">WhatsApp</a>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<a href="mailto:?subject=Relatorio&body={msg_enc}" style="background-color:#EA4335;color:white;padding:10px;border-radius:5px;text-decoration:none;display:block;text-align:center;">E-mail</a>', unsafe_allow_html=True)
        with col3:
            pdf_bytes = gerar_pdf(aluno_sel, dados['info_inicial'], df_regs)
            st.download_button("Baixar PDF", pdf_bytes, f"{aluno_sel}.pdf", "application/pdf")
    else:
        st.info("Cadastre alunos na página inicial.")

with abas[1]:
    st.header("⚙️ Central de Segurança")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Backup")
        if st.button("Gerar Arquivo de Backup"):
            alunos = pd.read_sql_query("SELECT * FROM alunos", conn)
            registros = pd.read_sql_query("SELECT * FROM registros", conn)
            b_data = {"alunos": alunos.to_dict('records'), "registros": registros.to_dict('records')}
            st.download_button("⬇️ Baixar JSON", json.dumps(b_data), f"backup_{datetime.now().strftime('%Y%m%d')}.json", "application/json")

    with c2:
        st.subheader("Restaurar")
        up = st.file_uploader("Suba o arquivo .json", type="json")
        if up and st.button("Confirmar Restauração"):
            data = json.loads(up.getvalue().decode())
            c = conn.cursor()
            c.execute("DELETE FROM alunos"); c.execute("DELETE FROM registros")
            for a in data['alunos']: c.execute("INSERT INTO alunos VALUES (?,?,?)", (a['id'], a['nome'], a['info_inicial']))
            for r in data['registros']: c.execute("INSERT INTO registros VALUES (?,?,?,?,?)", (r['id'], r['aluno_id'], r['data_hora'], r['autor'], r['relato']))
            conn.commit()
            st.success("Dados restaurados!")
