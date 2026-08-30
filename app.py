import streamlit as st
import pandas as pd
import numpy as np
import asyncio
from understat import Understat
import aiohttp

# Configuração visual do sistema Pro de Estatísticas Detalhadas
st.set_page_config(page_title="Analisador Estatístico Pro", page_icon="📊", layout="wide")

st.markdown("# 📊 Analisador de Performance e Estatísticas Profundas")
st.markdown("---")

LIGAS_UNDERSTAT = {
    "Premier League (Inglaterra)": "EPL",
    "La Liga (Espanha)": "La_Liga",
    "Serie A (Itália)": "Serie_A",
    "Ligue 1 (França)": "Ligue_1"
}

# Nova função assíncrona utilizando o conector oficial do Understat
async def obter_dados(liga_sigla):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        # Busca os dados oficiais de todas as equipes na temporada atual
        teams = await understat.get_teams(liga_sigla, 2026) # Configurado para o ano atual
        
        linhas = []
        for team in teams:
            nome_time = team['title']
            # O conector oficial separa as estatísticas de ataque e defesa mastigadas
            gols_feitos = int(team['history'][0]['g']) if team['history'] else 0
            linhas.append({
                'Equipe': nome_time,
                'Gols_Feitos': gols_feitos,
                'xG_Criado': float(team['stats']['seasons'][0]['xG']) if 'stats' in team else 0.0,
                'xG_Concedido': float(team['stats']['seasons'][0]['xG_allowed']) if 'stats' in team else 0.0,
                'Chutes_Realizados': float(team['stats']['seasons'][0]['shots']) if 'stats' in team else 0.0,
                'Chutes_Concedidos': float(team['stats']['seasons'][0]['shots_allowed']) if 'stats' in team else 0.0,
                'Passes_Terço_Final': float(team['stats']['seasons'][0]['deep']) if 'stats' in team else 0.0,
                'Faltas_Cometidas': float(team['stats']['seasons'][0]['fouls']) if 'stats' in team else 0.0
            })
        return pd.DataFrame(linhas)

@st.cache_data(ttl=600)
def buscar_dados_understat(liga_nome):
    try:
        # Roda o conector oficial dentro do ambiente síncrono do Streamlit
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        df_resultado = loop.run_until_complete(obter_dados(LIGAS_UNDERSTAT[liga_nome]))
        return df_resultado
    except Exception as e:
        st.error(f"Erro ao conectar com a base oficial: {e}")
        return pd.DataFrame()

# --- INTERFACE DE SELEÇÃO ---
st.sidebar.header("🔍 Seleção de Campeonato")
liga_escolhida = st.sidebar.selectbox("1. Escolha a Liga Europeia", list(LIGAS_UNDERSTAT.keys()))

df = buscar_dados_understat(liga_escolhida)

if df.empty:
    st.warning("Aguardando resposta do servidor oficial de estatísticas...")
else:
    todos_times = sorted(df['Equipe'].unique())
    
    st.sidebar.header("🔍 Seleção Automática de Jogos")
    time_a = st.sidebar.selectbox("2. Escolha o Mandante (Casa)", todos_times)
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Escolha o Visitante (Fora)", times_disponiveis_b)

    # --- ABA PRINCIPAL: CLASSIFICAÇÃO POR DESEMPENHO TÉCNICO ---
    st.markdown(f"### 🏆 Classificação Técnica de Performance: {liga_escolhida}")
    tabela_resumo = df.set_index('Equipe').sort_values(by='xG_Criado', ascending=False)
    st.dataframe(tabela_resumo, use_container_width=True)

    if st.sidebar.button("🚀 Processar Análise Profunda"):
        st.markdown("---")
        st.subheader(f"🏟️ Estatísticas Avançadas Comparativas: {time_a} vs {time_b}")
        
        stats_a = df[df['Equipe'] == time_a].iloc[0]
        stats_b = df[df['Equipe'] == time_b].iloc[0]
        
        dados_comparativos = {
            "Métrica de Desempenho (Acumulado Temporada)": [
                "Expected Goals - Gols Esperados (xG)", 
                "Total de Chutes Realizados", 
                "Passes no Terço Final do Campo",
                "Faltas Cometidas"
            ],
            time_a: [
                f"{stats_a['xG_Criado']:.2f}", 
                f"{stats_a['Chutes_Realizados']:.0f}", 
                f"{stats_a['Passes_Terço_Final']:.0f}",
                f"{stats_a['Faltas_Cometidas']:.0f}"
            ],
            time_b: [
                f"{stats_b['xG_Criado']:.2f}", 
                f"{stats_b['Chutes_Realizados']:.0f}", 
                f"{stats_b['Passes_Terço_Final']:.0f}",
                f"{stats_b['Faltas_Cometidas']:.0f}"
            ]
        }
        st.table(pd.DataFrame(dados_comparativos))
        
        st.markdown("### 🎯 O Veredito Estatístico do Confronto")
        
        expectativa_gols_a = (stats_a['xG_Criado'] + stats_b['xG_Concedido']) / 38
        expectativa_gols_b = (stats_b['xG_Criado'] + stats_a['xG_Concedido']) / 38
        total_gols_esperado = expectativa_gols_a + expectativa_gols_b
        
        tip_gols = "OVER 2.5 Gols" if total_gols_esperado >= 2.5 else "UNDER 2.5 Gols"
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Projeção de Placar para Hoje (Base xG)", f"{expectativa_gols_a:.1f} x {expectativa_gols_b:.1f}")
        with c2:
            st.metric("Média de Chutes das Equipes (Por Jogo)", f"{(stats_a['Chutes_Realizados'] + stats_b['Chutes_Realizados'])/38:.1f}")
            
        st.success(f"🔥 **Recomendação Baseada em Volume de Jogo Real:** {tip_gols}")

