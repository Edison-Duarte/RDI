import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from fpdf import FPDF

st.set_page_config(page_title="Relatórios e Gestão", layout="wide", page_icon="📊")

# Conexão
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def gerar_pdf(nome, info_ini, registros):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Relatorio: {nome}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "Info Inicial:", ln=True)
    pdf.set_font("Arial", '', 11); pdf.multi_cell(0, 8, info_ini.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "Historico:", ln=True)
    for _, r in registros.iterrows():
        pdf.set_font("Arial", 'B', 10); pdf.cell(0, 7, f"{r['data_hora']} | {r['autor']}", ln=True)
        pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 6, r['relato'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(2); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1', 'replace')

st.title("📊 Gestão de Alunos e Relatórios")

res_alunos = supabase.table("alunos").select("*").order("nome").execute()
df_alunos = pd.DataFrame(res_alunos.data)

if not df_alunos.empty:
    aluno_sel = st.selectbox("Selecione o Aluno:", df_alunos['nome'])
    dados_aluno = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
    aluno_id = int(dados_aluno['id'])

    aba1, aba2 = st.tabs(["📝 Editar Dados Aluno", "📜 Relatório e Histórico"])

    with aba1:
        st.subheader("Editar Cadastro do Aluno")
        novo_nome = st.text_input("Nome", value=dados_aluno['nome'])
        nova_info = st.text_area("Info Inicial", value=dados_aluno['info_inicial'])
        if st.button("Salvar Alterações do Aluno"):
            supabase.table("alunos").update({"nome": novo_nome, "info_inicial": nova_info}).eq("id", aluno_id).execute()
            st.success("Dados do aluno atualizados!")
            st.rerun()

    with aba2:
        res_regs = supabase.table("registros").select("*").eq("aluno_id", aluno_id).order("id", desc=True).execute()
        df_regs = pd.DataFrame(res_regs.data)

        if not df_regs.empty:
            for _, r in df_regs.iterrows():
                with st.expander(f"📅 {r['data_hora']} - {r['autor']}"):
                    ed_autor = st.text_input("Autor", value=r['autor'], key=f"a_{r['id']}")
                    ed_relato = st.text_area("Relato", value=r['relato'], key=f"r_{r['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("Salvar Alteração", key=f"b_{r['id']}"):
                        supabase.table("registros").update({"autor": ed_autor, "relato": ed_relato}).eq("id", r['id']).execute()
                        st.success("Alterado!")
                        st.rerun()
                    if c2.button("Excluir Registro", key=f"d_{r['id']}"):
                        supabase.table("registros").delete().eq("id", r['id']).execute()
                        st.warning("Excluído!")
                        st.rerun()

            # Exportação
            st.divider()
            col1, col2, col3 = st.columns(3)
            txt_share = f"Relatorio {aluno_sel}\n\n{dados_aluno['info_inicial']}"
            msg_enc = urllib.parse.quote(txt_share)
            
            with col1:
                st.markdown(f'<a href="https://wa.me/?text={msg_enc}" target="_blank" style="background-color:#25D366;color:white;padding:12px;border-radius:8px;text-decoration:none;display:block;text-align:center;font-weight:bold;">WhatsApp</a>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<a href="mailto:?subject=Relatorio&body={msg_enc}" style="background-color:#EA4335;color:white;padding:12px;border-radius:8px;text-decoration:none;display:block;text-align:center;font-weight:bold;">E-mail</a>', unsafe_allow_html=True)
            with col3:
                pdf_bytes = gerar_pdf(aluno_sel, dados_aluno['info_inicial'], df_regs)
                st.download_button("📄 PDF", pdf_bytes, f"{aluno_sel}.pdf", "application/pdf")
        else:
            st.warning("Nenhum histórico encontrado para este aluno.")
else:
    st.info("Cadastre alunos primeiro.")
