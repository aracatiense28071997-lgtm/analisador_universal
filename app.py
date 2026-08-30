import streamlit as st
import pandas as pd
import numpy as np

# Configuração visual do sistema
st.set_page_config(page_title="Tipster Pro AI", page_icon="⚽", layout="wide")

st.markdown("# ⚽ Analisador de Mercados & Green Garantido")
st.markdown("---")

# URL da sua planilha do Google Sheets configurada com o seu ID correto 
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTZlqND0nXrDDPcDo1ms1oWX0l0CDdFf9BisIYMaWC2wS1xoO3ZwAkc6Qe3sKGWR5a921vsJMinrHo5/pub?output=csv"

@st.cache_data(ttl=15) 
def carregar_dados():
    try:
        dados = pd.read_csv(URL_CSV)
        # Garantir conversão numérica das colunas necessárias
        dados['Pontos_Mandante'] = pd.to_numeric(dados['Pontos_Mandante'], errors='coerce')
        dados['Pontos_Visitante'] = pd.to_numeric(dados['Pontos_Visitante'], errors='coerce')
        dados['Escanteios'] = pd.to_numeric(dados['Escanteios'], errors='coerce')
        dados['Cartoes'] = pd.to_numeric(dados['Cartoes'], errors='coerce')
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.warning("⚠️ Adicione dados na sua planilha do Google Sheets para começar.")
else:
    # Filtro fixo para futebol para atender sua nova exigência
    df_futebol = df[df['Esporte'].str.lower() == 'futebol'] if 'Esporte' in df.columns else df
    
    if df_futebol.empty:
        st.warning("⚠️ Cadastre partidas com o esporte 'Futebol' na sua planilha para usar este módulo.")
    else:
        # --- INTERFACE DE SELEÇÃO ---
        st.sidebar.header("🔍 Selecionar Confronto")
        todos_times = sorted(list(set(df_futebol['Mandante'].unique()).union(set(df_futebol['Visitante'].unique()))))
        
        time_a = st.sidebar.selectbox("Mandante (Casa)", todos_times)
        times_disponiveis_b = [t for t in todos_times if t != time_a]
        time_b = st.sidebar.selectbox("Visitante (Fora)", times_disponiveis_b)

        if st.sidebar.button("🚀 Gerar Melhor Entrada"):
            st.subheader(f"🏟️ Confronto: {time_a} vs {time_b}")
            
            # Filtros de Histórico
            hist_casa = df_futebol[(df_futebol['Mandante'] == time_a)]
            hist_fora = df_futebol[(df_futebol['Visitante'] == time_b)]
            
            if hist_casa.empty or hist_fora.empty:
                st.warning("⚠️ Dados históricos insuficientes para um dos times jogando nesta condição (Casa/Fora).")
            else:
                # 1. Cálculos de Gols (Over/Under 2.5 como padrão de mercado)
                media_gols_casa = (hist_casa['Pontos_Mandante'].mean() + hist_casa['Pontos_Visitante'].mean())
                media_gols_fora = (hist_fora['Pontos_Mandante'].mean() + hist_fora['Pontos_Visitante'].mean())
                expectativa_gols = (media_gols_casa + media_gols_fora) / 2
                tip_gols = "OVER 2.5 Gols" if expectativa_gols >= 2.5 else "UNDER 2.5 Gols"
                confianca_gols = abs(expectativa_gols - 2.5) # Margem de distância da linha comum

                # 2. Cálculos de Escanteios (Over/Under 9.5 como padrão de mercado)
                media_cantos_casa = hist_casa['Escanteios'].mean() if 'Escanteios' in df_futebol.columns else 0
                media_cantos_fora = hist_fora['Escanteios'].mean() if 'Escanteios' in df_futebol.columns else 0
                expectativa_cantos = (media_cantos_casa + media_cantos_fora) / 2
                tip_cantos = "OVER 9.5 Escanteios" if expectativa_cantos >= 9.5 else "UNDER 9.5 Escanteios"
                confianca_cantos = abs(expectativa_cantos - 9.5)

                # 3. Cálculos de Cartões (Over/Under 4.5 como padrão de mercado)
                media_cartoes_casa = hist_casa['Cartoes'].mean() if 'Cartoes' in df_futebol.columns else 0
                media_cartoes_fora = hist_fora['Cartoes'].mean() if 'Cartoes' in df_futebol.columns else 0
                expectativa_cartoes = (media_cartoes_casa + media_cartoes_fora) / 2
                tip_cartoes = "OVER 4.5 Cartões" if expectativa_cartoes >= 4.5 else "UNDER 4.5 Cartões"
                confianca_cartoes = abs(expectativa_cartoes - 4.5)

                # 4. Cálculo do Resultado Final
                gols_pro_casa = hist_casa['Pontos_Mandante'].mean()
                gols_contra_casa = hist_casa['Pontos_Visitante'].mean()
                gols_pro_fora = hist_fora['Pontos_Visitante'].mean()
                gols_contra_fora = hist_fora['Pontos_Mandante'].mean()
                
                placar_casa = (gols_pro_casa + gols_contra_fora) / 2
                placar_fora = (gols_pro_fora + gols_contra_casa) / 2
                
                if placar_casa > placar_fora + 0.3:
                    resultado_final = f"Vitória do Mandante ({time_a})"
                    confianca_resultado = abs(placar_casa - placar_fora)
                elif placar_fora > placar_casa + 0.3:
                    resultado_final = f"Vitória do Visitante ({time_b})"
                    confianca_resultado = abs(placar_fora - placar_casa)
                else:
                    resultado_final = "Empate / Match Odds Equilibrado"
                    confianca_resultado = 0.5

                # --- EXIBIÇÃO EM TABELA DOS MERCADOS ---
                st.markdown("### 📊 Tendências de Linha Calculadas")
                
                dados_mercado = {
                    "Mercado Analisado": ["Resultado Final", "Total de Gols", "Total de Escanteios", "Total de Cartões"],
                    "Projeção Média Real": [f"{placar_casa:.1f} x {placar_fora:.1f}", f"{expectativa_gols:.1f} Gols", f"{expectativa_cantos:.1f} Cantos", f"{expectativa_cartoes:.1f} Cartões"],
                    "Tendência do Jogo": [resultado_final, tip_gols, tip_cantos, tip_cartoes]
                }
                st.table(pd.DataFrame(dados_mercado))

                # --- ELEIÇÃO DA MELHOR ENTRADA (MAIOR MARGEM DE SEGURANÇA) ---
                st.markdown("---")
                st.markdown("## 👑 A MELHOR ENTRADA PARA ESTA PARTIDA")
                
                # Mapeia qual mercado se distanciou mais da linha de risco (maior margem estatística)
                dicionario_confianca = {
                    f"🏆 Mercado: Resultado Final -> **{resultado_final}**": confianca_resultado,
                    f"⚽ Mercado: Gols -> **{tip_gols}** (Média projetada de {expectativa_gols:.1f})": confianca_gols,
                    f"📐 Mercado: Escanteios -> **{tip_cantos}** (Média projetada de {expectativa_cantos:.1f})": confianca_cantos,
                    f"🟨 Mercado: Cartões -> **{tip_cartoes}** (Média projetada de {expectativa_cartoes:.1f})": confianca_cartoes
                }
                
                melhor_entrada = max(dicionario_confianca, key=dicionario_confianca.get)
                
                st.success(f"🔥 **Recomendação Principal da IA:** {melhor_entrada}")
                st.caption("Nota: A melhor entrada é escolhida automaticamente calculando qual mercado possui a maior distância estatística das linhas convencionais de aposta (maior margem de segurança).")
