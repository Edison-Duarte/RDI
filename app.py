import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Registro Escolar", layout="wide", page_icon="📝")

# Inicialização do Banco de Dados
def init_db():
    conn = sqlite3.connect('escola.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alunos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, info_inicial TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_hora TEXT, autor TEXT, relato TEXT)''')
    conn.commit()
    return conn

conn = init_db()

st.title("📝 Registro de Desenvolvimento Infantil")

# --- CADASTRO DE ALUNOS ---
with st.expander("🆕 Cadastrar Novo Aluno", expanded=False):
    with st.form("form_cadastro", clear_on_submit=True):
        nome_aluno = st.text_input("Nome Completo do Aluno")
        info_inicial = st.text_area("Informações Iniciais")
        if st.form_submit_button("Adicionar Aluno"):
            if nome_aluno:
                c = conn.cursor()
                c.execute("INSERT INTO alunos (nome, info_inicial) VALUES (?, ?)", (nome_aluno, info_inicial))
                conn.commit()
                st.success(f"Aluno {nome_aluno} cadastrado!")
                st.rerun()
            else:
                st.error("O nome é obrigatório.")

st.divider()

# --- BUSCA E NOVO REGISTRO ---
st.subheader("🔍 Busca e Registro Diário")
df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)

if not df_alunos.empty:
    lista_nomes = df_alunos['nome'].tolist()
    selecao = st.selectbox("Pesquise ou selecione o aluno:", [""] + lista_nomes)

    if selecao:
        aluno_id = df_alunos[df_alunos['nome'] == selecao]['id'].values[0]
        
        with st.form("registro_diario", clear_on_submit=True):
            st.markdown(f"**Novo relato para: {selecao}**")
            col1, col2 = st.columns(2)
            autor = col1.text_input("Nome do Professor/Responsável")
            data_hora = col2.text_input("Data/Hora", datetime.now().strftime("%d/%m/%Y %H:%M"))
            relato = st.text_area("Descrição do desenvolvimento")
            
            if st.form_submit_button("Salvar Registro"):
                if autor and relato:
                    c = conn.cursor()
                    c.execute("INSERT INTO registros (aluno_id, data_hora, autor, relato) VALUES (?, ?, ?, ?)", 
                              (int(aluno_id), data_hora, autor, relato))
                    conn.commit()
                    st.success("Registro salvo com sucesso!")
                else:
                    st.warning("Preencha todos os campos.")
else:
    st.info("Nenhum aluno cadastrado no sistema.")
