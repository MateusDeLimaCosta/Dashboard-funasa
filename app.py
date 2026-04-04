import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px  # <-- ADICIONE ESTA LINHA
from dados import obter_dados_visao_executiva  # <-- ADICIONE ESTA LINHA

# Puxa os dados reais do banco assim que o app liga
df_visao = obter_dados_visao_executiva()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA, dbc.icons.BOOTSTRAP])
server = app.server  # Para quando for subir no Heroku ou similar

# ==========================================
# GERAÇÃO DOS GRÁFICOS REAIS (PLOTLY)
# ==========================================

# 1. FILTRO DE OUTLIERS: Removemos os Polos de Saúde (ex: Jaci) para ver a tendência real
limite_maximo = df_visao['taxa_internacao_100k'].quantile(0.95) # Corta os 5% maiores
df_limpo = df_visao[df_visao['taxa_internacao_100k'] < limite_maximo]

# 2. Cria o gráfico usando o df_limpo (já sem as anomalias)
fig_correlacao = px.scatter(
    df_limpo, 
    x="percentual_cobertura_esgoto", 
    y="taxa_internacao_100k", 
    hover_name="municipio",
    color="uf",
    opacity=0.7, # Bolinhas levemente transparentes
    labels={
        "percentual_cobertura_esgoto": "Cobertura de Esgoto (%)", 
        "taxa_internacao_100k": "Internações (por 100 mil hab.)"
    },
    template="plotly_white"
)

# 3. Ajustes finais de design (borda nas bolinhas e fundo transparente)
fig_correlacao.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
fig_correlacao.update_layout(
    margin=dict(l=20, r=20, t=30, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

# ==========================================
# CÁLCULO DOS KPIs E RANKING (PANDAS)
# ==========================================

# 1. Calculando Totais para os Cards
populacao_total = df_visao['populacao_total'].sum()
internacoes_totais = df_visao['internacoes_clinicas'].sum()
custo_total_sus = df_visao['custo_total'].sum()

# Formatando os números para ficarem elegantes no dashboard (ex: 210.5M, R$ 45.2M)
pop_formatada = f"{populacao_total / 1e6:.1f}M"
int_formatada = f"{internacoes_totais:,.0f}".replace(',', '.')
custo_formatado = f"R$ {custo_total_sus / 1e9:.1f}B"

# 2. Criando o Gráfico de "Municípios em Alerta Máximo" (Top 5 piores taxas)
df_alerta = df_limpo.nlargest(5, 'taxa_internacao_100k').sort_values('taxa_internacao_100k', ascending=True)

fig_alerta = px.bar(
    df_alerta, 
    x="taxa_internacao_100k", 
    y="municipio", 
    orientation='h', # Barras deitadas para ler melhor o nome da cidade
    color="percentual_cobertura_esgoto", 
    color_continuous_scale="Reds_r", # Quanto mais vermelho, menor a cobertura de esgoto
    labels={"taxa_internacao_100k": "Taxa de Internação", "municipio": "", "percentual_cobertura_esgoto": "Esgoto (%)"},
    template="plotly_white"
)

fig_alerta.update_layout(
    margin=dict(l=0, r=20, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    coloraxis_showscale=False # Esconde a barrinha de cor lateral para economizar espaço
)

# 3. Criando o Treemap de Impacto por Estado
# Removemos cidades com custo zerado só para o gráfico de árvore não dar erro
df_treemap = df_limpo[df_limpo['custo_total'] > 0]

fig_estado = px.treemap(
    df_treemap,
    path=[px.Constant("Brasil"), 'uf', 'municipio'], # A hierarquia do zoom
    values='custo_total', # O tamanho do quadrado
    color='percentual_cobertura_esgoto', # A cor do quadrado
    color_continuous_scale='RdYlGn', # Vermelho (ruim) -> Amarelo -> Verde (bom)
    labels={'percentual_cobertura_esgoto': 'Esgoto (%)', 'custo_total': 'Custo (R$)'},
    template="plotly_white"
)

fig_estado.update_layout(
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

# ==========================================
# COMPONENTES DA INTERFACE
# ==========================================

sidebar = html.Div([
    html.Div([
        # A imagem da logo puxada da pasta assets
        html.Img(src="/assets/logo_funasa.png", style={"width": "140px", "marginBottom": "15px"}),
        
        # O nome do seu "produto"
        #html.H5("OBSERVATÓRIO", className="brand-title", style={"color": "#0A192F", "fontWeight": "800", "fontSize": "1.2rem", "marginBottom": "2px"}),
        
        # O subtítulo explicando o escopo
        html.P("SAÚDE & SANEAMENTO", className="brand-subtitle", style={"color": "#22C55E", "fontWeight": "700"}), # Um verde para combinar com o tema
    ], className="sidebar-header", style={"textAlign": "center", "padding": "10px 0 20px 0"}),
    
    html.Hr(),
    
dbc.Nav([
            # Aba 1: O cruzamento geral
            dbc.NavLink([html.I(className="bi bi-grid-fill me-2"), "Visão Executiva"], href="/", active="exact", className="nav-link-custom"),
            
            # Aba 2: Foco em Esgoto/Água
            dbc.NavLink([html.I(className="bi bi-droplet-half me-2"), "Saneamento Básico"], href="/saneamento", active="exact", className="nav-link-custom"),
            
            # Aba 3: Foco em Hospitalizações
            dbc.NavLink([html.I(className="bi bi-heart-pulse me-2"), "Saúde Pública (SUS)"], href="/saude", active="exact", className="nav-link-custom"),
            
            # Aba 4: Filtros Livres
            dbc.NavLink([html.I(className="bi bi-funnel me-2"), "Exploração Dinâmica"], href="/exploracao", active="exact", className="nav-link-custom"),
            
        ], vertical=True, pills=True, className="flex-grow-1"),
    
    html.Div([
        dbc.NavLink([html.I(className="bi bi-box-arrow-right me-2"), "Sair"], href="#", className="nav-link-custom text-muted"),
    ], className="sidebar-footer")
], className="sidebar")

topbar = html.Div([
    # Quadrado Rosa/Roxo: Agora apenas com o ícone de informação
    html.Div([
        # O ícone precisa de um ID para que o Tooltip saiba onde "grudar"
        html.I(
            className="bi bi-question-circle text-muted fs-4", 
            id="icone-info-dashboard",
            style={"cursor": "help"} # Muda o mouse para uma interrogação ao passar por cima
        ),
        
        # O balãozinho de texto (Tooltip)
        dbc.Tooltip(
            "Dashboard desenvolvido para cruzamento de dados de infraestrutura de saneamento e impactos na saúde pública (SUS).",
            target="icone-info-dashboard",
            placement="bottom",
        )
    ], className="user-section d-flex align-items-center")
], className="topbar d-flex justify-content-between align-items-center")

header_section = html.Div([
    html.P("INSTITUCIONAL FUNASA", className="section-pretitle text-success fw-bold mb-1"),
    html.H1("Visão Geral da Saúde e Saneamento", className="section-title fw-bold mb-2"),
    html.P("Monitoramento em tempo real das metas de cobertura vacinal, saneamento rural e distribuição de recursos hídricos em todo o território nacional.", className="text-muted")
], className="mb-4")


# KPI Cards
kpi_cards = dbc.Row([
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([html.I(className="bi bi-people-fill text-primary fs-4")], className="icon-box bg-light-primary"),
            html.Div("Censo 2022", className="trend-badge text-primary"),
            html.P("POPULAÇÃO ANALISADA", className="kpi-label mt-3"),
            html.H2(pop_formatada, className="kpi-value"), # <-- Variável real aqui
            html.Div(className="progress-bar-custom bg-dark-blue w-100 mt-2")
        ])
    ], className="kpi-card shadow-sm border-0"), width=4),
    
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([html.I(className="bi bi-hospital text-danger fs-4")], className="icon-box bg-light-danger", style={"backgroundColor": "#FEE2E2"}),
            html.Div("SUS", className="trend-badge text-danger"),
            html.P("INTERNAÇÕES CLÍNICAS", className="kpi-label mt-3"),
            html.H2(int_formatada, className="kpi-value"), # <-- Variável real aqui
            html.P("Acumulado histórico na base", className="text-muted small mt-2 mb-0")
        ])
    ], className="kpi-card shadow-sm border-0 border-bottom-danger", style={"borderBottom": "4px solid #EF4444"}), width=4),
    
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.Div([html.I(className="bi bi-cash-stack text-warning fs-4")], className="icon-box bg-light-warning"),
            html.Div("Impacto", className="trend-badge text-warning"),
            html.P("CUSTO ESTIMADO", className="kpi-label mt-3"),
            html.H2(custo_formatado, className="kpi-value"), # <-- Variável real aqui
            html.P("Gasto público total", className="text-muted small mt-2 mb-0")
        ])
    ], className="kpi-card shadow-sm border-0 border-bottom-warning"), width=4),
], className="mb-4")

# ==========================================
# ÁREA DOS GRÁFICOS (ROW PRINCIPAL)
# ==========================================
graficos_mockup = dbc.Row([
    
    # --- PRIMEIRA COLUNA (Dispersão) ---
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H5("Relação: Saneamento vs. Internações", className="fw-bold"),
            html.P("Cidades com menor cobertura tendem a ter taxas mais altas", className="text-muted small mb-4"),
            
            # Gráfico real do Plotly
            dcc.Graph(figure=fig_correlacao, config={'displayModeBar': False})
            
        ])
    ], className="shadow-sm border-0 h-100"), width=8),
    
    # --- SEGUNDA COLUNA (Ranking) ---
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H5("Municípios em Alerta Máximo", className="fw-bold text-danger"),
            html.P("Maiores taxas de internação do país", className="text-muted small mb-4"),
            
            # Gráfico de Barras com as piores cidades
            dcc.Graph(figure=fig_alerta, config={'displayModeBar': False}, style={"height": "250px"})
            
        ])
    ], className="shadow-sm border-0 h-100"), width=4)

], className="mb-4 g-4") # <--- AQUI É ONDE FECHA O ROW PRINCIPAL!

# ==========================================
# ÁREA INFERIOR (TREEMAP ESTADUAL)
# ==========================================
banner_nacional = dbc.Row([
    dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H5("Raio-X Nacional: Impacto Financeiro vs. Infraestrutura", className="fw-bold"),
            html.P("Tamanho do bloco: Custo total de internações | Cor: Cobertura de esgoto (Vermelho = Crítico)", className="text-muted small mb-3"),
            
            # O nosso novo super gráfico interativo
            dcc.Graph(figure=fig_estado, style={"height": "400px"})
            
        ])
    ], className="shadow-sm border-0"), width=12)
], className="mb-4")



# ==========================================
# CÁLCULOS E GRÁFICOS: ABA 2 (SANEAMENTO)
# ==========================================

# 1. Calculando o Déficit Real (População sem Esgoto)
# Se a cidade tem 100 mil hab e 60% de esgoto, 40 mil estão sem.
df_limpo['pop_sem_esgoto'] = df_limpo['populacao_total'] * (1 - (df_limpo['percentual_cobertura_esgoto'] / 100))
total_sem_esgoto = df_limpo['pop_sem_esgoto'].sum()
deficit_formatado = f"{total_sem_esgoto / 1e6:.1f}M"

media_nacional_esgoto = df_limpo['percentual_cobertura_esgoto'].mean()

# 2. Gráfico: Média de Esgoto por Estado (UF)
df_uf = df_limpo.groupby('uf')['percentual_cobertura_esgoto'].mean().reset_index().sort_values('percentual_cobertura_esgoto')
fig_uf_esgoto = px.bar(
    df_uf, 
    x='percentual_cobertura_esgoto', 
    y='uf', 
    orientation='h',
    color='percentual_cobertura_esgoto',
    color_continuous_scale='RdYlGn',
    labels={'percentual_cobertura_esgoto': 'Cobertura Média (%)', 'uf': 'Estado'},
    template="plotly_white"
)
fig_uf_esgoto.update_layout(margin=dict(l=0, r=20, t=20, b=0), coloraxis_showscale=False)

# 3. Gráficos: Top 10 Piores e Melhores
df_piores = df_limpo.nsmallest(10, 'percentual_cobertura_esgoto').sort_values('percentual_cobertura_esgoto', ascending=False)
fig_piores = px.bar(df_piores, x='percentual_cobertura_esgoto', y='municipio', orientation='h', color_discrete_sequence=['#EF4444'], template="plotly_white", labels={'percentual_cobertura_esgoto': '%', 'municipio': ''})
fig_piores.update_layout(margin=dict(l=0, r=0, t=0, b=0))

df_melhores = df_limpo.nlargest(10, 'percentual_cobertura_esgoto').sort_values('percentual_cobertura_esgoto', ascending=True)
fig_melhores = px.bar(df_melhores, x='percentual_cobertura_esgoto', y='municipio', orientation='h', color_discrete_sequence=['#10B981'], template="plotly_white", labels={'percentual_cobertura_esgoto': '%', 'municipio': ''})
fig_melhores.update_layout(margin=dict(l=0, r=0, t=0, b=0))


# ==========================================
# ESTRUTURA DO LAYOUT: ABA 2
# ==========================================
layout_saneamento = html.Div([
    # Cabeçalho da Aba
    html.Div([
        html.H5("INSTITUCIONAL FUNASA", className="text-success fw-bold mb-1 small"),
        html.H2("Panorama de Saneamento Básico", className="fw-bold text-dark"),
        html.P("Análise detalhada da infraestrutura de coleta e tratamento de esgoto.", className="text-muted")
    ], className="mb-4"),

    # KPIs
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("POPULAÇÃO SEM COBERTURA", className="kpi-label text-danger"),
            html.H2(deficit_formatado, className="kpi-value"),
            html.P("Brasileiros expostos a riscos hídricos", className="text-muted small mb-0")
        ]), className="shadow-sm border-0 border-bottom-danger mb-4"), width=6),
        
        dbc.Col(dbc.Card(dbc.CardBody([
            html.P("MÉDIA NACIONAL DE COBERTURA", className="kpi-label text-success"),
            html.H2(f"{media_nacional_esgoto:.1f}%", className="kpi-value"),
            html.P("Índice médio dos municípios analisados", className="text-muted small mb-0")
        ]), className="shadow-sm border-0 border-bottom-success mb-4"), width=6),
    ]),

    # Gráfico de Estados
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Média de Cobertura por Estado (UF)", className="fw-bold"),
            dcc.Graph(figure=fig_uf_esgoto, style={"height": "400px"})
        ]), className="shadow-sm border-0 mb-4"), width=12)
    ]),

    # Gráficos de Melhores e Piores
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Top 10: Situação Crítica", className="fw-bold text-danger"),
            dcc.Graph(figure=fig_piores, style={"height": "300px"})
        ]), className="shadow-sm border-0"), width=6),
        
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Top 10: Excelência", className="fw-bold text-success"),
            dcc.Graph(figure=fig_melhores, style={"height": "300px"})
        ]), className="shadow-sm border-0"), width=6),
    ])
])

# ==========================================
# CÁLCULOS E GRÁFICOS: ABA 3 (SAÚDE PÚBLICA)
# ==========================================

# 1. Gráfico: Top 10 Cidades com Maior Custo SUS (Absoluto)
df_custo_top10 = df_limpo.nlargest(10, 'custo_total').sort_values('custo_total', ascending=True)
fig_custo_sus = px.bar(
    df_custo_top10,
    x='custo_total',
    y='municipio',
    orientation='h',
    color='custo_total',
    color_continuous_scale='Reds',
    labels={'custo_total': 'Custo Total (R$)', 'municipio': ''},
    template="plotly_white"
)
fig_custo_sus.update_layout(margin=dict(l=0, r=20, t=20, b=0), coloraxis_showscale=False)

# 2. Gráfico: Custo Per Capita por Estado (Gasto por habitante)
df_estado_custo = df_limpo.groupby('uf').agg({'custo_total': 'sum', 'populacao_total': 'sum'}).reset_index()
df_estado_custo['custo_per_capita_uf'] = df_estado_custo['custo_total'] / df_estado_custo['populacao_total']
df_estado_custo = df_estado_custo.sort_values('custo_per_capita_uf', ascending=False)

fig_custo_per_capita = px.bar(
    df_estado_custo,
    x='uf',
    y='custo_per_capita_uf',
    color='custo_per_capita_uf',
    color_continuous_scale='Oranges',
    labels={'custo_per_capita_uf': 'Custo por Habitante (R$)', 'uf': 'Estado'},
    template="plotly_white"
)
fig_custo_per_capita.update_layout(margin=dict(l=0, r=0, t=20, b=0), coloraxis_showscale=False)

# ==========================================
# ESTRUTURA DO LAYOUT: ABA 3
# ==========================================
layout_saude = html.Div([
    # Cabeçalho da Aba
    html.Div([
        html.H5("INSTITUCIONAL FUNASA", className="text-danger fw-bold mb-1 small"),
        html.H2("Impacto na Saúde Pública (SUS)", className="fw-bold text-dark"),
        html.P("Monitoramento de internações e custos hospitalares associados à infraestrutura.", className="text-muted")
    ], className="mb-4"),

    # Gráficos Principais
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Top 10 Municípios: Maior Gasto Absoluto (SUS)", className="fw-bold text-danger"),
            dcc.Graph(figure=fig_custo_sus, style={"height": "400px"})
        ]), className="shadow-sm border-0 mb-4"), width=6),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("Custo Hospitalar por Habitante (Média por Estado)", className="fw-bold text-warning"),
            dcc.Graph(figure=fig_custo_per_capita, style={"height": "400px"})
        ]), className="shadow-sm border-0 mb-4"), width=6),
    ])
])


# ==========================================
# CÁLCULOS E ESTRUTURA: ABA 4 (EXPLORAÇÃO)
# ==========================================

layout_exploracao = html.Div([
    # Cabeçalho da Aba
    html.Div([
        html.H5("INSTITUCIONAL FUNASA", className="text-info fw-bold mb-1 small"),
        html.H2("Exploração Dinâmica de Dados", className="fw-bold text-dark"),
        html.P("Filtre, ordene e analise os microdados consolidados de todos os municípios.", className="text-muted")
    ], className="mb-4"),

    # Área de Filtros (Dropdowns)
    dbc.Row([
        dbc.Col([
            html.Label("Filtrar por Estado (UF):", className="fw-bold"),
            dcc.Dropdown(
                id='filtro-uf',
                options=[{'label': uf, 'value': uf} for uf in sorted(df_limpo['uf'].dropna().unique())],
                placeholder="Selecione um Estado...",
                clearable=True
            )
        ], width=4),
        
        dbc.Col([
            html.Label("Filtrar por Município:", className="fw-bold"),
            dcc.Dropdown(
                id='filtro-municipio',
                options=[{'label': mun, 'value': mun} for mun in sorted(df_limpo['municipio'].dropna().unique())],
                placeholder="Digite ou selecione um Município...",
                clearable=True
            )
        ], width=8),
    ], className="mb-4 p-3 bg-white rounded shadow-sm border"),

    # Tabela de Dados Interativa
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            dash.dash_table.DataTable(
                id='tabela-dados',
                columns=[
                    {"name": "Município", "id": "municipio"},
                    {"name": "UF", "id": "uf"},
                    {"name": "População", "id": "populacao_total", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "Cobertura Esgoto (%)", "id": "percentual_cobertura_esgoto", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Internações (SUS)", "id": "internacoes_clinicas", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "Custo SUS (R$)", "id": "custo_total", "type": "numeric", "format": {"specifier": "$,.2f"}}
                ],
                data=df_limpo.to_dict('records'),
                page_size=15, # Mostra 15 linhas por vez
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'sans-serif'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                sort_action='native', # Permite clicar no título da coluna para ordenar (do maior pro menor, etc)
                filter_action='native' # Cria uma caixinha de busca embaixo de cada coluna
            )
        ]), className="shadow-sm border-0"), width=12)
    ])
])


# ==========================================
# ESTRUTURA FINAL E ROTEAMENTO (O MOTOR DE ABAS)
# ==========================================

# O layout principal recebe o Menu, a Barra Superior e um "Espaço Vazio" (page-content)
app.layout = html.Div([
    dcc.Location(id="url"), # O "espião" que olha a URL para saber onde você clicou
    sidebar,
    html.Div([
        topbar,
        html.Div(id="page-content", className="main-content-padding") # Onde as abas vão aparecer
    ], className="content-wrapper")
], className="dashboard-container")


# Callback: A inteligência que troca as telas
# Callback: A inteligência que troca as telas
@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        # Se estiver na página inicial, carrega a Aba 1
        return html.Div([header_section, kpi_cards, graficos_mockup, banner_nacional])
    
    elif pathname == "/saneamento":
        # Se clicou em Saneamento, carrega a Aba 2
        return layout_saneamento

    elif pathname == "/saude":
        # Se clicou em Saúde Pública, carrega a Aba 3
        return layout_saude
    elif pathname == "/exploracao":
        # Se clicou em Exploração Dinâmica, carrega a Aba 4
        return layout_exploracao
    
    # Se digitar endereço errado, volta pra página 1
    return html.Div([header_section, kpi_cards, graficos_mockup, banner_nacional])

#---------------------------------------------------------
# Callback: Filtra a tabela da Aba 4 baseado nos Dropdowns
#---------------------------------------------------------

@app.callback(
    dash.dependencies.Output('tabela-dados', 'data'),
    [dash.dependencies.Input('filtro-uf', 'value'),
     dash.dependencies.Input('filtro-municipio', 'value')]
)
def atualizar_tabela(uf_selecionada, municipio_selecionado):
    # Começa com todos os dados
    df_filtrado = df_limpo.copy()
    
    # Se o usuário escolheu um Estado, corta a tabela só praquele estado
    if uf_selecionada:
        df_filtrado = df_filtrado[df_filtrado['uf'] == uf_selecionada]
        
    # Se o usuário escolheu um Município, mostra só ele
    if municipio_selecionado:
        df_filtrado = df_filtrado[df_filtrado['municipio'] == municipio_selecionado]
        
    # Devolve os dados cortadinhos para a tabela atualizar na tela
    return df_filtrado.to_dict('records')

# ==========================================
# INICIAR O SERVIDOR
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)