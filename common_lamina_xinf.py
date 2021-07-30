import dash_html_components as html
import dash_core_components as dcc
from datetime import datetime, timedelta, date
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import numpy_financial as npf
import math
import os
import dash_table
from zipfile import ZipFile
from bs4 import BeautifulSoup as bs
from App.Posicao._PL_Cotas.read_portfolio import Portfolio
from Risk.ret import ret_mes, ret_ano, ret_ini, BENCH_SERIES
from calendars import DayCounts
from App.Contas._Ativos.debentures import debentures as deb

ativos = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Contas\_Ativos\cadastro_ativos.csv')
ativos['_CNPJ'] = ativos['_CNPJ'].str.replace('FD', '')

deb_carac = pd.read_csv(r'Z:\Credito Privado\Ativos\Debenture_Caracteristica.csv', encoding='latin-1')
inf_cia = pd.read_csv(r'Z:\Credito Privado\Ativos\inf_cadastral_cia_aberta.csv', encoding='latin-1')
inf_cia['CNPJ'] = 'FD' + inf_cia['CNPJ_CIA'].str.replace('.', '').str.replace('/', '').str.replace('-', '')

deb_inf = pd.merge(deb_carac, inf_cia, on='CNPJ', how='left').loc[:, ['ISIN', 'SETOR_ATIV', 'UF',
                                                                      'Empresa        ', 'Deb. Incent. (Lei 12.431)',
                                                                      ' Data de Vencimento',
                                                                      'Percentual Multiplicador/Rentabilidade',
                                                                      'Juros Critério Novo - Taxa'
                                                                      ]]


deb_inf.columns = ['_ISIN', 'Setor', 'Estado', 'Empresa', '12431', 'Data de Vencimento', 'Taxa pós', 'Taxa pré']
enq_12431 = {'N': 'Não', 'S': 'Sim', 'nan': 'Não'}
deb_inf['12431'] = deb_inf['12431'].map(enq_12431)
deb_inf.loc[:, ['Taxa pós', 'Taxa pré']] = deb_inf.loc[:, ['Taxa pós', 'Taxa pré']].fillna(0).astype(str)
ativos = pd.merge(ativos, deb_inf, on='_ISIN', how='left')

grup_eco_nome = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Contas\_Ativos\Grupos_EconomicosTF.csv').loc[:, ['id', 'nome']]
grup_eco_nome = pd.Series(grup_eco_nome.loc[:, 'nome'].values, index=grup_eco_nome.loc[:, 'id'].astype('str')).to_dict()
ativos.loc[:, 'grupoeconomico'] = ativos.loc[:, 'grupoeconomico'].astype('str').replace(grup_eco_nome)

ativos.loc[:, '12431'] = ativos.loc[:, '12431'].fillna('Não')
ativos.loc[ativos['Code'].str.contains("BLFT|BNTNB"), "Setor"] = "Governo Federal"
ativos.loc[ativos['Code'].str.contains("BLFT|BNTNB"), "grupoeconomico"] = "Governo Federal"
ativos.loc[ativos['Ativo'] == 'FUNDO', "grupoeconomico"] = "Fundos"
ativos.loc[ativos['Strategy'] == "CREDITO", "grupoeconomico"] = ativos.loc[
    ativos['Strategy'] == "CREDITO", "grupoeconomico"].fillna('sem info')
ratings = ['RatingF', 'RatingIF', 'RatingIM', 'RatingIS', 'RatingM', 'RatingS']
ativos.loc[ativos['Strategy'] == "FIDC", "Empresa"] = 'FIDC'
ativos.loc[:, ratings] = ativos.loc[:, ratings].fillna('-')
ativos.fillna('Outros', inplace=True)


FUNDS = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Passivo/Fundos.csv', index_col=0)

COM_LAM_PARAMETERS = {
    'commercial': '',
    'date': ''
}

FUND_LAM_PARAMETERS = {
    'fund': '',
    'date': '',
    'p2': '',
    'group_name': ''
}


def header(app, title, subtitle, ref_date):
    """
    Header function for funds reports
    :param app: Dash app object
    :param title: header title
    :param subtitle: header subtitle
    :param ref_date: date to be displayed on the header
    :return: Dash html.Div()
    """
    head = html.Div(
        [
            # html.Div(id="idz"),
            html.Div(
                [
                    html.Div([
                        html.H3(children=title, style={'margin': '0px'}),
                        html.P(subtitle, className='small'),
                        html.H6(ref_date),
                    ], className="main-title_lam", style={'display': 'inline-block', 'width': '80%'}),
                    html.Div([
                        html.Div([
                            html.A(
                                html.Img(
                                    src=app.get_asset_url("LOGO_BDR_AM.png"),
                                    className="main-logo",
                                ),
                                href="http://bdrasset.com.br/",
                            ),
                        ], style={'text-align': 'right', 'vertical-align': 'middle'}),
                    ], style={'display': 'inline-block', 'width': '20%', 'vertical-align': 'top'}),
                ],
                # className="row",
            ),
        ],
        style={},
        # className="row",
    )
    return head


def footer(app, uso_interno=False, additional_text=''):
    """
    Footer for funds reports
    :param app: Dash app object
    :param uso_interno: if true, shows "USO INTERNO" on footer
    :param additional_text: any aditional text to be added to the default disclaimer text
    :return: Dash html.Div()
    """
    text = ''
    if uso_interno:
        text = '* DOCUMENTO DE USO INTERNO *'
    return html.Div([
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            [
                                                html.Img(
                                                    src=app.get_asset_url("Selo-adesao-provisoria-Colorido-01.png"),
                                                    className="logo-float",
                                                ),
                                                html.H6([
                                                    text
                                                ], style={'color': 'red', 'font-size': 10}),
                                                '''
                                                As informações no presente material de divulgação são exclusivamente informativas.
                                                 Estas não devem ser entendidas como oferta, recomendação ou análise de investimentos ou ativos.
                                                  A BDR Investimentos Ltda. não comercializa nem distribui quotas de fundos de investimento. Rentabilidade passada não representa garantia de rentabilidade futura. Ao investidor é recomendada a leitura cuidadosa do prospecto e do 
                                                regulamento dos fundos de investimento ao aplicar seus recursos. Fundos de investimentos não contam com a garantia do administrador, do gestor, do consultor de crédito ou ainda do Fundo Garantidor de Crédito 
                                                - FGC. Para avaliação da performance de um FI, é recomendável uma análise de no mínimo doze meses. Lei o propsecto antes de aceitar a oferta.
                                                Para mais informações acerca das taxas de administração, cotização e público-alvo de cada um dos fundos, consulte os documentos do fundo disponíveis no site 
                                                ''',
                                                html.A('www.bdrasset.com.br', href='http://bdrasset.com.br/'),
                                                '''
                                                .
                                                '''
                                                + additional_text

                                            ],
                                            className='disclaimer'
                                        ),
                                    ],
                                    style={'padding': '2px 10px'},
                                ),
                            ],
                            # className="row",
                            style={
                                "background-color": "#f9f9f9",
                                # "padding-bottom": "0px",
                            },
                        ),
                    ],
                )
            ],
        ),

        # footer
        html.Div(
            [
                html.Div(
                    [
                        html.P([
                            '''BDR Investimentos Ltda          CNPJ: 35.132.740/0001-66          Rua Joaquim Floriano, 733 – 3º andar'''
                        ], style={'text-align': 'center', 'white-space': 'pre', 'overflow': 'hidden'}),
                    ],
                    className="footer",
                )
            ],
            # className="row",
        ),
    ], style={
        'position': 'absolute',
        'left': 0,
        'bottom': 0,
        'width': '100%',
        'display': 'inline-block',
    })


def make_dash_table(df):
    """
    Return a dash definition of an HTML table for a Pandas dataframe
    :param df: dataframe
    :return: Dash html.Table
    """
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return html.Table([
        html.Thead(),
        html.Tbody(table),
    ])


def generate_table(dataframe):
    """
    Generates Dash html.Table()
    :param dataframe: dataframe
    :return: Dahs html.Table()
    """
    return html.Table([
        html.Thead([
            html.Tr([
                html.Th(col) for col in dataframe.columns
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(len(dataframe))
        ])
    ])


def generate_dash_table(df):
    """
    Generates a dash datatable
    :param df: dataframe
    :return: dash_table.Datatable
    """
    df_aux = df.copy()
    df_aux.columns = [''.join(col) for col in df_aux.columns.values]
    return dash_table.DataTable(
        columns=[{"name": i, "id": ''.join(i)} for i in df.columns],
        data=df_aux.to_dict('records'),
        style_as_list_view=True,
        merge_duplicate_headers=True,
        editable=True,
        style_cell={
            'fontSize': 9,
            'font-family': 'calibri',
            'whiteSpace': 'normal',
            'text-align': 'center',
            'color': 'black',
            'height': 'auto',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            'text-align': 'center',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'padding-top': '1px',
            'padding-bottom': '1px',
        },
        style_header={
            'backgroundColor': 'lightgray',
            'color': 'black',
            'border': 'white',
            'text-align': 'center'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{ } contains "20"'
                },
                'backgroundColor': 'rgb(248, 248, 248)',
                'border': '1px solid black'
            }],
        style_header_conditional=None,
    )


def generate_chart(df, series, chartType='line', color_palet=False, legendPos=None, axesNames=None, xaxis_dates=False,
                   bar_chart_orientation='v', texttemplate='', textposition='auto', normalize=False):
    """
    This function generates a chart from a dataframe given a list of series
    :param legendPos: 'h' for legend under the chart
    :param chartType: 'line' or 'bar'
    :param df: dataframe containing the dada for the charts
    :param series: a list containing the name of the series to be plotted
    :param axesNames: a list containing the name of the axis. Ex: ["x_axis_name","y_axis_name"]
    :param xaxis_dates: if true, format x axis as dates
    :param bar_chart_orientation: bar chart orientation -> 'v' or 'h'
    :param texttemplate: template for text format
    :param textposition: for labels on plot
    :param normalize: normalizes all the values to zero at the beginning
    :return: a dcc.Graph()
    """
    if axesNames is None:
        axesNames = ['', '']
    fig = go.Figure()

    if color_palet:
        color_palett = px.colors.diverging.Geyser.copy()
        # color_palett.reverse()
    else:
        color_palett = px.colors.qualitative.Plotly

    if normalize:
        for col in series:
            df.loc[:, col] = df.loc[:, col] / df.loc[:, col].values[0] - 1

    for i in range(len(series)):
        mode = 'lines'
        line = marker = {}
        if 'CDI' in series[i]:
            line = {
                'color': 'lightgray',
                'width': 1,
            }
        else:
            line = {
                'color': color_palett[i],
            }
        if chartType == 'line':
            fig.add_trace(go.Scatter(x=df.index,
                                     y=df[series[i]],
                                     name=series[i],
                                     connectgaps=True,
                                     mode=mode,
                                     line=line,
                                     marker=marker,
                                     ))
            fig.update_traces(texttemplate='%{text:.2f}%')
        elif chartType == 'bar':
            if bar_chart_orientation == 'v':
                fig.add_trace(go.Bar(x=df.index,
                                     y=df[series[i]],
                                     name=series[i],
                                     orientation='v',
                                     text=df[series[i]],
                                     marker_color=color_palett[i]))
            else:
                fig.add_trace(go.Bar(x=df[series[i]],
                                     y=df.index,
                                     name=series[i],
                                     orientation='h',
                                     text=df[series[i]],
                                     marker_color=color_palett[i]))
            fig.update_traces(texttemplate=texttemplate, textposition=textposition)
        else:
            print('Error: invalid chart type')
            return None

    if xaxis_dates:
        if len(df.index.tolist()) < 20:
            dtick = 'D1'
            fig.update_xaxes(
                dtick=dtick,
                tickformat="%d/%m/%y")
        elif len(df.index.tolist()) < 252 * 2:
            dtick = 'M1'
            fig.update_xaxes(
                dtick=dtick,
                tickformat="%m/%Y")
        else:
            dtick = 'M6'
            fig.update_xaxes(
                dtick=dtick,
                tickformat="%m/%Y")

    fig.update_layout(
        hovermode='x',
        xaxis_title=axesNames[0],
        yaxis_title=axesNames[1],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        # width='100%',
        # height=220,
        autosize=True,
        xaxis=dict(showgrid=False, zeroline=False, autorange=True, fixedrange=False),
        yaxis=dict(showgrid=False, zeroline=False, autorange=True, fixedrange=False),
        margin={
            "r": 0,
            "t": 0,
            "b": 0,
            "l": 0,
            "pad": 0,
        },
        dragmode='pan',  # changed for easier usage @MGA 2020-07-31
    )
    if legendPos == 'h':
        y = None
    else:
        y = 1
    fig.update_layout(
        legend_orientation=legendPos,
        legend=dict(
            y=y,
            traceorder="normal",
            font=dict(
                family="helvetica",
                size=10,
                color="black"
            ),
            bgcolor="rgba(0,0,0,0)",
        )
    )
    fig.update_yaxes(tickfont=dict(size=8),
                     title_font=dict(size=8))
    fig.update_xaxes(tickfont=dict(size=8),
                     title_font=dict(size=8))
    config = dict({'scrollZoom': True,  # changed for easier usage @MGA 2020-07-31
                   'displayModeBar': False
                   })
    return dcc.Graph(figure=fig, config=config, className='chart')


def receita_retorno(com, ref_date, cota=None):
    """

    :param com: salesperson
    :param ref_date: reference date
    :param cota: dataframe containign quote (optional)
    :return: dataframe
    """
    global FUNDS

    # comerciais = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Posicao\_PL_Cotas\Remuneracao\Weaker.csv', index_col=0,
    #                          parse_dates=True).loc[:ref_date]
    bdr = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Posicao/_PL_Cotas/Remuneracao/BTG_FILES/BTG_HISTORICO.csv',
                      index_col=0,
                      parse_dates=True).dropna(axis=0, how='all').iloc[:, :-1]

    rebate = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Laminas/rebate.csv', header=[0, 1], index_col=0, parse_dates=True)
    rebate = rebate.loc[:, com.upper()]

    try:

        rb_m = rebate.groupby([rebate.index.year, rebate.index.month]).sum().loc[
            [(int(ref_date.strftime('%Y')), int(ref_date.strftime('%m')))]].T

        rb_y = rebate.groupby([rebate.index.year]).sum().loc[[int(ref_date.strftime('%Y'))]].T

        # df_1d = comerciais.loc[[ref_date], :].T
        df_m_bdr = bdr.groupby([bdr.index.year, bdr.index.month]).sum().loc[
            [(int(ref_date.strftime('%Y')), int(ref_date.strftime('%m')))]].T

        # df_m = comerciais.groupby([comerciais.index.year, comerciais.index.month]).sum().loc[
        #     [(int(ref_date.strftime('%Y')), int(ref_date.strftime('%m')))]].T
        # df_y = comerciais.groupby([comerciais.index.year]).sum().loc[[int(ref_date.strftime('%Y'))]].T
        # # receita = pd.concat([df_m_bdr, df_m, df_y], axis=1)
        # receita = pd.concat([df_m_bdr, rb_m, rb_y], axis=1)#.dropna(axis=0, how='any')
        receita = df_m_bdr.merge(rb_m, left_index=True, right_index=True, how='right')
        receita = receita.merge(rb_y, left_index=True, right_index=True, how='right')

    except KeyError:
        receita = pd.DataFrame(index=rebate.columns, columns=['a', 'b', 'c'])

    receita.index = receita.index.astype('str')
    receita = receita.fillna(0)
    receita.loc['Total'] = receita.sum(numeric_only=True)
    receita.columns = [('Receita', 'Mês BDR'), ('Receita', 'Mês ' + com), ('Receita', 'Ano ' + com)]
    for col in receita.columns:
        receita[col] = receita[col].map('R${:,.2f}'.format).str.replace(",", "X").str.replace(".", ",").str.replace("X",
                                                                                                                    ".")

    # retorno
    mask = (FUNDS.loc[:, (FUNDS.columns.str.contains('Comercial')) &
                         (~FUNDS.columns.str.contains('Rebate_Comercial'))] == com).any(axis=1)
    funds = FUNDS.loc[mask]
    funds['CNPJ'] = funds['CNPJ'].str.replace('.', '').str.replace('/', '').str.replace('-', '')
    btg_name_to_fd = pd.Series(funds.loc[:, 'codBTG'].values, index=funds.loc[:, 'BTGName']).to_dict()
    fd_to_name = pd.Series(funds.loc[:, 'Nome'].values, index=funds.loc[:, 'codBTG']).to_dict()

    receita.rename(index=btg_name_to_fd, inplace=True)

    if cota is None:
        cota = get_cota(ref_date, 'Comercial', com)

    retorno = pd.DataFrame(columns=['Mês', 'Ano', 'Início'])
    for col in cota.columns:
        cota_fundo = cota.loc[:ref_date, [col]].dropna(axis=0, how='any')

        cota_fundo.columns = ['cota']
        cota_fundo.index.names = ['Date']

        retorno.loc[col, 'Mês'] = ret_mes(cota_fundo).iloc[-1]['cota']
        retorno.loc[col, 'Ano'] = ret_ano(cota_fundo).iloc[-1]['cota']
        retorno.loc[col, 'Início'] = ((cota_fundo.iloc[-1] - cota_fundo.iloc[0]) / cota_fundo.iloc[0])['cota']

    retorno = retorno.fillna(9999999)
    retorno.columns = [('Retorno', 'Mês'), ('Retorno', 'Ano'), ('Retorno', 'Início')]
    for col in retorno.columns:
        retorno[col] = retorno[col].map('{:.2%}'.format).str.replace(".", ",")
        retorno[col] = retorno[col].str.replace('999999900,00%', '-')

    r = pd.merge(receita, retorno, how='outer', left_index=True, right_index=True)
    r = r.rename(index=fd_to_name)
    r = r.fillna('')
    return r


def rentabilidade(filter_by, ref_date, parameter='Nome', cota=None, benchmark='CDI', pct_bench=1, pre_bench=0):
    """

    :param filter_by: word to filter in fundos.csv
    :param ref_date: reference date
    :param parameter: column to filter in fundos.csv
    :param cota: dataframe containing quotes (optional)
    :param benchmark: 'CDI' or 'IBOV' (str)
    :param pct_bench: percentage of the benchmark (float)
    :param pre_bench: pre percentage (float)
    :return: dataframe
    """
    global FUNDS
    if parameter == "Comercial":
        mask = (FUNDS.loc[:, (FUNDS.columns.str.contains('Comercial')) &
                             (~FUNDS.columns.str.contains('Rebate_Comercial'))] == filter_by).any(axis=1)
        funds = FUNDS.loc[mask]
    else:
        funds = FUNDS.loc[FUNDS[parameter] == filter_by]
    cnpj_to_name = pd.Series(funds.loc[:, 'Nome'].values, index=funds.loc[:, 'codBTG']).to_dict()

    # if benchmark == 'CDI':
    #     if pct_bench != 1:
    #         cnpj_to_name['CDI_ACUM'] = '{:.0%} '.format(pct_bench) + benchmark
    #     else:
    #         cnpj_to_name['CDI_ACUM'] = benchmark
    if pct_bench != 1 and pre_bench != 0:
        cnpj_to_name[benchmark] = '{:.0%} '.format(pct_bench) + benchmark + ' + {:.0%}'.format(pre_bench)
    elif pct_bench != 1:
        cnpj_to_name[benchmark] = '{:.0%} '.format(pct_bench) + benchmark
    elif pre_bench != 0:
        cnpj_to_name[benchmark] = benchmark + ' + {:.0%}'.format(pre_bench)

    if cota is None:
        cota = get_cota(ref_date, parameter, filter_by)

    path = BENCH_SERIES[benchmark]['path']
    column = BENCH_SERIES[benchmark]['col']
    bench = pd.read_csv(path, index_col=0, parse_dates=True)
    bench = bench.loc[:, [column]].dropna(axis=0).sort_index() * pct_bench
    bench = bench.rename(columns={column: benchmark})
    if parameter == "Comercial":
        cota = cota.loc[date(2020, 8, 12):]
    cota = pd.merge(cota, bench, how='left', left_index=True, right_index=True)
    norm_date = pd.to_datetime(cota.dropna(axis=0, how='any').index.values[0])
    for cols in cota.columns:
        cota.loc[:, cols] = ((cota.loc[:, cols] / cota.loc[norm_date, cols]) - 1) * 100
    if pre_bench != 0:
        cota.loc[:, benchmark] = cota.apply(
            lambda x: x[benchmark] + ((1 + pre_bench) ** (cota.index.tolist().index(x.name) / 252) - 1) * 100, axis=1)
    cota = cota.rename(columns=cnpj_to_name)
    return cota.loc[:ref_date]


def funds_info(com, ref_date):
    """

    :param com: salesperson
    :param ref_date: referece date
    :return: dash html.Div
    """
    global FUNDS
    mask = (FUNDS.loc[:, (FUNDS.columns.str.contains('Comercial')) &
                         (~FUNDS.columns.str.contains('Rebate_Comercial'))] == com).any(axis=1)
    funds = FUNDS.loc[mask]
    funds.loc[:, 'Nome'] = funds.loc[:, 'Nome'].str.replace("_", " ")

    funds.loc[:, 'reb'] = 0
    for index, row in funds.iterrows():
        com_num = row.index[row.str.contains(com) & row.index.str.contains('Comercial')][0].strip('Comercial')
        funds.loc[index, 'reb'] = funds.loc[index, 'Rebate_Comercial' + com_num]

    funds.columns = funds.columns.str.replace("_", " ")

    fd_list = tuple(funds.loc[:, 'codBTG'].dropna().tolist())

    # funds['CNPJ_2'] = funds['CNPJ'].str.replace('.', '').str.replace('/', '').str.replace('-', '')

    relative_path = 'Z:/Gestao/Programas/Python/App/Posicao\\'
    day = ref_date.strftime('%d').lstrip('0')
    month = ref_date.strftime('%m').lstrip('0')
    year = ref_date.strftime('%Y')
    path = relative_path + year + '\\' + month + '\\' + day + '\\'
    if os.path.exists(path):
        for file_name in os.listdir(path):
            raw_name = file_name.split('.')[0]
            if raw_name.startswith(fd_list):
                if file_name.endswith('.xml'):  # fundos btg
                    with open(os.path.join(path, file_name)) as file:
                        content = file.readlines()
                        content = "".join(content)
                        soup = bs(content, "lxml")
                        header = soup.find('header')
                        pl = float(header.find('patliq').text)

                elif file_name.endswith('.zip'):  # fundos intrader
                    with ZipFile(os.path.join(path, file_name), 'r') as zip_file:
                        patrimonio_csv = [i for i in zip_file.namelist() if 'Patrimonio-Totais' in i]
                        patr = pd.read_csv(zip_file.open(patrimonio_csv[0]), encoding='latin-1', sep=';', thousands='.',
                                           decimal=',')
                        pl = patr.loc[0, 'VALORPATRIMONIOLIQUIDO']
                funds.loc[funds['codBTG'] == file_name.split('_')[0], 'PL Atual'] = pl

    funds = funds.loc[:, ['Nome', 'CNPJ', 'PL Atual', 'Taxa ADM', 'Taxa Performance', 'reb']].dropna(
        axis=0, how='any')
    format_dict = {'Taxa ADM': '{:,.1%}', 'Taxa Performance': '{0:,.1%}', 'reb': '{0:,.1%}'}
    for key in format_dict.keys():
        funds.loc[:, key] = funds.loc[:, key].map(format_dict[key].format).str.replace('.', ',')
    funds.loc[:, 'PL Atual'] = funds.loc[:, 'PL Atual'].map('R${0:,.2f}'.format).str.replace(",", "X").str.replace(".",
                                                                                                                   ",").str.replace(
        "X", ".")
    funds.loc[:, 'PL Atual'] = funds.loc[:, 'PL Atual'].str.replace('R$-1,00', '-')
    funds = funds.rename(columns={'Taxa Performance': 'Taxa de performance',
                                  'Taxa ADM': 'Taxa de administração',
                                  'PL Atual': 'PL atual',
                                  'reb': 'Rebate comercial'})

    div_list = []
    for index, row in funds.iterrows():
        aux_df = funds.loc[index, :].to_frame()
        aux_df.reset_index(inplace=True)
        aux_df.columns = aux_df.iloc[0]
        aux_df = aux_df.iloc[1:]
        div_list.append(generate_dash_table(aux_df))
    return html.Div(div_list)


def carteira(ref_date: datetime.date, fund_cnpj: str, pct_pl=False, group_name='Nickname', drop_compromiss=False,
             quantity=False) -> pd.DataFrame:
    """
    This function gets the current portfolio of a fund in a given date
    :param ref_date: reference date, should be business day
    :param fund_cnpj: FD + fund cnpj
    :param pct_pl: to get the portfolio as percentage of the total: -> default False
    :param group_name: how to group the assets (according to cadastro_ativos.csv columns): -> default "Nickname"
    :param drop_compromiss: to drop compromissada from the portifolio: -> default False
    :param quantity: return only the quantity of each asset on the portfolio: -> default False
    :return: pd.dataframe -> columns: index->asset name; comp->PU, %PL or Quantity of the asset
    """
    relative_path = r'Z:/Gestao/Programas/Python/App/Posicao'
    df = pd.DataFrame()
    # port = Portfolio()
    day = str(ref_date.day)
    month = str(ref_date.month)
    year = str(ref_date.year)
    path = os.path.join(relative_path, year, month, day)
    if os.path.exists(path):
        for file_name in os.listdir(path):
            current_file = os.path.join(path, file_name)
            if os.path.isfile(current_file) and file_name.startswith(fund_cnpj):
                port = Portfolio(current_file, group_name=group_name, get_provisao=False)
                df = port.portfolio.rename(columns={'code': 'index'})
    if drop_compromiss:
        df = df.loc[~df['index'].str.contains('Compromissada')]

    if quantity:
        return df.loc[:, ['index', 'pu', 'qtd']]

    df.loc[:, 'comp'] = df.loc[:, 'pu'] * df.loc[:, 'qtd']
    df = df.loc[:, ['index', 'comp']]

    if pct_pl:
        df.loc[:, 'comp'] = df.loc[:, 'comp'] / port.pl * 100
    return df


def group_carteira(df, group_name):
    """
    This function groups the portfolio given a group_name
    :param df: dataframe containing the portifolio
    :param group_name: name of the group (see ativos variable)
    :return: grouped portifolio dataframe
    """
    cart = df.copy()
    cart_grop = pd.Series(ativos.loc[:, group_name].values, index=ativos.loc[:, 'Nickname']).to_dict()
    cart = cart.replace(cart_grop)
    if group_name == 'Strategy':
        cart.loc[cart['index'].str.contains("Compromissada"), "index"] = "CAIXA"
    elif group_name == 'Passive':
        cart.loc[cart['index'].str.contains("Compromissada"), "index"] = "CDI +"
    elif group_name == 'Setor':
        cart.loc[cart['index'].str.contains("Compromissada"), "index"] = "Bancos"
    elif group_name == '12431':
        cart.loc[cart['index'].str.contains("Compromissada"), "index"] = "Não"
    else:
        cart.loc[cart['index'].str.contains("Compromissada"), "index"] = "Compromissada"
    return cart.groupby(['index']).sum().reset_index()


def get_last_trades(init_dtate:datetime.date, end_date: datetime.date, fd_code: str) -> pd.DataFrame:

    fund_name = FUNDS.loc[FUNDS['codBTG'] == fd_code, 'Nome'].values[0]
    relative_path = r'Z:/Gestao/Programas/Python/App/Boletagem'
    current_date = pd.to_datetime(init_dtate)
    last_trades = pd.DataFrame()
    while current_date <= end_date:
        day = current_date.day
        month = current_date.month
        year = current_date.year
        path = os.path.join(relative_path, str(year), str(month), str(day), 'boletagem_credito.csv')
        if os.path.isfile(path):
            boleta = pd.read_csv(path).fillna(0)
            if fund_name in boleta.columns:
                boleta = boleta.loc[boleta[fund_name] != 0]
                if not boleta.empty:
                    boleta.loc[:, 'date'] = current_date
                    #Code,Price,Corretora,Strategy,Noroeste
                    boleta = boleta.loc[:, ['date', 'Code', 'Price', 'Taxa', fund_name]]

                    last_trades = last_trades.append(boleta)
        current_date += np.timedelta64(1, 'D')
    last_trades = last_trades.loc[last_trades['Code'] != 'COMPROMISSADA']
    # last_trades.loc[:, 'Taxa'] = None
    # if not last_trades.empty:
    #     last_trades.loc[:, 'Taxa'] = last_trades.apply(
    #         lambda x: deb.bond_rate(x.Code, x.Price, x.date)[2] if x.Code in ativos.loc[
    #             ativos['tp_ativo'] == 'DEBENTURE', 'Code'].tolist() else 0, axis=1)

    last_trades = last_trades.rename(columns={'date': 'Data da operação', 'Code': 'Ativo', 'Price': 'Preço',
                                              fund_name: 'Quantidade'})

    return last_trades


def deb_dur_spread_pz(ref_date: datetime.date, fd_code: str) -> pd.DataFrame:
    """

    :param ref_date: reference date
    :param fd_code: 'FD' + fund cnpj
    :return: dataframe containing duration, spread, spread IPCA, and average maturity ? (prazo médio)
    """
    relative_path = r'Z:/Gestao/Programas/Python/App/Posicao'
    evo = pd.DataFrame(columns=['m_dur', 'spread', 'spread_ipca', 'pz_med'])
    dc = DayCounts(dc='bus/252', calendar='anbima')
    current_date = ref_date
    while current_date > date(2020, 8, 12):
        day = current_date.strftime('%d').lstrip('0')
        month = current_date.strftime('%m').lstrip('0')
        year = current_date.strftime('%Y')
        path = os.path.join(relative_path, year, month, day)
        dur_spread_pz = pd.read_csv(os.path.join(path, 'debentures_daily_calc.csv'), index_col=0)
        try:
            ct = carteira(current_date, fd_code, pct_pl=True, group_name='Nickname', drop_compromiss=True)
        except KeyError:
            break
        ct = ct.set_index('index')
        prod = dur_spread_pz.mul(ct.iloc[:, 0] / 100, axis=0).dropna(axis=0, how='all')
        evo.loc[pd.to_datetime(current_date)] = prod.sum(axis=0)
        current_date = dc.workday(current_date, -1)
    return evo


def pie_chart(df, values, names):
    df.loc[df[names].str.len() > 15, names] = df.loc[df[names].str.len() > 15, names].str.replace(' ', '\n', 1)

    fig = go.Figure(px.pie(df, values=values, names=names, hole=.3,
                           color_discrete_sequence=px.colors.diverging.Geyser))  # squential good -> Teal, Mint, dense, amp

    fig.update_traces(textinfo='percent', textfont_size=8)

    fig.update(layout_showlegend=True)

    if df.shape[0] > 5:
        fig.update_layout(
            legend_orientation="h",
            legend=dict(
                x=1,
                y=1,
                font=dict(
                    size=5,
                )
            )
        )
    else:
        fig.update_layout(
            legend=dict(
                font=dict(
                    size=5,
                )
            )
        )

    fig.update_layout(
        # uniformtext_minsize=6, uniformtext_mode='hide',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        margin={
            "r": 0,
            "t": 0,
            "b": 0,
            "l": 0,
        }
    )
    config = dict({'displayModeBar': False})
    return dcc.Graph(figure=fig, config=config, className='chart')


def ret_table(fund_cnpj, ref_date, cota=None):
    if cota is not None:
        pass
    elif fund_cnpj == '00000000000022':
        cota = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Passivo/Cota_f001.csv', index_col=0, parse_dates=True).loc[
               :ref_date, ['Cota']]
    else:
        cota = get_cota(ref_date, 'codBTG', 'FD' + fund_cnpj)

    bench = FUNDS.loc[FUNDS['codBTG'] == 'FD' + fund_cnpj, 'Benchmark'].values[0]
    pct_bench = FUNDS.loc[FUNDS['codBTG'] == 'FD' + fund_cnpj, 'pct_benchmark'].values[0]
    pre_bench = FUNDS.loc[FUNDS['codBTG'] == 'FD' + fund_cnpj, 'pre_benchmark'].values[0]

    if pct_bench != 1 and pre_bench != 0:
        bench_name = '{:.0%} '.format(pct_bench) + bench + ' + {:.0%}'.format(pre_bench)
    elif pct_bench != 1:
        bench_name = '{:.0%} '.format(pct_bench) + bench
    elif pre_bench != 0:
        bench_name = bench + ' + {:.0%}'.format(pre_bench)
    else:
        bench_name = bench
    cota.columns = ['cota']
    cota.index.names = ['Date']
    reto_mes = ret_mes(cota, benchmark=bench, pct_bench=pct_bench, pre_bench=pre_bench)
    reto_ano = ret_ano(cota, benchmark=bench, pct_bench=pct_bench, pre_bench=pre_bench)
    reto_ano['Year'] = reto_ano.index.year
    reto_mes['Year'] = reto_mes.index.year
    reto_mes['Month'] = reto_mes.index.month
    meses = ['index'] + list(range(1, 13)) + ['Ano', 'Início']
    ret = pd.DataFrame(columns=meses)
    for year in reto_ano.loc[:, 'Year'].values:
        reto_ini = ret_ini(cota, year, benchmark=bench, pct_bench=pct_bench, pre_bench=pre_bench) - 1
        reto_ini['pct_bench'] = reto_ini[list(cota.columns)[0]] / reto_ini.iloc[:, -1]

        ret_y = reto_ano.loc[reto_ano['Year'] == year].drop('Year', 1)
        ret_y['pct_bench'] = ret_y[list(cota.columns)[0]] / ret_y.iloc[:, -1]

        ret_m = reto_mes.loc[reto_mes['Year'] == year].drop('Year', 1)
        ret_m['pct_bench'] = ret_m.loc[:, list(cota.columns)[0]] / ret_m.loc[:, bench]
        ret_m = ret_m.set_index('Month')
        ret_m = ret_m.T.reset_index()
        ret_m.loc[:, 'Ano'] = ret_y.iloc[0].values
        ret_m.loc[:, 'Início'] = reto_ini.iloc[0].values
        ret_m.loc[:, 'index'] = [str(year), bench_name, '% ' + bench_name]
        ret = pd.concat([ret, ret_m], axis=0, ignore_index=True)
    ret = ret.rename(
        columns={'index': ' ', 1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set',
                 10: 'Out',
                 11: 'Nov', 12: 'Dez'})
    ret.fillna(99999, inplace=True)
    for index, row in ret.iterrows():
        if row[' '] == '% ' + bench:
            ret.iloc[index, 1:] = ret.iloc[index, 1:].apply('{:.0%}'.format)
            ret.iloc[index, 1:] = ret.iloc[index, 1:].str.replace('9999900%', '-')
        else:
            ret.iloc[index, 1:] = ret.iloc[index, 1:].apply('{:.2%}'.format).str.replace('.', ',')
            ret.iloc[index, 1:] = ret.iloc[index, 1:].str.replace('9999900.00%', '-')
    return ret


# def performance_attribution_test(fund_cnpj, ref_date, group_name='Nickname'):
#     ativos = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Contas\_Ativos\cadastro_ativos.csv', encoding='latin-1')
#     nick_to_group = pd.Series(ativos.loc[:, group_name].values, index=ativos.loc[:, 'Nickname']).to_dict()
#     nick_to_group['provisao'] = 'Custos do fundo'
#     if fund_cnpj == 'FD00000000000022':
#         # ***************
#         diff = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Laminas\perf_atri.csv', index_col=0)
#     else:
#         cart = get_data(group=False, prov=True)
#
#         cota_dummy = cart.loc[:ref_date, [(fund_cnpj, 'Valor da cota', 'Valor da cota')]].dropna(how='all', axis=0)
#
#         cota_dummy.columns = ['cota']
#         cota_dummy.index.names = ['Date']
#         cdi_mes = ret_mes(cota_dummy)
#         cdi_ano = ret_ano(cota_dummy)
#         print(ref_date)
#         diff = pnl(cart, ref_date, fund_cnpj).loc[:, ['PNL mês', 'PNL ano']]
#         compromis_list = list(filter(lambda x: 'Compromissada' in x, diff.index.tolist()))
#         diff.loc['CAIXA', :] = diff.loc[compromis_list, :].sum(axis=0)
#         diff.drop(compromis_list, axis=0, inplace=True)
#         diff = diff.rename(index=nick_to_group).groupby(level=0, axis=0).sum() * 100
#         diff.loc['PNL total', :] = diff.sum(axis=0)
#         diff.loc['CDI', ['PNL mês', 'PNL ano']] = [cdi_mes.iloc[-1, 1] * 100, cdi_ano.iloc[-1, 1] * 100]
#
#     diff = diff.loc[(diff != 0).any(axis=1), :]
#     diff_pos = diff.where(diff > 0, 0)
#     diff_neg = diff.where(diff < 0, 0)
#
#     fig1 = go.Figure()
#
#     fig2 = go.Figure()
#
#     fig1.add_trace(go.Bar(x=diff_pos['PNL mês'].values,
#                           y=diff_neg.index.values,
#                           orientation='h',
#                           marker_color='green',
#                           marker_opacity=0.8,
#                           text=diff_pos['PNL mês'].values,
#                           name='Mês'))
#
#     fig1.add_trace(go.Bar(x=diff_neg['PNL mês'].values,
#                           y=diff_neg.index.values,
#                           orientation='h',
#                           marker_color='red',
#                           marker_opacity=0.4,
#                           text=diff_neg['PNL mês'].values,
#                           name='Mês'))
#
#     fig2.add_trace(go.Bar(x=diff_pos['PNL ano'].values,
#                           y=diff_pos.index.values,
#                           orientation='h',
#                           marker_color='green',
#                           marker_opacity=0.8,
#                           text=diff_pos['PNL ano'].values,
#                           name='Ano'))
#     fig2.add_trace(go.Bar(x=diff_neg['PNL ano'].values,
#                           y=diff_neg.index.values,
#                           orientation='h',
#                           marker_color='red',
#                           marker_opacity=0.4,
#                           text=diff_neg['PNL ano'].values,
#                           name='Ano'))
#     fig1.update_traces(texttemplate='%{text:.2f}%', textposition='auto', textfont_size=8)
#     fig2.update_traces(texttemplate='%{text:.2f}%', textposition='auto', textfont_size=8)
#     fig1.update_layout(
#         # hovermode='x',
#         barmode='relative',
#         plot_bgcolor="rgba(0,0,0,0)",
#         paper_bgcolor="rgba(0,0,0,0)",
#         autosize=True,
#         margin={
#             "r": 0,
#             "t": 20,
#             "b": 0,
#             "l": 0,
#             "pad": 0
#         },
#         showlegend=False,
#         xaxis={'showticklabels': False},
#         xaxis2={'showticklabels': False},
#         yaxis={'tickfont'
#                ''
#                '': dict(size=6)},
#         dragmode='pan',  # changed for easier usage @MGA 2020-07-31
#     )
#     fig2.update_layout(
#         # hovermode='x',
#         barmode='relative',
#         plot_bgcolor="rgba(0,0,0,0)",
#         paper_bgcolor="rgba(0,0,0,0)",
#         autosize=True,
#         margin={
#             "r": 0,
#             "t": 20,
#             "b": 0,
#             "l": 0,
#             "pad": 0
#         },
#         showlegend=False,
#         xaxis={'showticklabels': False},
#         xaxis2={'showticklabels': False},
#         yaxis={'tickfont': dict(size=10)},
#         dragmode='pan',  # changed for easier usage @MGA 2020-07-31
#     )
#
#     config = dict({'scrollZoom': True,
#                    'displayModeBar': False})
#
#     return html.Div([
#         html.Div([
#             dcc.Graph(figure=fig1, config=config, className='chart')
#         ], className='chart-container', style={'display': 'inline-block', 'width': '45%', 'padding': '30px'}),
#         html.Div([
#             dcc.Graph(figure=fig2, config=config, className='chart')
#         ], className='chart-container', style={'display': 'inline-block', 'width': '45%', 'padding': '30px'})
#     ])


def performance_attribution(fund_cnpj, ref_date, group_name='Nickname'):
    # ativos = pd.read_csv(r'Z:\Gestao\Programas\Python\App\Contas\_Ativos\cadastro_ativos.csv', encoding='latin-1')
    nick_to_group = pd.Series(ativos.loc[:, group_name].values, index=ativos.loc[:, 'Nickname']).to_dict()
    nick_to_group['provisao'] = 'Custos do fundo'
    if fund_cnpj == 'FD00000000000022':
        # ***************
        diff = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Laminas/perf_atri.csv', index_col=0)

    else:
        fund_name = FUNDS.loc[FUNDS['codBTG'] == fund_cnpj, 'Nome'].values[0]
        current_date = date(2020, 8, 14)
        relative_path = r'Z:/Gestao/Programas/Python/App/Posicao'
        diff = pd.DataFrame()
        while current_date <= ref_date:
            day = str(current_date.day)
            month = str(current_date.month)
            year = str(current_date.year)
            path = os.path.join(relative_path, year, month, day, 'pnl_btg.csv')
            try:
                pnl_dia = pd.read_csv(path)
                pnl_dia = pnl_dia.loc[pnl_dia['Fund'] == fund_name, ['Code', 'PNL %']].set_index('Code').T
                if not pnl_dia.empty:
                    pnl_dia.index = [pd.to_datetime(current_date)]
                    diff = diff.append(pnl_dia)
            except FileNotFoundError:
                pass
            current_date = current_date + timedelta(1)
        diff = diff.fillna(0)
        diff.loc[:, 'PNL total'] = diff.sum(axis=1)
        diff = diff.apply(lambda x: 1 + x)
        df_m = diff.groupby([diff.index.year, diff.index.month]).prod().loc[[(int(ref_date.year), int(ref_date.month))]].T
        df_y = diff.groupby([diff.index.year]).prod().loc[[int(ref_date.year)]].T

        diff = pd.merge(df_m, df_y, how='outer', left_index=True, right_index=True)
        diff = diff.apply(lambda x: x - 1)
        diff.columns = ['PNL mês', 'PNL ano']
        compromis_list = list(filter(lambda x: 'Compromissada' in x, diff.index.tolist()))
        diff.loc['CAIXA', :] = diff.loc[compromis_list, :].sum(axis=0)
        diff.drop(compromis_list, axis=0, inplace=True)
        diff = diff.rename(index=nick_to_group).groupby(level=0, axis=0).sum() * 100
        diff = diff.loc[['PNL total']+diff.index.tolist()].drop_duplicates(keep='last')

    diff = diff.loc[(diff != 0).any(axis=1), :].sort_values(by=['PNL mês'])
    cols = [i for i in diff.index if i != 'PNL total'] + ['PNL total']
    diff = diff.loc[cols]
    diff_pos = diff.where(diff > 0, 0)
    diff_neg = diff.where(diff < 0, 0)

    # diff_pos = diff_pos.sort_values(by=['PNL mês'])
    # diff_neg = diff_neg.sort_values(by=['PNL mês'])

    # m_min = diff_neg['PNL mês'].min()
    # m_max = diff_pos['PNL mês'].max()
    # y_min = diff_neg['PNL ano'].min()
    # y_max = diff_pos['PNL ano'].max()
    #
    # f_min = f_max = 0
    # if abs(m_min) < m_max:
    #     f_min = (abs(m_min) + m_max) * 0.9
    # else:
    #     f_max = (abs(m_min) + m_max) * 0.9
    # m = [m_min - f_min, m_max + f_max]
    #
    # f_min = f_max = 0
    # if abs(y_min) < y_max:
    #     f_min = (abs(m_min) + m_max) * 1
    # else:
    #     f_max = (abs(m_min) + m_max) * 1
    # y = [y_min - f_min, y_max + f_max]

    fig = make_subplots(rows=1, cols=2,
                        specs=[[{}, {}]],
                        shared_xaxes=False,
                        shared_yaxes=True,
                        # vertical_spacing=0.001,
                        horizontal_spacing=0,
                        subplot_titles=('Mês', 'Ano'))

    fig.add_trace(go.Bar(x=diff_pos['PNL mês'].values,
                         y=diff_neg.index.values,
                         orientation='h',
                         marker_color='rgb(0, 128, 128)',
                         marker_opacity=0.8,
                         text=diff_pos['PNL mês'].values,
                         name='Mês'), 1, 1)
    fig.add_trace(go.Bar(x=diff_neg['PNL mês'].values,
                         y=diff_neg.index.values,
                         orientation='h',
                         marker_color='rgb(222, 138, 90)',
                         marker_opacity=0.9,
                         text=diff_neg['PNL mês'].values,
                         name='Mês'), 1, 1)

    fig.add_trace(go.Bar(x=diff_pos['PNL ano'].values,
                         y=diff_neg.index.values,
                         orientation='h',
                         marker_color='rgb(0, 128, 128)',
                         marker_opacity=0.8,
                         text=diff_pos['PNL ano'].values,
                         name='Ano'), 1, 2)
    fig.add_trace(go.Bar(x=diff_neg['PNL ano'].values,
                         y=diff_neg.index.values,
                         orientation='h',
                         marker_color='rgb(222, 138, 90)',
                         marker_opacity=0.9,
                         text=diff_neg['PNL ano'].values,
                         name='Ano'), 1, 2)
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='auto', textfont_size=8)
    fig.update_layout(
        # hovermode='x',
        barmode='relative',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        margin={
            "r": 0,
            "t": 20,
            "b": 0,
            "l": 0,
            "pad": 0
        },
        showlegend=False,
        xaxis={'visible': False},
        xaxis2={'visible': False},
        dragmode='pan',  # changed for easier usage @MGA 2020-07-31
    )
    fig.update_yaxes(tickfont=dict(size=6))

    config = dict({'scrollZoom': True,
                   'displayModeBar': False})
    return dcc.Graph(figure=fig, config=config, className='chart')


def features_table(fund_cnpj, ref_date):
    """

    :param fund_cnpj: 'FD' + cnpj
    :return:
    """
    global FUNDS

    fund = FUNDS.loc[FUNDS['codBTG'] == fund_cnpj]
    fund = fund.fillna('n/a')

    tab = pd.DataFrame(columns=['valor'])
    inicio = str(int(fund.loc[:, 'Data_Inicio_original'].values[0]))
    tab.loc['Data de início', 'valor'] = inicio[-2:] + '/' + inicio[4:6] + '/' + inicio[:4]
    tab.loc['Público alvo', 'valor'] = fund.loc[:, 'Publico'].values[0]
    tab.loc['Classificação Anbima', 'valor'] = fund.loc[:, 'classificacao_fundo_n1'].values[0]  # + ' ' +\

    pl = get_pl(ref_date, 'codBTG', fund_cnpj)
    if pl.shape[0] != 0:
        tab.loc['PL atual', 'valor'] = 'R${:,.2f}'.format(float(pl.iloc[-1, 0])).replace(",", "X").replace(".",
                                                                                                           ",").replace(
            "X", ".")
        pl = pl.groupby([pl.index.year, pl.index.month]).mean().iloc[:, 0]
        tab.loc['PL médio 12 meses / desde o início', 'valor'] = 'R${:,.2f}'.format(
            float(pl.iloc[-12:].where(pl>0).dropna().mean())).replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        tab.loc['PL atual', 'valor'] = 0
        tab.loc['PL médio 12 meses / desde o início', 'valor'] = 0

    tab.loc['Aplicação mínima', 'valor'] = \
        fund.loc[:, 'apl_min'].apply('R${:,.2f}'.format).str.replace(",", "X").str.replace(".", ",").str.replace("X",
                                                                                                                 ".").values[
            0]
    tab.loc['Saldo mínimo', 'valor'] = \
        fund.loc[:, 'saldo_min'].apply('R${:,.2f}'.format).str.replace(",", "X").str.replace(".", ",").str.replace("X",
                                                                                                                   ".").values[
            0]
    tab.loc['Cota', 'valor'] = fund.loc[:, 'cota'].values[0]
    tab.loc['Cota de aplicação', 'valor'] = fund.loc[:, 'cotizacao_aplicao'].values[0]
    tab.loc['Cota de resgate', 'valor'] = fund.loc[:, 'cotizacao_resgate'].values[0]
    tab.loc['Liquidação do resgate', 'valor'] = fund.loc[:, 'Liquidacao_resgate'].values[0]

    if type(fund.loc[:, 'Taxa_ADM'].values[0]) == str:
        tab.loc['Taxa de administração (a.a.)', 'valor'] = fund.loc[:, 'Taxa_ADM'].values[0]
    else:
        tab.loc['Taxa de administração (a.a.)', 'valor'] = \
            fund.loc[:, 'Taxa_ADM'].apply('{:.2%}'.format).str.replace(".", ",").values[0]
    tab.loc['Taxa de administração máxima (a.a.)', 'valor'] = \
        fund.loc[:, 'tx_adm_max'].apply('{:.2%}'.format).str.replace(".", ",").values[0]
    if type(fund.loc[:, 'Taxa_Performance'].values[0]) == str:
        tab.loc['Taxa de performance (a.a.)', 'valor'] = fund.loc[:, 'Taxa_Performance'].values[0]
    else:
        tab.loc['Taxa de performance (a.a.)', 'valor'] = \
            fund.loc[:, 'Taxa_Performance'].apply('{:.2%}'.format).str.replace(".", ",").values[0]
    tab.loc['Taxa de custódia', 'valor'] = \
        fund.loc[:, 'px_cust'].apply('{:.2%}'.format).str.replace(".", ",").values[0]
    tab.loc['Admnistrador', 'valor'] = fund.loc[:, 'Administrador'].values[0]
    tab.loc['Custódia', 'valor'] = fund.loc[:, 'Custodia'].values[0]
    tab.loc['Gestora', 'valor'] = fund.loc[:, 'Gestora'].values[0]
    tab.loc['Perfil de risco', 'valor'] = fund.loc[:, 'perfil_risco'].values[0]
    tab.loc['Tipo de condomínio', 'valor'] = fund.loc[:, 'condominio'].values[0]

    nome = fund.loc[:, 'Nome_Oficial'].values[0]
    cnpj = fund.loc[:, 'CNPJ'].values[0]

    banco = str(int(fund.loc[:, 'banco'].values[0]))
    ag = str(int(fund.loc[:, 'agencia'].values[0]))
    cc = str(int(fund.loc[:, 'conta_corrente'].values[0]))
    horario = str(fund.loc[:, 'lim_mov_aplicacao'].values[0])

    tab.reset_index(inplace=True)
    lines = tab.shape[0]
    left_col = tab.iloc[:lines // 2 + lines % 2].reset_index().iloc[:, 1:]
    right_col = tab.iloc[lines // 2 + lines % 2:].reset_index().iloc[:, 1:]
    features = pd.merge(left_col, right_col, how='outer', left_index=True, right_index=True)

    return html.Div([
        html.Div([
            html.H6('Informações gerais', style={'color': 'black'})
        ]),
        html.Div([
            html.Div([
                dash_table.DataTable(
                    columns=[{"name": str(i), "id": str(i)} for i in features.columns],
                    data=features.to_dict('records'),
                    style_as_list_view=True,
                    editable=True,
                    # merge_duplicate_headers=True,
                    style_cell={'fontSize': 8,
                                'font-family': 'calibri',
                                'textAlign': 'left',
                                'color': 'black',
                                'height': '100%',
                                'padding': '2px',
                                'maxWidth': 0
                                },
                    style_header={
                        'height': '100%',
                        'fontSize': 1,
                        'color': 'rgba(255, 255, 255, 0)',
                        'border-top': '0px'
                    },
                )
            ], className='column_80'),
            html.Div([
                html.P('Informações bacárias', className='thick'),
                html.P('Nome: ' + nome, className='small'),
                html.P('CNPJ: ' + cnpj, className='small'),
                html.P('Banco: ' + banco, className='small'),
                html.P('Agência: ' + ag + ' | ' + 'CC: ' + cc, className='small'),
                html.P('Horário limite para movimentação: ' + horario, className='small'),
            ], className='column_30'),
        ]),
    ], className='features-board')


def months_ptbr(string):
    month_dict = {'January': 'Janeiro',
                  'February': 'Fevereiro',
                  'March': 'Março',
                  'April': 'Abril',
                  'May': 'Maio',
                  'June': 'Junho',
                  'July': 'Julho',
                  'August': 'Agosto',
                  'September': 'Setembro',
                  'October': 'Outubro',
                  'November': 'Novembro',
                  'December': 'Dezembro'}
    for key in month_dict.keys():
        string = string.replace(key, month_dict[key])
    return string


def get_cota(ref_date, parameter, filter_by):
    global FUNDS

    if parameter == "Comercial":
        mask = (FUNDS.loc[:, (FUNDS.columns.str.contains('Comercial')) &
                             (~FUNDS.columns.str.contains('Rebate_Comercial'))] == filter_by).any(axis=1)
        funds = FUNDS.loc[mask]
    else:
        funds = FUNDS.loc[FUNDS[parameter] == filter_by]
    cnpj = tuple(funds.loc[:, 'codBTG'])

    cota = pd.DataFrame()
    if 'FD00000' in cnpj:  # avarga
        ct_alpha = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Passivo/Cota_f001.csv', index_col=0,
                               parse_dates=True).loc[:ref_date, ['Cota']]
        ct_alpha.columns = ['FD00000']
        cota = pd.concat([cota, ct_alpha], axis=1)

    for current_cnpj in cnpj:
        try:
            current_cota = pd.read_csv(
                r'Z:\Gestao\Programas\Python\App\Posicao\_PL_Cotas' + '\\' + current_cnpj[2:] + '.csv', index_col=0,
                parse_dates=True).loc[:, ['Cota_liq']]
            current_cota.columns = [current_cnpj]
            cota = cota.merge(current_cota, how='outer', left_index=True, right_index=True)
            # cota.loc[current_cota.index, current_cnpj] = current_cota.loc[:, 'Cota_liq']
        except FileNotFoundError:
            continue
    if cota.shape[0] == 0: # or cnpj not in set(cota.columns.tolist()):
        current_date = pd.to_datetime(date(2020, 8, 11))
    else:
        current_date = pd.to_datetime(cota.dropna(how='any', axis=0).index.values[-1])

    relative_path = 'Z:/Gestao/Programas/Python/App/Posicao\\'
    while current_date < pd.to_datetime(ref_date):
        day = current_date.strftime('%d').lstrip('0')
        month = current_date.strftime('%m').lstrip('0')
        year = current_date.strftime('%Y')
        path = relative_path + year + '\\' + month + '\\' + day + '\\'
        if os.path.exists(path):
            for file_name in os.listdir(path):
                raw_name = file_name.split('.')[0]
                if raw_name.startswith(cnpj):
                    if file_name.endswith('.xml'):  # fundos btg
                        with open(os.path.join(path, file_name)) as file:
                            content = file.readlines()
                            content = "".join(content)
                            soup = bs(content, "lxml")
                            header = soup.find('header')
                            cota_day = float(header.find('valorcota').text)

                    elif file_name.endswith('.zip'):  # fundos intrader
                        with ZipFile(os.path.join(path, file_name), 'r') as zip_file:
                            patrimonio_csv = [i for i in zip_file.namelist() if 'Patrimonio-Totais' in i]
                            patr = pd.read_csv(zip_file.open(patrimonio_csv[0]), encoding='latin-1', sep=';',
                                               thousands='.', decimal=',')
                            cota_day = patr.loc[0, 'VALORCOTALIQUIDO']
                    cota.loc[current_date, raw_name.split('_')[0]] = cota_day
        current_date += np.timedelta64(1, 'D')
    cota = cota.sort_index()

    # amortização
    amort = pd.read_csv(r'Z:/Gestao/Programas/Python/App/Posicao/_PL_Cotas/_support/amortizacoes_fundos.csv',
                        index_col=0, parse_dates=True)
    amort = amort.loc[:, amort.columns.intersection(cota.columns)].dropna(axis=0)
    if amort.shape[1] != 0:
        for index, row in amort.iterrows():
            for col in row.index.values:
                pct_change = cota.loc[index:, col].pct_change().tolist()
                pct_change[0] = row[col]
                last = cota.loc[cota.index.values[cota.index.tolist().index(index)-1], col]
                cota_fix = [last * (1 + pct_change[0])]
                for i in range(1, len(pct_change)):
                    cota_fix.append(cota_fix[i-1] * (1 + pct_change[i]))
                cota.loc[index:, col] = cota_fix

    return cota


def get_pl(ref_date, parameter, filter_by):
    global FUNDS
    funds = FUNDS.loc[FUNDS[parameter] == filter_by]
    cnpj = tuple(funds.loc[:, 'codBTG'])

    pl = pd.DataFrame()

    for current_cnpj in cnpj:
        try:
            current_pl = pd.read_csv(
                os.path.join(r'Z:/Gestao/Programas/Python/App/Posicao/_PL_Cotas', current_cnpj[2:] + '.csv'),
                index_col=0, parse_dates=True).loc[:, ['PL']]
            current_pl.columns = [current_cnpj]
            pl = pl.merge(current_pl, how='outer', left_index=True, right_index=True)
            # cota.loc[current_cota.index, current_cnpj] = current_cota.loc[:, 'Cota_liq']
        except FileNotFoundError:
            continue
    if pl.shape[0] == 0: # or cnpj not in set(cota.columns.tolist()):
        current_date = pd.to_datetime(date(2020, 8, 11))
    else:
        current_date = pd.to_datetime(pl.dropna(how='any', axis=0).index.values[-1])

    relative_path = 'Z:/Gestao/Programas/Python/App/Posicao\\'
    while current_date < pd.to_datetime(ref_date):
        day = current_date.strftime('%d').lstrip('0')
        month = current_date.strftime('%m').lstrip('0')
        year = current_date.strftime('%Y')
        path = relative_path + year + '\\' + month + '\\' + day + '\\'
        if os.path.exists(path):
            for file_name in os.listdir(path):
                raw_name = file_name.split('.')[0]
                if raw_name.startswith(cnpj):
                    if file_name.endswith('.xml'):  # fundos btg
                        with open(os.path.join(path, file_name)) as file:
                            content = file.readlines()
                            content = "".join(content).replace(',', '.')
                            soup = bs(content, "lxml")
                            header = soup.find('header')
                            pl_day = float(header.find('patliq').text)

                    elif file_name.endswith('.zip'):  # fundos intrader
                        with ZipFile(os.path.join(path, file_name), 'r') as zip_file:
                            patrimonio_csv = [i for i in zip_file.namelist() if 'Patrimonio-Totais' in i]
                            patr = pd.read_csv(zip_file.open(patrimonio_csv[0]), encoding='latin-1', sep=';',
                                               thousands='.', decimal=',')
                            pl_day = patr.loc[0, 'VALORCOTALIQUIDO']  #######
                    pl.loc[current_date, raw_name.split('_')[0]] = pl_day
        current_date += np.timedelta64(1, 'D')
    return pl.sort_index()


def carteira_detalhada(ref_date, cnpj):
    global ativos

    ct = carteira(ref_date, cnpj, pct_pl=False, group_name='_ISIN')
    ct_pct = carteira(ref_date, cnpj, pct_pl=True, group_name='_ISIN')
    ct = pd.merge(ct, ct_pct, on='index', how='left')
    ct.columns = ['_ISIN', 'Valor', '% PL']
    ct = pd.merge(ct, ativos.copy(), on='_ISIN', how='left')
    ct = ct[(ct['Strategy'] == 'CREDITO') | (ct['Strategy'] == 'FIDC')]  # gets debentures and FIDC
    ct.loc[:, 'Rating'] = ct.loc[:, 'RatingF'] + ', ' + ct.loc[:, 'RatingM'] + ', ' + ct.loc[:, 'RatingS']
    ct.loc[:, 'Rating I'] = ct.loc[:, 'RatingIF'] + ', ' + ct.loc[:, 'RatingIM'] + ', ' + ct.loc[:, 'RatingIS']

    for index, row in ct.iterrows():
        if row['Taxa pós'] == '100' and row['Taxa pré'] == '0':
            ct.loc[index, 'Taxa'] = row['Passive']
        elif row['Taxa pós'] == '100':
            ct.loc[index, 'Taxa'] = row['Passive'] + ' ' + row['Taxa pré'] + '%'
        elif row['Taxa pré'] == '0':
            ct.loc[index, 'Taxa'] = row['Taxa pós'] + row['Passive']
        else:
            ct.loc[index, 'Taxa'] = row['Taxa pós'] + row['Passive'] + ' ' + row['Taxa pré'] + '%'

    ct.loc[:, 'Taxa'] = ct.apply(lambda x: x.remuneracao_alvo if x.Strategy == 'FIDC' else x.Taxa, axis=1)
    ct.loc[:, 'Data de Vencimento'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['Data de Vencimento'], axis=1)
    ct.loc[:, '12431'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['12431'], axis=1)
    # ct.loc[:, 'Rating'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['Rating'], axis=1)
    ct.loc[:, 'Rating I'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['Rating I'], axis=1)
    ct.loc[:, 'emissor_ativo'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['emissor_ativo'], axis=1)
    ct.loc[:, 'Setor'] = ct.apply(lambda x: '-' if x.Strategy == 'FIDC' else x['Setor'], axis=1)

    ct = ct.loc[:,
         ['Nickname', '_ISIN', 'Valor', '% PL', 'Taxa', 'Data de Vencimento', '12431', 'Rating', 'Rating I',
          'emissor_ativo', 'Setor']]
    ct.columns = ['Ticker', 'ISIN', 'Valor em carteira (R$)', '% PL', 'Taxa', 'Vencimento', 'Enquadramento Lei 12.431',
                  'Rating *', 'Rating emissor *', 'Emissor', 'Setor']
    ct.loc[:, 'Valor em carteira (R$)'] = ct.loc[:, 'Valor em carteira (R$)'].map('{:,.2f}'.format).str.replace(",",
                                                                                                                "X").str.replace(
        ".", ",").str.replace("X", ".")
    ct.loc[:, '% PL'] = ct.loc[:, '% PL'].round(2).astype(str)
    #
    return ct


def detalhamento_debentures(df):
    global ativos
    # cad = pd.read_csv('Z:\Gestao\Programas\Python\App\Contas\_Ativos\cadastro_ativos.csv', index_col=0)

    bbg = pd.read_csv('Z:/Gestao/Programas/Python/App/Contas/_Ativos/BBG_PRICE.csv', index_col=0).fillna(method='ffill')
    df.columns = ['Code']
    ct = pd.merge(df, ativos.copy(), on='Code', how='inner')
    # ct = ct[(ct['Strategy'] == 'CREDITO')]
    ct.loc[:, 'Rating'] = ct.loc[:, 'RatingF'] + ', ' + ct.loc[:, 'RatingM'] + ', ' + ct.loc[:, 'RatingS']
    ct.loc[:, 'Rating I'] = ct.loc[:, 'RatingIF'] + ', ' + ct.loc[:, 'RatingIM'] + ', ' + ct.loc[:, 'RatingIS']
    ct.loc[:, 'Última taxa negociada'] = '-'

    for index, row in ct.iterrows():

        if row['Taxa pós'] == '100' and row['Taxa pré'] == '0':
            ct.loc[index, 'Taxa'] = row['Passive']
        elif row['Taxa pós'] == '100':
            ct.loc[index, 'Taxa'] = row['Passive'] + ' ' + row['Taxa pré'] + '%'
        elif row['Taxa pré'] == '0':
            ct.loc[index, 'Taxa'] = row['Taxa pós'] + row['Passive']
        else:
            ct.loc[index, 'Taxa'] = row['Taxa pós'] + row['Passive'] + ' ' + row['Taxa pré'] + '%'
        ct.loc[index, 'Última taxa negociada'] = '{:,.2f}'.format(bbg.loc[:, ct.loc[index, 'BBGcode']].values[-1])

    ct = ct.loc[:, ['Nickname', '_ISIN', 'Taxa', 'Última taxa negociada', 'Data de Vencimento', '12431', 'Rating',
                    'Rating I', 'emissor_ativo', 'Setor']]
    ct.columns = ['Ticker', 'ISIN', 'Taxa', 'Última taxa negociada', 'Vencimento', 'Enquadramento Lei 12.431',
                  'Rating *', 'Rating emissor *', 'Emissor', 'Setor']

    return ct


def debenture_future_cash_flows(isin_pu_qtd, ref_date):
    """

    :param isin_list: df com isin e qtd
    :return:
    """
    cf = pd.DataFrame()
    for index, row in isin_pu_qtd.iterrows():
        isin = row['ISIN']
        qtd = row['qtd']
        pu = row['pu']
        current_deb_inf = ativos[ativos['_ISIN'] == isin].iloc[0].astype(str)
        deb_code = current_deb_inf['Code']
        try:
            current_cf = deb.bond_rate(deb_code, pu, ref_date)[0]
        except Exception as e:
            continue
        current_cf.loc[:, 'flow'] = current_cf.loc[:, 'flow'] * qtd
        current_cf.columns = pd.MultiIndex.from_product([[isin], current_cf.columns])
        cf = pd.concat([cf, current_cf], axis=1)
    return cf


# depreciated, should not be uses
def debenture_cash_flow(df, indice, nominal, tx_pre, tx_pos, round_fs=9, round_tdi=8, round_fdi=8, round_fj=9,
                        round_cup=8):
    """
    Calculates the cash flot of a bond
    :param df: dataframe containing dates of the events on the index
    :param indice: index of the bond (IPCA, DI, PRÉ)
    :param nominal: value of the bond
    :param tx_pre: interest rate
    :param tx_pos: interest rate
    :param round_fs: round spread factor
    :param round_tdi: round tx DI
    :param round_fdi: round fator DI
    :param round_fj: round fator de juros
    :param round_cup: round coupon
    :return: dataframe of the cash flow
    """
    if math.isnan(tx_pre):
        tx_pre = 0
    if math.isnan(tx_pos):
        tx_pos = 0
    cf = df.copy()
    dc = DayCounts(dc='bus/252', calendar='anbima')

    # pegar a curva correta to cdi
    # fazer para IPCA

    CDI = pd.read_csv(r'/CSV/CDI.csv', index_col=0, parse_dates=True).loc[:, ['CDI']] / 100
    di = \
    pd.read_csv(r'/CSV/Historico_taxas/Historico_di.csv', index_col=0, parse_dates=True).loc[
        [CDI.index.values[-1]]].T
    di.columns = ['CDI']
    di.index = [dc.workday(date.today(), int(x)) for x in di.index]

    CDI = pd.concat([CDI, di.iloc[1:]], axis=0)

    CDI.loc[:, 'TDI'] = round((CDI.loc[:, 'CDI'] + 1) ** (1 / 252) - 1, round_tdi)
    CDI.loc[:, 'prod'] = 1 + (CDI.loc[:, 'TDI'] * tx_pos / 100)

    # CDI = pd.read_csv(r'Z:\Gestao\Programas\Python\Mateus\test\prod.csv', index_col=0, parse_dates=True).dropna(axis=1, how='all')
    # # pos entra aaqui
    # CDI.loc[:, 'prod'] = 1 + ((CDI.loc[:, 'prod'] - 1) * tx_pos / 100)
    # CDI.loc[:, 'di'] = CDI.loc[:, 'prod'] ** 252 - 1
    # CDI.reset_index(inplace=True)

    cf.loc[:, 'residuo'] = nominal
    cf.loc[:, 'amortz'] = 0
    cf.loc[:, 'cupom'] = 0
    cf.loc[:, 'flow'] = -nominal

    for i in range(1, cf.shape[0]):
        cf.loc[:, 'residuo'].iloc[i] = cf.loc[:, 'residuo'].iloc[i - 1] * (
                1 - cf.loc[:, 'taxa_amortizacao'].iloc[i] / 100)
        cf.loc[:, 'amortz'].iloc[i] = cf.loc[:, 'residuo'].iloc[i - 1] * (cf.loc[:, 'taxa_amortizacao'].iloc[i] / 100)

        spread = round((tx_pre / 100 + 1) ** (dc.days(cf.index.values[i - 1], cf.index.values[i]) / 252), round_fs)
        prod = round(CDI.loc[(CDI.index >= cf.index.values[i - 1]) & (CDI.index < cf.index.values[i]), 'prod'].prod(),
                     round_fdi)
        fj = round(spread * prod, round_fj)
        cf.loc[:, 'cupom'].iloc[i] = round(cf.loc[:, 'residuo'].iloc[i] * (fj - 1), round_cup)
        cf.loc[:, 'flow'].iloc[i] = cf.loc[:, 'cupom'].iloc[i] + cf.loc[:, 'amortz'].iloc[i]

    cf.loc[:, 'flow'].iloc[-1] += cf.loc[:, 'residuo'].iloc[-1]
    return cf.loc[:, ['flow', 'cupom', 'amortz']]


# depreciated, should not be uses
def dur():
    deb_carac = pd.read_csv(r'Z:\Credito Privado\Ativos\Debenture_Caracteristica.csv', encoding='latin-1',
                            parse_dates=True)
    inf_cia = pd.read_csv(r'Z:\Credito Privado\Ativos\inf_cadastral_cia_aberta.csv', encoding='latin-1',
                          parse_dates=True)
    inf_cia['CNPJ'] = 'FD' + inf_cia['CNPJ_CIA'].str.replace('.', '').str.replace('/', '').str.replace('-', '')
    deb_inf = pd.merge(deb_carac, inf_cia, on='CNPJ', how='left')

    CDI = pd.read_csv(r'/Mateus/test/prod.csv', index_col=0, parse_dates=True).dropna(axis=1,
                                                                                      how='all')
    CDI.loc[:, 'di'] = CDI.loc[:, 'prod'] ** 252 - 1

    dc = DayCounts(dc='bus/252', calendar='anbima')

    current_deb_inf = deb_inf[deb_inf['ISIN'] == 'BRCPLEDBS000'].iloc[0].astype(str)

    relative_path = r'Z:/Gestao/Programas/Python/App/Contas/_Ativos/debentures/agenda'
    calendario = pd.read_csv(os.path.join(relative_path, current_deb_inf['Código do Ativo'] + '.csv'),
                             parse_dates=[0, 1])

    calendario = calendario.loc[:, ['Data do Evento', 'Evento', 'taxa', 'flow']]
    first_row = {'Data do Evento': [
        pd.to_datetime(datetime.strptime(current_deb_inf[' Data do Início da Rentabilidade'], '%d/%m/%Y'))],
        'Evento': ['juros'],
        'taxa': [0],
        'flow': [-1 * float(current_deb_inf['Valor Nominal na Emissão'])]}
    calendario = pd.concat([pd.DataFrame(first_row), calendario], ignore_index=True)
    calendario.index = calendario.index + 1
    calendario = calendario.sort_index()
    df = pd.DataFrame(columns=['taxa', 'taxa_amortizacao'])
    for index, row in calendario.iterrows():
        if 'juros' in row['Evento']:
            df.loc[row['Data do Evento'], 'taxa'] = row['taxa']
            # df[row['Data do Evento'], ['flow']] = row['flow']
        if 'Amortizacao' in row['Evento']:
            df.loc[row['Data do Evento'], 'taxa_amortizacao'] = row['taxa']
    df.fillna(0, inplace=True)
    current_cf = debenture_cash_flow(df,
                                     current_deb_inf['Índice'],
                                     float(current_deb_inf['Valor Nominal na Emissão']),
                                     float(
                                         current_deb_inf['Juros Critério Novo - Taxa'].replace('-', 'nan').replace(',',
                                                                                                                   '.')),
                                     float(current_deb_inf['Percentual Multiplicador/Rentabilidade'].replace('-',
                                                                                                             'nan').replace(
                                         ',', '.'))).loc[:, ['flow']]

    current_cf = current_cf.loc['2019-11-6':]
    pu_compra = -1020
    try:
        current_cf.loc[pd.to_datetime(datetime(2019, 11, 6))] = current_cf.loc[
                                                                    pd.to_datetime(datetime(2019, 11, 6))] + pu_compra
    except:
        current_cf.loc[pd.to_datetime(datetime(2019, 11, 6))] = [pu_compra]
    current_cf.sort_index(inplace=True)

    current_cf.loc[:, 'pv'] = 0
    current_cf.loc[:, 'pv_per'] = 0

    for i in range(1, current_cf.shape[0]):
        du = dc.days(current_cf.index.values[0], current_cf.index.values[i])
        du_cdi = current_cf.index.values[i]
        while dc.isbus(du_cdi) is not True:
            du_cdi = du_cdi - np.timedelta64(1, 'D')
        current_cf.loc[:, 'pv'].iloc[i] = current_cf.loc[:, 'flow'].iloc[i] / (1 + CDI.loc[du_cdi, 'di']) ** (du / 252)
        current_cf.loc[:, 'pv_per'].iloc[i] = current_cf.loc[:, 'pv'].iloc[i] * du / 252

    YTM = npf.irr(current_cf.loc[:, 'flow'])
    npv = current_cf.loc[:, 'pv'].sum()
    # npv = npf.npv(0.019, CF.loc[:, 'flow'].iloc[1:])

    dur = (current_cf.loc[:, 'pv_per']).sum() / npv
    mod_dur = dur / (1 + YTM)

    print('YMT: ', YTM)
    print('Duration: ', dur)
    print('Modified duration: ', mod_dur)

    return None


if __name__ == "__main__":
    # cota = get_cota(datetime(2020, 10, 2), 'codBTG', 'FD10348215000151')
    # cota_dummy = pd.DataFrame(1, index=cota.index, columns=['cota'])
    # cota_dummy.index.names = ['Date']
    # reto_mes = ret_mes(cota_dummy).iloc[-1]['CDI_ACUM'].T
    # reto_ano = ret_ano(cota_dummy).iloc[-1]['CDI_ACUM'].T
    # deb_dur_spread_pz(date(2020,10,13), 'FD10348215000151')

    # carteira(date(2020,10,13), 'FD10348215000151', pct_pl=True, group_name = 'Nickname', drop_compromiss = True)
    #                                                                                                              quantity = False)
    # deb_dur_spread_pz(date(2021,2,26), 'FD10348215000151')
    # aaaa = get_cota(date(2021,2,26),  'codBTG', 'FD39846562000196')
    # ret_table('39846562000196',date(2021,2,26), aaaa)
    performance_attribution('FD10348215000151', date(2021,5,31), group_name='Nickname')
    # aaaaaaaaaaaaaaa = get_last_trades(date(2021,1,29)-timedelta(120), date(2021,1,29), 'FD10348215000151')
    # aa = deb_dur_spread_pz(date(2020, 11, 18), 'FD10348215000151')

    # ct = carteira(date(2020,10,15), 'FD10348215000151', group_name='_ISIN', quantity=True)
    # cre = ativos[ativos['tp_ativo']=='DEBENTURE']
    #
    # cd = pd.merge(ct, cre, left_on='index', right_on='_ISIN', how='inner')
    #
    # cd = cd.loc[:, ct.columns]
    # cd.columns = ['ISIN', 'pu', 'qtd']
    # aaaaaa = debenture_future_cash_flows(cd, date(2020,10,15))

    # get_cota(date(2020,10,13), 'codBTG', 'FD10348215000151')

    print('')

