import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Registro Escolar Supabase", layout="wide", page_icon="🏫")

# Conexão com Supabase (Pegando dos Secrets do Streamlit)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🏫 Registro de Desenvolvimento (Nuvem)")

# --- CADASTRO DE ALUNOS ---
with st.expander("🆕 Cadastrar Novo Aluno"):
    with st.form("form_cadastro", clear_on_submit=True):
        nome_aluno = st.text_input("Nome Completo do Aluno")
        info_inicial = st.text_area("Informações Iniciais")
        if st.form_submit_button("Adicionar Aluno"):
            if nome_aluno:
                data = {"nome": nome_aluno, "info_inicial": info_inicial}
                supabase.table("alunos").insert(data).execute()
                st.success(f"Aluno {nome_aluno} salvo na nuvem!")
                st.rerun()

st.divider()

# --- BUSCA E REGISTRO ---
st.subheader("🔍 Busca e Registro Diário")

# Busca inteligente de alunos no Supabase
res_alunos = supabase.table("alunos").select("*").order("nome").execute()
df_alunos = pd.DataFrame(res_alunos.data)

if not df_alunos.empty:
    lista_nomes = df_alunos['nome'].tolist()
    selecao = st.selectbox("Pesquise o aluno:", [""] + lista_nomes)

    if selecao:
        aluno_id = int(df_alunos[df_alunos['nome'] == selecao]['id'].values[0])
        
        with st.form("registro_diario", clear_on_submit=True):
            st.markdown(f"**Relato para: {selecao}**")
            col1, col2 = st.columns(2)
            autor = col1.text_input("Professor(a)")
            data_hora = col2.text_input("Data/Hora", datetime.now().strftime("%d/%m/%Y %H:%M"))
            relato = st.text_area("Descrição do desenvolvimento")
            
            if st.form_submit_button("Salvar no Histórico"):
                if autor and relato:
                    novo_reg = {
                        "aluno_id": aluno_id,
                        "data_hora": data_hora,
                        "autor": autor,
                        "relato": relato
                    }
                    supabase.table("registros").insert(novo_reg).execute()
                    st.success("💾 Registro salvo permanentemente!")
                else:
                    st.warning("Preencha os campos obrigatórios.")
else:
    st.info("Aguardando cadastro de alunos...")
