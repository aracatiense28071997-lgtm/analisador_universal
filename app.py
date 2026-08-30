import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import poisson # Biblioteca matemática para cálculo de IA

# Configuração visual do sistema
st.set_page_config(page_title="Analista Esportivo Pro AI", page_icon="🤖", layout="wide")

st.markdown("# 🤖 Analisador Esportivo com IA Avançada")
st.markdown("---")

# URL da sua planilha do Google Sheets configurada com o seu ID correto 
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTZlqND0nXrDDPcDo1ms1oWX0l0CDdFf9BisIYMaWC2wS1xoO3ZwAkc6Qe3sKGWR5a921vsJMinrHo5/pub?output=csv"

@st.cache_data(ttl=30) 
def carregar_dados():
    try:
        dados = pd.read_csv(URL_CSV)
        dados['Pontos_Mandante'] = pd.to_numeric(dados['Pontos_Mandante'], errors='coerce')
        dados['Pontos_Visitante'] = pd.to_numeric(dados['Pontos_Visitante'], errors='coerce')
        dados['Métrica_Ataque'] = pd.to_numeric(dados['Métrica_Ataque'], errors='coerce')
        dados['Métrica_Defesa'] = pd.to_numeric(dados['Métrica_Defesa'], errors='coerce')
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("⚠️ Adicione dados na sua planilha do Google Sheets para começar.")
else:
    # --- INTERFACE DE SELEÇÃO ---
    st.sidebar.header("🔍 Configurar Confronto")
    
    lista_esportes = df['Esporte'].unique()
    esporte_selecionado = st.sidebar.selectbox("1. Escolha o Esporte", lista_esportes)
    
    df_esporte = df[df['Esporte'] == esporte_selecionado]
    todos_times = sorted(list(set(df_esporte['Mandante'].unique()).union(set(df_esporte['Visitante'].unique()))))
    
    time_a = st.sidebar.selectbox("2. Mandante (Casa)", todos_times)
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Visitante (Fora)", times_disponiveis_b)

    if st.sidebar.button("🚀 Executar Análise Preditiva IA"):
        
        st.subheader(f"🏟️ Confronto: {time_a} vs {time_b} ({esporte_selecionado})")
        
        # Filtros de Histórico
        hist_casa = df_esporte[(df_esporte['Mandante'] == time_a)]
        hist_fora = df_esporte[(df_esporte['Visitante'] == time_b)]
        
        # Médias de Pontos
        gols_pro_casa = hist_casa['Pontos_Mandante'].mean() if not hist_casa.empty else 0
        gols_contra_casa = hist_casa['Pontos_Visitante'].mean() if not hist_casa.empty else 0
        gols_pro_fora = hist_fora['Pontos_Visitante'].mean() if not hist_fora.empty else 0
        gols_contra_fora = hist_fora['Pontos_Mandante'].mean() if not hist_fora.empty else 0

        # Médias Extras (Novas Estatísticas)
        met_ataque_casa = hist_casa['Métrica_Ataque'].mean() if 'Métrica_Ataque' in df.columns and not hist_casa.empty else 0
        met_defesa_casa = hist_casa['Métrica_Defesa'].mean() if 'Métrica_Defesa' in df.columns and not hist_casa.empty else 0
        met_ataque_fora = hist_fora['Métrica_Ataque'].mean() if 'Métrica_Ataque' in df.columns and not hist_fora.empty else 0
        met_defesa_fora = hist_fora['Métrica_Defesa'].mean() if 'Métrica_Defesa' in df.columns and not hist_fora.empty else 0

        # Expectativa de Placar (Média de Gols)
        lambda_casa = (gols_pro_casa + gols_contra_fora) / 2
        lambda_fora = (gols_pro_fora + gols_contra_casa) / 2

        # --- EXIBIÇÃO DE CARD COM NOVAS ESTATÍSTICAS ---
        st.markdown("### 📊 Painel Geral de Médias")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"🏠 **{time_a}** (Casa)")
            st.metric("Média Pontos Feitos", f"{gols_pro_casa:.2f}")
            st.metric("Média Métrica Ataque (Ex: Escanteios)", f"{met_ataque_casa:.1f}")
            st.metric("Média Métrica Defesa (Ex: Faltas)", f"{met_defesa_casa:.1f}")
        with c2:
            st.success(f"🚀 **{time_b}** (Fora)")
            st.metric("Média Pontos Feitos", f"{gols_pro_fora:.2f}")
            st.metric("Média Métrica Ataque", f"{met_ataque_fora:.1f}")
            st.metric("Média Métrica Defesa", f"{met_defesa_fora:.1f}")

        # --- MODELAGEM DE IA (POISSON) ---
        st.markdown("### 🔮 Previsões de Probabilidade (Modelo de Poisson)")
        
        # Só calcula probabilidades detalhadas se for placar baixo (Futebol), para não quebrar a matriz no basquete
        if esporte_selecionado.lower() == 'futebol':
            max_gols = 6
            matriz_gols = np.outer(poisson.pmf(range(max_gols), lambda_casa), poisson.pmf(range(max_gols), lambda_fora))
            
            prob_vitoria_casa = np.sum(np.tril(matriz_gols, -1)) * 100
            prob_empate = np.sum(np.diag(matriz_gols)) * 100
            prob_vitoria_fora = np.sum(np.triu(matriz_gols, 1)) * 100
            
            # Gráfico de Pizza com as Probabilidades
            fig_pizza = go.Figure(data=[go.Pie(
                labels=[f'Vitória {time_a}', 'Empate', f'Vitória {time_b}'],
                values=[prob_vitoria_casa, prob_empate, prob_vitoria_fora],
                hole=.3,
                marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c']
            )])
            fig_pizza.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                st.write(f"**Probabilidade Matemática:**")
                st.write(f"🟩 **{time_a}:** {prob_vitoria_casa:.1f}%")
                st.write(f"🟨 **Empate:** {prob_empate:.1f}%")
                st.write(f"🟩 **{time_b}:** {prob_vitoria_fora:.1f}%")
            with col_p2:
                st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("💡 Modelo Probabilístico de 1X2 otimizado para Futebol. Para esportes de alta pontuação, utilize a projeção de placar abaixo.")

        # Projeção de Placar Final
        st.markdown("---")
        st.metric("🎯 Placar mais Provável Calculado pela IA", f"{lambda_casa:.1f} x {lambda_fora:.1f}")

        # --- TABELA DE HISTÓRICO ---
        st.markdown("### 📅 Histórico de Partidas na Planilha")
        jogos_recentes = df_esporte[
            (df_esporte['Mandante'] == time_a) | (df_esporte['Visitante'] == time_a) |
            (df_esporte['Mandante'] == time_b) | (df_esporte['Visitante'] == time_b)
        ].tail(5)
        st.dataframe(jogos_recentes, use_container_width=True)
