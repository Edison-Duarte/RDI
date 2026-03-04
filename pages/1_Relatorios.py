import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import urllib.parse
import json

st.set_page_config(page_title="Relatórios e Backup", layout="wide", page_icon="📊")

def get_db():
    return sqlite3.connect('escola.db')

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
def gerar_pdf(nome, info_inicial, registros):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Relatório: {nome}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Informações Iniciais:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, info_inicial.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Histórico:", ln=True)
    for _, row in registros.iterrows():
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"Data: {row['data_hora']} | Autor: {row['autor']}", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 8, row['relato'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- FUNÇÕES DE BACKUP ---
def exportar_backup():
    conn = get_db()
    alunos = pd.read_sql_query("SELECT * FROM alunos", conn)
    registros = pd.read_sql_query("SELECT * FROM registros", conn)
    backup_data = {
        "alunos": alunos.to_dict(orient="records"),
        "registros": registros.to_dict(orient="records")
    }
    return json.dumps(backup_data, indent=4)

def importar_backup(json_data):
    try:
        data = json.loads(json_data)
        conn = get_db()
        c = conn.cursor()
        # Limpa as tabelas atuais para evitar duplicatas ao restaurar
        c.execute("DELETE FROM alunos")
        c.execute("DELETE FROM registros")
        
        for aluno in data['alunos']:
            c.execute("INSERT INTO alunos (id, nome, info_inicial) VALUES (?, ?, ?)", 
                      (aluno['id'], aluno['nome'], aluno['info_inicial']))
        
        for reg in data['registros']:
            c.execute("INSERT INTO registros (id, aluno_id, data_hora, autor, relato) VALUES (?, ?, ?, ?, ?)", 
                      (reg['id'], reg['aluno_id'], reg['data_hora'], reg['autor'], reg['relato']))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro na importação: {e}")
        return False

# --- INTERFACE ---
st.title("📊 Relatórios e Gestão de Dados")

tabs = st.tabs(["📄 Relatório Individual", "💾 Segurança e Backup"])

with tabs[0]:
    conn = get_db()
    df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)

    if not df_alunos.empty:
        aluno_sel = st.selectbox("Selecione o Aluno:", df_alunos['nome'])
        aluno_dados = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
        df_regs = pd.read_sql_query(f"SELECT data_hora, autor, relato FROM registros WHERE aluno_id = {aluno_dados['id']} ORDER BY id DESC", conn)
        
        st.markdown(f"### Aluno: {aluno_sel}")
        st.info(f"**Informações Iniciais:** {aluno_dados['info_inicial']}")
        
        if not df_regs.empty:
            for _, r in df_regs.iterrows():
                st.caption(f"📅 {r['data_hora']} — ✍️ {r['autor']}")
                st.write(r['relato'])
                st.divider()

            # Exportação
            st.subheader("📤 Compartilhar Relatório")
            col1, col2, col3 = st.columns(3)
            
            # Formatação para links
            texto_share = f"Relatório de {aluno_sel}\n\nInfo: {aluno_dados['info_inicial']}\n\nÚltimo Relato: {df_regs.iloc[0]['relato']}"
            msg_encoded = urllib.parse.quote(texto_share)
            
            with col1:
                st.markdown(f'''<a href="https://wa.me/?text={msg_encoded}" target="_blank" 
                    style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-decoration:none;display:block;text-align:center;">
                    📱 WhatsApp</a>''', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''<a href="mailto:?subject=Relatorio&body={msg_encoded}" 
                    style="background-color:#EA4335;color:white;padding:10px;border-radius:5px;text-decoration:none;display:block;text-align:center;">
                    📧 E-mail</a>''', unsafe_allow_html=True)
            with col3:
                pdf_bytes = gerar_pdf(aluno_sel, aluno_dados['info_inicial'], df_regs)
                st.download_button("📄 Baixar PDF", pdf_bytes, f"Relatorio_{aluno_sel}.pdf", "application/pdf")
        else:
            st.warning("Sem registros para este aluno.")
    else:
        st.info("Nenhum aluno cadastrado.")

with tabs[1]:
    st.header("⚙️ Central de Backup")
    st.write("Como o servidor pode reiniciar, recomendamos baixar um backup semanalmente.")
    
    col_back1, col_back2 = st.columns(2)
    
    with col_back1:
        st.subheader("1. Exportar")
        data_json = exportar_backup()
        st.download_button(
            label="⬇️ Baixar Backup Completo (.json)",
            data=data_json,
            file_name=f"backup_escola_{datetime.now().strftime('%d_%m_%Y')}.json",
            mime="application/json"
        )
        st.caption("Guarde este arquivo em local seguro (Google Drive ou Pen Drive).")

    with col_back2:
        st.subheader("2. Importar")
        arquivo_upload = st.file_uploader("Selecione o arquivo de backup para restaurar", type="json")
        if arquivo_upload is not None:
            if st.button("🚀 Restaurar Dados Agora"):
                conteudo = arquivo_upload.getvalue().decode("utf-8")
                if importar_backup(conteudo):
                    st.success("✅ Banco de dados restaurado com sucesso! Recarregue a página.")
                    st.balloons()
