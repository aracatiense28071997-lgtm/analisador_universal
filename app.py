import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import re
from bs4 import BeautifulSoup

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

@st.cache_data(ttl=600)
def buscar_dados_understat(liga_nome):
    try:
        url = f"https://understat.com/league/{LIGAS_UNDERSTAT[liga_nome]}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'lxml')
        scripts = soup.find_all('script')
        
        # Procura o bloco JSON contendo as estatísticas completas de todas as equipes
        dados_times = None
        for s in scripts:
            if s.string and 'teamsData' in s.string:
                match = re.search(r"teamsData\s*=\s*JSON\.parse\('([^']+)'\)", s.string)
                if match:
                    # Decodifica o JSON criptografado na página do Understat
                    raw_data = match.group(1)
                    dados_bytes = raw_data.encode('utf-8').decode('unicode-escape')
                    dados_times = json.loads(dados_bytes)
                    break
        
        if not dados_times:
            raise ValueError("Dados não encontrados")
            
        # Organiza as estatísticas avançadas em uma tabela limpa
        linhas = []
        for id_time, info in dados_times.items():
            nome_time = info['title']
            historico = info['history']
            for jogo in historico:
                linhas.append({
                    'Equipe': nome_time,
                    'Gols_Feitos': jogo['g'],
                    'Gols_Sofridos': jogo['ga'],
                    'xG_Criado': jogo['xG'],
                    'xG_Concedido': jogo['xGA'],
                    'Chutes_Realizados': jogo['shots'],
                    'Chutes_Concedidos': jogo['sh_allowed'],
                    'Passes_Terço_Final': jogo['deep'],
                    'Faltas_Cometidas': jogo['ppda']['fouls']
                })
                
        return pd.DataFrame(linhas)
    except Exception as e:
        st.error(f"Erro ao conectar com a base estatística: {e}")
        return pd.DataFrame()

# --- INTERFACE DE SELEÇÃO ---
st.sidebar.header("🔍 Seleção de Campeonato")
liga_escolhida = st.sidebar.selectbox("1. Escolha a Liga Europeia", list(LIGAS_UNDERSTAT.keys()))

df = buscar_dados_understat(liga_escolhida)

if df.empty:
    st.warning("Aguardando resposta do servidor de dados...")
else:
    todos_times = sorted(df['Equipe'].unique())
    
    st.sidebar.header("🔍 Seleção Automática de Jogos")
    time_a = st.sidebar.selectbox("2. Escolha o Mandante (Casa)", todos_times)
    times_disponiveis_b = [t for t in todos_times if t != time_a]
    time_b = st.sidebar.selectbox("3. Escolha o Visitante (Fora)", times_disponiveis_b)

    # --- ABA PRINCIPAL: CLASSIFICAÇÃO POR DESEMPENHO TÉCNICO ---
    st.markdown(f"### 🏆 Classificação Técnica de Performance: {liga_escolhida}")
    tabela_resumo = df.groupby('Equipe').agg({
        'Gols_Feitos': 'sum',
        'xG_Criado': 'sum',
        'Chutes_Realizados': 'sum',
        'Passes_Terço_Final': 'sum',
        'Faltas_Cometidas': 'sum'
    }).sort_values(by='xG_Criado', ascending=False)
    
    st.dataframe(tabela_resumo, use_container_width=True)

    if st.sidebar.button("🚀 Processar Análise Profunda"):
        st.markdown("---")
        st.subheader(f"🏟️ Estatísticas Avançadas Comparativas: {time_a} vs {time_b}")
        
        # Separa as médias de cada equipe na temporada
        stats_a = df[df['Equipe'] == time_a].mean(numeric_only=True)
        stats_b = df[df['Equipe'] == time_b].mean(numeric_only=True)
        
        # --- TABELA DE MÉDRICAS COMPARATIVAS ESTILO SOFASCORE ---
        dados_comparativos = {
            "Métrica de Desempenho (Média por Jogo)": [
                "Média de Gols Marcados", 
                "Expected Goals - Gols Esperados (xG)", 
                "Total de Chutes Realizados", 
                "Passes no Terço Final do Campo",
                "Faltas Cometidas"
            ],
            time_a: [
                f"{stats_a['Gols_Feitos']:.2f}", 
                f"{stats_a['xG_Criado']:.2f}", 
                f"{stats_a['Chutes_Realizados']:.1f}", 
                f"{stats_a['Passes_Terço_Final']:.1f}",
                f"{stats_a['Faltas_Cometidas']:.1f}"
            ],
            time_b: [
                f"{stats_b['Gols_Feitos']:.2f}", 
                f"{stats_b['xG_Criado']:.2f}", 
                f"{stats_b['Chutes_Realizados']:.1f}", 
                f"{stats_b['Passes_Terço_Final']:.1f}",
                f"{stats_b['Faltas_Cometidas']:.1f}"
            ]
        }
        st.table(pd.DataFrame(dados_comparativos))
        
        # --- SISTEMA DE PREVISÃO REORGANIZADO ---
        st.markdown("### 🎯 O Veredito Estatístico do Confronto")
        
        # Cruzamento de xG de ataque contra xG de defesa
        expectativa_gols_a = (stats_a['xG_Criado'] + stats_b['xG_Concedido']) / 2
        expectativa_gols_b = (stats_b['xG_Criado'] + stats_a['xG_Concedido']) / 2
        total_gols_esperado = expectativa_gols_a + expectativa_gols_b
        
        tip_gols = "OVER 2.5 Gols" if total_gols_esperado >= 2.5 else "UNDER 2.5 Gols"
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Placar de Gols Esperados (xG Proved)", f"{expectativa_gols_a:.1f} x {expectativa_gols_b:.1f}")
        with c2:
            st.metric("Total de Chutes Previstos na Partida", f"{stats_a['Chutes_Realizados'] + stats_b['Chutes_Realizados']:.1f}")
            
        st.success(f"🔥 **Recomendação Baseada em Volume de Jogo e xG:** {tip_gols} (Projeção de {total_gols_esperado:.2f} gols com alto volume de finalizações)")


