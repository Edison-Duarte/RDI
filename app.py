import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração inicial
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
st.markdown("---")

# --- SEÇÃO: NOVO ALUNO ---
st.subheader("🆕 Cadastrar Novo Aluno")
with st.form("form_cadastro", clear_on_submit=True):
    nome_aluno = st.text_input("Nome Completo do Aluno")
    info_inicial = st.text_area("Informações Iniciais (Contexto familiar, saúde, etc.)")
    btn_adicionar = st.form_submit_button("Adicionar Aluno")
    
    if btn_adicionar:
        if nome_aluno:
            c = conn.cursor()
            c.execute("INSERT INTO alunos (nome, info_inicial) VALUES (?, ?)", (nome_aluno, info_inicial))
            conn.commit()
            st.success(f"✅ {nome_aluno} cadastrado com sucesso!")
        else:
            st.error("⚠️ O nome do aluno é obrigatório.")

st.markdown("---")

# --- SEÇÃO: BUSCA E REGISTRO DIÁRIO ---
st.subheader("🔍 Busca e Seleção")

# Carregar alunos para o selectbox inteligente
df_alunos = pd.read_sql_query("SELECT * FROM alunos ORDER BY nome", conn)

if not df_alunos.empty:
    lista_nomes = df_alunos['nome'].tolist()
    # O selectbox do Streamlit já possui busca inteligente nativa ao digitar
    aluno_selecionado = st.selectbox("Selecione o aluno para novo registro:", [""] + lista_nomes)

    if aluno_selecionado:
        # Pega dados do aluno selecionado
        aluno_id = df_alunos[df_alunos['nome'] == aluno_selecionado]['id'].values[0]
        
        st.info(f"**Registrando para:** {aluno_selecionado}")
        
        # Formulário de novo registro
        with st.form("novo_registro_diario", clear_on_submit=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                autor = st.text_input("Nome do Educador")
            with col2:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.write(f"**Data/Hora:** {data_atual}")
            
            relato = st.text_area("Relato do Desenvolvimento / Ocorrência Diária")
            
            if st.form_submit_button("Salvar Registro"):
                if autor and relato:
                    c = conn.cursor()
                    c.execute("INSERT INTO registros (aluno_id, data_hora, autor, relato) VALUES (?, ?, ?, ?)", 
                              (int(aluno_id), data_atual, autor, relato))
                    conn.commit()
                    st.success("💾 Registro salvo no histórico com sucesso!")
                else:
                    st.warning("⚠️ Preencha o nome do autor e o relato.")
else:
    st.info("Nenhum aluno cadastrado. Use o formulário acima para começar.")
