import streamlit as st
import pandas as pd
import numpy as np

# Configuração visual do sistema
st.set_page_config(page_title="Analista Esportivo Pro", page_icon="📊", layout="wide")

st.markdown("# 📊 Analisador Universal de Partidas")
st.markdown("---")

# URL da sua planilha do Google Sheets configurada com o seu ID correto 
URL_CSV = "https://docs.google.com/spreadsheets/d/1eOwQmNTdR6PjIZTOAUaj_wAr42waGQCQU3S-DDu-PEw/export?format=csv"

@st.cache_data(ttl=60) # Atualiza os dados a cada 60 segundos se você mudar a planilha
def carregar_dados():
    try:
        dados = pd.read_csv(URL_CSV)
        # Limpeza básica de dados
        dados['Pontos_Mandante'] = pd.to_numeric(dados['Pontos_Mandante'], errors='coerce')
        dados['Pontos_Visitante'] = pd.to_numeric(dados['Pontos_Visitante'], errors='coerce')
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("⚠️ Adicione dados na sua planilha do Google Sheets para começar.")
else:
    # --- INTERFACE DE SELEÇÃO ---
    st.sidebar.header("🔍 Selecione o Confronto")
    
    lista_esportes = df['Esporte'].unique()
    esporte_selecionado = st.sidebar.selectbox("1. Escolha o Esporte", lista_esportes)
    
    # Filtrar dados pelo esporte escolhido
    df_esporte = df[df['Esporte'] == esporte_selecionado]
    
    # Listar times disponíveis
    todos_times = sorted(list(set(df_esporte['Mandante'].unique()).union(set(df_esporte['Visitante'].unique()))))
    
    time_a = st.sidebar.selectbox("2. Time/Atleta Mandante (Casa)", todos_times)
    # Filtra para não escolher o mesmo time contra ele mesmo
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Time/Atleta Visitante (Fora)", times_disponiveis_b)

    # --- BOTÃO DE ANÁLISE ---
    if st.sidebar.button("🚀 Executar Análise Precisa"):
        
        st.subheader(f"🏟️ Confronto Histórico: {time_a} vs {time_b} ({esporte_selecionado})")
        
        # Histórico do Mandante jogando em CASA
        hist_casa = df_esporte[(df_esporte['Mandante'] == time_a)]
        # Histórico do Visitante jogando FORA
        hist_fora = df_esporte[(df_esporte['Visitante'] == time_b)]
        
        # Estatísticas do Mandante em Casa
        gols_pro_casa = hist_casa['Pontos_Mandante'].mean() if not hist_casa.empty else 0
        gols_contra_casa = hist_casa['Pontos_Visitante'].mean() if not hist_casa.empty else 0
        
        # Estatísticas do Visitante Fora
        gols_pro_fora = hist_fora['Pontos_Visitante'].mean() if not hist_fora.empty else 0
        gols_contra_fora = hist_fora['Pontos_Mandante'].mean() if not hist_fora.empty else 0

        # --- EXIBIÇÃO DE MÉTRICAS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"🏠 Estatísticas do **{time_a}** em Casa")
            st.metric("Média de Pontos Marcados", f"{gols_pro_casa:.2f}")
            st.metric("Média de Pontos Sofridos", f"{gols_contra_casa:.2f}")
            st.caption(f"Baseado em {len(hist_casa)} jogos no seu banco de dados.")

        with col2:
            st.success(f"🚀 Estatísticas do **{time_b}** Fora")
            st.metric("Média de Pontos Marcados", f"{gols_pro_fora:.2f}")
            st.metric("Média de Pontos Sofridos", f"{gols_contra_fora:.2f}")
            st.caption(f"Baseado em {len(hist_fora)} jogos no seu banco de dados.")

        # --- SISTEMA DE PREVISÃO MATEMÁTICA ---
        st.markdown("### 🎯 Probabilidades e Tendências Técnicas")
        
        # Força de Ataque vs Força de Defesa cruzadas
        expectativa_mandante = (gols_pro_casa + gols_contra_fora) / 2
        expectativa_visitante = (gols_pro_fora + gols_contra_casa) / 2
        
        col_prev1, col_prev2 = st.columns(2)
        
        with col_prev1:
            st.metric("Placar Esperado Estatisticamente", f"{expectativa_mandante:.1f} x {expectativa_visitante:.1f}")
            
        with col_prev2:
            # Lógica simples de indicação de vencedor
            if expectativa_mandante > expectativa_visitante + 0.3:
                st.warning(f"Análise: Forte tendência de vitória para o Mandante ({time_a}).")
            elif expectativa_visitante > expectativa_mandante + 0.3:
                st.warning(f"Análise: Forte tendência de vitória para o Visitante ({time_b}).")
            else:
                st.warning("Análise: Confronto extremamente equilibrado. Tendência de empate ou placar parelho.")
