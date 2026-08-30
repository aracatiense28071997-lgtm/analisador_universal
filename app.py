import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuração visual do sistema
st.set_page_config(page_title="Analista Esportivo Pro", page_icon="📊", layout="wide")

st.markdown("# 📊 Analisador Universal de Partidas")
st.markdown("---")

# URL da sua planilha do Google Sheets configurada com o seu ID correto 
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTZlqND0nXrDDPcDo1ms1oWX0l0CDdFf9BisIYMaWC2wS1xoO3ZwAkc6Qe3sKGWR5a921vsJMinrHo5/pub?output=csv"

@st.cache_data(ttl=60) 
def carregar_dados():
    try:
        dados = pd.read_csv(URL_CSV)
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
    
    df_esporte = df[df['Esporte'] == esporte_selecionado]
    todos_times = sorted(list(set(df_esporte['Mandante'].unique()).union(set(df_esporte['Visitante'].unique()))))
    
    time_a = st.sidebar.selectbox("2. Time/Atleta Mandante (Casa)", todos_times)
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Time/Atleta Visitante (Fora)", times_disponiveis_b)

    # --- BOTÃO DE ANÁLISE ---
    if st.sidebar.button("🚀 Executar Análise Precisa"):
        
        st.subheader(f"🏟️ Confronto Histórico: {time_a} vs {time_b} ({esporte_selecionado})")
        
        hist_casa = df_esporte[(df_esporte['Mandante'] == time_a)]
        hist_fora = df_esporte[(df_esporte['Visitante'] == time_b)]
        
        gols_pro_casa = hist_casa['Pontos_Mandante'].mean() if not hist_casa.empty else 0
        gols_contra_casa = hist_casa['Pontos_Visitante'].mean() if not hist_casa.empty else 0
        
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

        # --- NOVO: GRÁFICO DE BARRAS COMPARATIVO ---
        st.markdown("### 📊 Comparativo Visual de Força")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Pontos Feitos (Ataque)',
            x=[time_a, time_b],
            y=[gols_pro_casa, gols_pro_fora],
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Bar(
            name='Pontos Sofridos (Defesa)',
            x=[time_a, time_b],
            y=[gols_contra_casa, gols_contra_fora],
            marker_color='#ef553b'
        ))
        
        fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # --- SISTEMA DE PREVISÃO MATEMÁTICA ---
        st.markdown("### 🎯 Probabilidades e Tendências Técnicas")
        
        expectativa_mandante = (gols_pro_casa + gols_contra_fora) / 2
        expectativa_visitante = (gols_pro_fora + gols_contra_casa) / 2
        
        col_prev1, col_prev2 = st.columns(2)
        
        with col_prev1:
            st.metric("Placar Esperado Estatisticamente", f"{expectativa_mandante:.1f} x {expectativa_visitante:.1f}")
            
        with col_prev2:
            if expectativa_mandante > expectativa_visitante + 0.3:
                st.warning(f"Análise: Forte tendência de vitória para o Mandante ({time_a}).")
            elif expectativa_visitante > expectativa_mandante + 0.3:
                st.warning(f"Análise: Forte tendência de vitória para o Visitante ({time_b}).")
            else:
                st.warning("Análise: Confronto extremamente equilibrado. Tendência de empate ou placar parelho.")

        # --- NOVO: TABELA DE JOGOS RECENTES MAPEADOS ---
        st.markdown("### 📅 Últimas Partidas Registradas Destes Times")
        jogos_recentes = df_esporte[
            (df_esporte['Mandante'] == time_a) | (df_esporte['Visitante'] == time_a) |
            (df_esporte['Mandante'] == time_b) | (df_esporte['Visitante'] == time_b)
        ].tail(5)
        
        if not jogos_recentes.empty:
            st.dataframe(jogos_recentes, use_container_width=True)
        else:
            st.caption("Nenhum jogo recente listado na planilha para essas equipes.")
