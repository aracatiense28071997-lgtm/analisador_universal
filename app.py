import streamlit as st
import pandas as pd
import numpy as np
import urllib.request

# Configuração visual do sistema Pro de Estatísticas Detalhadas
st.set_page_config(page_title="Analisador Estatístico Pro", page_icon="📊", layout="wide")

st.markdown("# 📊 Analisador de Performance e Estatísticas Profundas")
st.markdown("---")

# URLs oficiais de estatísticas detalhadas de equipes do FBref (Cobre Gols, Chutes, Faltas e Cartões)
LIGAS_ESTATISTICAS = {
    "Premier League (Inglaterra)": "https://fbref.com",
    "Brasileirão Série A": "https://fbref.com",
    "La Liga (Espanha)": "https://fbref.com",
    "Serie A (Itália)": "https://fbref.com",
    "Ligue 1 (França)": "https://fbref.com"
}

@st.cache_data(ttl=600)
def buscar_estatisticas_fbref(url_liga):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        req = urllib.request.Request(url_liga, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read()
            
        tabelas = pd.read_html(html)
        
        # Procura a tabela de estatísticas padrão das equipes (Squad Regular Season Stats)
        df_stats = pd.DataFrame()
        for t in tabelas:
            if isinstance(t.columns, pd.MultiIndex):
                t.columns = t.columns.get_level_values(-1)
            if 'Squad' in t.columns and 'MP' in t.columns and 'Gls' in t.columns:
                df_stats = t
                break
                
        if df_stats.empty:
            raise ValueError("Tabela de estatísticas não encontrada.")
            
        # Filtra e organiza apenas as métricas de performance reais por jogo
        df_stats = df_stats.dropna(subset=['Squad'])
        df_stats = df_stats[~df_stats['Squad'].str.contains('vs Opponent|Total')]
        
        # Tratamento numérico seguro das colunas do FBref
        df_stats['MP'] = pd.to_numeric(df_stats['MP'], errors='coerce').fillna(1)
        df_stats['Gls_Media'] = pd.to_numeric(df_stats['Gls'], errors='coerce') / df_stats['MP']
        df_stats['xG_Media'] = pd.to_numeric(df_stats['xG'], errors='coerce') / df_stats['MP']
        df_stats['Sh_Media'] = pd.to_numeric(df_stats['Sh'], errors='coerce') / df_stats['MP']
        df_stats['CrdY_Media'] = pd.to_numeric(df_stats['CrdY'], errors='coerce') / df_stats['MP']
        df_stats['Fls_Media'] = pd.to_numeric(df_stats['Fls'], errors='coerce', default=12.5) / df_stats['MP']
        
        return df_stats[['Squad', 'MP', 'Gls_Media', 'xG_Media', 'Sh_Media', 'CrdY_Media', 'Fls_Media']]
    except Exception as e:
        st.error(f"Erro ao conectar com a base estatística: {e}")
        return pd.DataFrame()

# --- INTERFACE DE SELEÇÃO ---
st.sidebar.header("🔍 Seleção de Campeonato")
liga_escolhida = st.sidebar.selectbox("1. Escolha a Liga", list(LIGAS_ESTATISTICAS.keys()))

df = buscar_estatisticas_fbref(LIGAS_ESTATISTICAS[liga_escolhida])

if df.empty:
    st.warning("Tentando reestabelecer conexão com o servidor de dados esportivos...")
else:
    # Limpa nomes de equipes
    df['Squad'] = df['Squad'].astype(str).str.strip()
    todos_times = sorted(df['Squad'].unique())
    
    st.sidebar.header("🔍 Seleção Automática de Jogos")
    time_a = st.sidebar.selectbox("2. Escolha o Mandante (Casa)", todos_times)
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Escolha o Visitante (Fora)", times_disponiveis_b)

    # --- ABA PRINCIPAL: TABELA GERAL DE PERFORMANCE TÉCNICA ---
    st.markdown(f"### 🏆 Painel de Médias de Performance por Jogo: {liga_escolhida}")
    tabela_exibicao = df.rename(columns={
        'Squad': 'Equipe', 'MP': 'Partidas', 'Gls_Media': 'Média Gols',
        'xG_Media': 'Média xG (Criado)', 'Sh_Media': 'Média Chutes',
        'CrdY_Media': 'Média Cartões', 'Fls_Media': 'Média Faltas'
    }).set_index('Equipe')
    
    st.dataframe(tabela_exibicao.style.format(precision=2), use_container_width=True)

    if st.sidebar.button("🚀 Processar Análise Profunda"):
        st.markdown("---")
        st.subheader(f"🏟️ Estatísticas Avançadas Comparativas: {time_a} vs {time_b}")
        
        stats_a = df[df['Squad'] == time_a].iloc[0]
        stats_b = df[df['Squad'] == time_b].iloc[0]
        
        # --- TABELA DE MÉDRICAS COMPARATIVAS ESTILO SOFASCORE ---
        dados_comparativos = {
            "Métrica de Desempenho (Média por Jogo)": [
                "Média de Gols Marcados", 
                "Expected Goals - Gols Esperados (xG)", 
                "Total de Chutes Realizados", 
                "Média de Faltas Cometidas",
                "Média de Cartões Amarelos"
            ],
            time_a: [
                f"{stats_a['Gls_Media']:.2f}", 
                f"{stats_a['xG_Media']:.2f}", 
                f"{stats_a['Sh_Media']:.1f}", 
                f"{stats_a['Fls_Media']:.1f}",
                f"{stats_a['CrdY_Media']:.1f}"
            ],
            time_b: [
                f"{stats_b['Gls_Media']:.2f}", 
                f"{stats_b['xG_Media']:.2f}", 
                f"{stats_b['Sh_Media']:.1f}", 
                f"{stats_b['Fls_Media']:.1f}",
                f"{stats_b['CrdY_Media']:.1f}"
            ]
        }
        st.table(pd.DataFrame(dados_comparativos))
        
        # --- SISTEMA DE PREVISÃO REORGANIZADO ---
        st.markdown("### 🎯 O Veredito Estatístico do Confronto")
        
        total_gols_esperado = stats_a['Gls_Media'] + stats_b['Gls_Media']
        total_chutes_esperado = stats_a['Sh_Media'] + stats_b['Sh_Media']
        total_cartoes_esperado = stats_a['CrdY_Media'] + stats_b['CrdY_Media']
        
        tip_gols = "OVER 2.5 Gols" if total_gols_esperado >= 2.45 else "UNDER 2.5 Gols"
        tip_cartoes = "OVER 3.5 Cartões" if total_cartoes_esperado >= 3.5 else "UNDER 3.5 Cartões"
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total de Gols Esperados", f"{total_gols_esperado:.2f}")
        with c2:
            st.metric("Total de Chutes Previstos", f"{total_chutes_esperado:.1f}")
        with c3:
            st.metric("Total de Cartões Estimados", f"{total_cartoes_esperado:.1f}")
            
        st.success(f"🔥 **Recomendação Principal da IA:** {tip_gols} | **Tendência Secundária:** {tip_cartoes}")

