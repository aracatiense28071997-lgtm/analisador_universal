import urllib.request

@st.cache_data(ttl=3600)
def raspar_dados_fbref():
    try:
        url = "https://fbref.com"
        
        # Cria uma requisição fingindo ser um navegador Google Chrome no Windows
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        
        # Abre o site com a identidade falsa e joga no Pandas
        with urllib.request.urlopen(req) as response:
            html = response.read()
            
        tabelas = pd.read_html(html)
        df_jogos = tabelas[0]
        
        df_jogos = df_jogos.dropna(subset=['Home', 'Away'])
        df_jogos = df_jogos.rename(columns={
            'Home': 'Mandante',
            'Away': 'Visitante',
            'Score': 'Placar'
        })
        
        df_jogos[['Gols_Mandante', 'Gols_Visitante']] = df_jogos['Placar'].str.split('–', expand=True)
        df_jogos['Gols_Mandante'] = pd.to_numeric(df_jogos['Gols_Mandante'], errors='coerce')
        df_jogos['Gols_Visitante'] = pd.to_numeric(df_jogos['Gols_Visitante'], errors='coerce')
        
        return df_jogos
    except Exception as e:
        st.error(f"Erro ao raspar dados em tempo real: {e}. Carregando simulador de contingência.")
        dados_seguranca = {
            'Mandante': ['Athletico-PR', 'Flamengo', 'Corinthians', 'Mirassol', 'Grêmio', 'Bahia'],
            'Visitante': ['Fluminense', 'Botafogo', 'Santos', 'Palmeiras', 'Chapecoense', 'Internacional'],
            'Gols_Mandante': [1.4, 2.1, 1.1, 0.9, 1.8, 1.5],
            'Gols_Visitante': [0.9, 1.2, 1.0, 1.7, 0.8, 1.1]
        }
        return pd.DataFrame(dados_seguranca)

    st.success(f"🔥 **Palpite de Alta Confiança da IA:** {melhor_opcao}")
