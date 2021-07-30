import dash_html_components as html
from App.Laminas import common as cm
import pandas as pd
import os
import math as m
from calendars import DayCounts
from datetime import timedelta
from App.Riscos.Risk import calc_df

path = os.path.dirname(__file__)

ativos = pd.read_csv(r'/App/Contas/_Ativos/cadastro_ativos.csv')
ativos['_CNPJ'] = ativos['_CNPJ'].str.replace('FD', '')

deb_carac = pd.read_csv(r'Z:\Credito Privado\Ativos\Debenture_Caracteristica.csv', encoding='latin-1')
inf_cia = pd.read_csv(r'Z:\Credito Privado\Ativos\inf_cadastral_cia_aberta.csv', encoding='latin-1')
inf_cia['CNPJ'] = 'FD' + inf_cia['CNPJ_CIA'].str.replace('.', '').str.replace('/', '').str.replace('-', '')
deb_inf = pd.merge(deb_carac, inf_cia, on='CNPJ', how='left').loc[:,
          ['ISIN', 'SETOR_ATIV', 'UF', 'Empresa        ', 'Deb. Incent. (Lei 12.431)']]
deb_inf.columns = ['_ISIN', 'Setor', 'Estado', 'Empresa', '12431']
enq_12431 = {'N': 'Não', 'S': 'Sim', 'nan': 'Não'}
deb_inf['12431'] = deb_inf['12431'].map(enq_12431)
ativos = pd.merge(ativos, deb_inf, on='_ISIN', how='left')
ativos.loc[:, '12431'] = ativos.loc[:, '12431'].fillna('Não')
ativos.loc[ativos['Code'] == "LFT", "Setor"] = "Governo Federal"
ativos.fillna('Outos', inplace=True)


def lam_funds_layout(app):
    # parameter = pd.read_csv(path + '\\lam_parameter.csv', index_col=0)
    date = pd.to_datetime(cm.FUND_LAM_PARAMETERS['date'], format='%Y-%m-%d')
    group_name = cm.FUND_LAM_PARAMETERS['group_name']
    fund = cm.FUND_LAM_PARAMETERS['fund']

    if 'interno' in cm.FUND_LAM_PARAMETERS['p2']:
        uso_interno = True
    else:
        uso_interno = False

    dc = DayCounts('BUS/252', adj=None, calendar='anbima', weekmask='Mon Tue Wed Thu Fri', adjoffset=0)
    is_bus = dc.isbus(date)
    i = 1
    while is_bus is not True:
        date = date - timedelta(i)
        is_bus = dc.isbus(date)
        i += 1
    funds = pd.read_csv(r'/App/Passivo/Fundos.csv', index_col=0)
    funds = funds.loc[funds['Nome'] == fund]
    full_name = funds.loc[:, 'BTGName'].values[0]
    cnpj = funds.loc[:, 'CNPJ'].values[0]
    funds['CNPJ'] = funds['CNPJ'].str.replace('.', '').str.replace('/', '').str.replace('-', '')
    fund_cnpj = funds['CNPJ'].values[0]
    fd_code = funds['codBTG'].values[0]
    publico = funds['Publico'].values[0]

    texto = pd.read_csv(r'/App/Laminas/lam_text.csv')
    texto = texto.loc[texto['Nome'] == fund]
    objetivo = texto.loc[:, 'objetivo'].values[0]
    politica = texto.loc[:, 'politica'].values[0]

    # cota
    if fund == 'Alpha':
        cota = pd.read_csv(r'/App/Passivo/Cota_f001.csv', index_col=0,
                           parse_dates=True).loc[:date, ['Cota']]
        cota.columns = ['FD00000']
    else:
        cota = cm.get_cota(date, 'codBTG', 'FD' + fund_cnpj).loc[:date]

    bench = funds.loc[funds['codBTG'] == 'FD' + fund_cnpj, 'Benchmark'].values[0]
    pct_bench = funds.loc[funds['codBTG'] == 'FD' + fund_cnpj, 'pct_benchmark'].values[0]
    pre_bench = funds.loc[funds['codBTG'] == 'FD' + fund_cnpj, 'pre_benchmark'].values[0]

    ret = cm.rentabilidade(fund, date, parameter='Nome', cota=cota.copy(), benchmark=bench, pct_bench=pct_bench,
                           pre_bench=pre_bench)

    if fund == 'Alpha':
        carteira = pd.read_csv(r'/App/Laminas/risk.csv', index_col=0)
        carteira.columns = ['comp']
        carteira.reset_index(inplace=True)

    else:
        carteira = cm.carteira(date, 'FD' + fund_cnpj, pct_pl=False, group_name='Nickname', drop_compromiss=False)
    comp_carteira = cm.group_carteira(carteira, group_name)

    perf = cm.ret_table(fund_cnpj, date, cota=cota.copy())

    page = [
        html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            # page content
            html.Div([
                # row 1
                html.Div([
                    # right column
                    html.Div([
                        html.Div([
                            html.H6(
                                "Público alvo",
                                className="subtitle pad line"
                            ),
                            html.Div([
                                html.P([
                                    '''
                                    Este fundo tem como públio alvo o Investidor 
                                    ''' + str(publico).strip() + '.'

                                ], className='small')
                            ]),
                            html.H6(
                                "Objetivo",
                                className="subtitle pad line"
                            ),
                            html.Div([
                                html.P([
                                    objetivo
                                ], className='small')
                            ]),
                            html.H6(
                                "Política de investimento",
                                className="subtitle pad line"
                            ),
                            html.Div([
                                html.P([
                                    politica
                                ], className='small')
                            ]),
                        ]),
                    ], className='half_column_lam'),

                    # left column
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Rentabilidade acumulada",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(ret, ret.columns.values, color_palet=True, legendPos='h',
                                                  xaxis_dates=False, axesNames=['', 'Retorno %'])
                            ], className='chart'),
                        ], className='chart-container'),  # style={'height': '260px'}
                    ], className='half_column_lam'),
                ], className='full_column_lam'),

                # Row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                "Rentabilidade",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_dash_table(perf.iloc[-15:])
                        ], style={})
                    ])
                ], className='full_column_lam'),

                # row 2
                html.Div([
                    # right column
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    ["Performance attribution", html.Sup('1')],
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.performance_attribution('FD' + fund_cnpj, date, group_name=group_name)
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                        ], style={'margin-top': '15px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                    # left column
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    # "Componsição da carteira",
                                    'Composição da Carteira',
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.pie_chart(comp_carteira, 'comp', 'index')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                        ], style={'margin-top': '15px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),
                ], className='full_column_lam'),
                # Row 5
                html.Div([
                    html.Div([
                        cm.features_table(fd_code, date)
                    ]),
                ], className='full_column_lam'),

            ], className="sub_page_lam"),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                               1 - Performance attribution mensal e anual calculados desde a dada de início do fundo sob gestão da BRD Investimentos Ltda.
                               '''))
        ], className="page_lam")
    ]

    if 'p2' in cm.FUND_LAM_PARAMETERS['p2']:
        regs = calc_df(fd_code[2:], 60)
        regs.set_index('Data', inplace=True)
        regs = regs.loc[:date]

        beta_anbima = regs.loc[:, ['ambima']]
        beta_ibov = regs.loc[:, ['ibov']]
        beta_PRE = regs.loc[:, ['Pre5y']]
        beta_anbima.loc[:, 'média'] = beta_anbima.loc[:, 'ambima'].mean()
        beta_ibov.loc[:, 'média'] = beta_ibov.loc[:, 'ibov'].mean()
        beta_PRE.loc[:, 'média'] = beta_PRE.loc[:, 'Pre5y'].mean()

        vol = regs.loc[:, ['vol', 'vol_hist']]
        sharpe = regs.loc[:, ['sharpe', 'sharpe_hist']]
        var = regs.loc[:, ['var', 'var_hist']]
        # print(var)
        skew = regs.loc[:, ['skew', 'skew_hist']]
        kurt = regs.loc[:, ['kurt', 'kurt_hist']]

        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Beta Ibov",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(beta_ibov, beta_ibov.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: Bloombeg  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                '%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Beta pre",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(beta_PRE, beta_PRE.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: Bloombeg  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                '%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Beta anbima",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(beta_anbima, beta_anbima.columns.values, color_palet=True,
                                                  legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: Anbima Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                '%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Vol",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(vol, vol.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                ], className='full_column_lam'),

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Sharpe",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(sharpe, sharpe.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Var",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(var, var.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px'}),
                        ], style={'margin-top': '5px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                ], className='full_column_lam'),

                # row 4
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Skew",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(skew, skew.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                        ], style={'margin-top': '15px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Kurt",
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_chart(kurt, kurt.columns.values, color_palet=True, legendPos='h')
                            ], className='chart'),
                        ], className='chart-container'),
                        html.Div([
                            html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                                0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                                   style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                        ], style={'margin-top': '15px', 'vertical-align': 'center'}),
                    ], className='half_column_lam'),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                               '''))
        ], className='page_lam'), )

    if 'p_cred' in cm.FUND_LAM_PARAMETERS['p2']:

        # carteiras por diferentes filtros
        pie_chart_list = ['Strategy', 'Passive', 'Setor', 'grupoeconomico']
        pie_chart_list.remove(group_name)
        carteiras_lits = []
        for i in range(len(pie_chart_list)):
            cart = cm.group_carteira(carteira, pie_chart_list[i])
            carteiras_lits.append(cart)
            pie_chart_list[i] = pie_chart_list[i].replace('Passive', 'Passivo').replace('grupoeconomico',
                                                                                        'Grupo Econômico').replace(
                'Strategy', 'Estratégia')

        # carteria 12431
        carteira_12431 = cm.group_carteira(carteira, '12431')

        # carteira detalhada pelo nome das empresas
        carteira_empresas = cm.carteira(date, 'FD' + fund_cnpj, pct_pl=True, group_name='Nickname',
                                        drop_compromiss=True)
        carteira_empresas = cm.group_carteira(carteira_empresas, 'Empresa')

        carteira_empresas = carteira_empresas[carteira_empresas['index'] != 'Outros']
        carteira_empresas.set_index('index', inplace=True)
        carteira_empresas.sort_values(by=['comp'], inplace=True)

        # carteira detalhada das debêntures
        carteira_detalhada = cm.carteira_detalhada(date, 'FD' + fund_cnpj)
        isin_to_ticker = pd.Series(carteira_detalhada.loc[:, 'Ticker'].values,
                                   index=carteira_detalhada.loc[:, 'ISIN']).to_dict()
        pu_qtd_deb = cm.carteira(date, 'FD' + fund_cnpj, pct_pl=False, group_name='_ISIN', quantity=True)
        pu_qtd_deb.columns = ['ISIN', 'pu', 'qtd']
        deb_isin_pu_qtd = pd.merge(carteira_detalhada.loc[:, ['ISIN']], pu_qtd_deb, on='ISIN', how='left')

        # fluxo projetado das debêntures

        deb_cash_flow = cm.debenture_future_cash_flows(deb_isin_pu_qtd, date)

        deb_fut_events = pd.DataFrame(columns=['Ticker', 'Data', 'Tipo de evento', 'Valor'])
        i = 0
        for index, row in deb_cash_flow.iterrows():
            current_row = row.dropna()
            for ind, value in current_row.items():
                if value == 0.0:
                    continue
                elif ind[1] == 'cup':
                    tipo = 'Pagamento de cupom'
                elif ind[1] == 'amortz':
                    tipo = 'Pagamento de amortização'
                else:
                    continue
                deb_fut_events.loc[i, ['Ticker', 'Data', 'Tipo de evento', 'Valor']] = [ind[0],
                                                                                        index.strftime('%d/%m/%Y'),
                                                                                        tipo,
                                                                                        'R${:,.2f}'.format(
                                                                                            value).replace(',',
                                                                                                           'X').replace(
                                                                                            '.', ',').replace('X', '.')]
            i += 1
        deb_fut_events.loc[:, 'Ticker'] = deb_fut_events.loc[:, 'Ticker'].replace(isin_to_ticker)

        if not deb_cash_flow.empty:
            deb_cash_flow = deb_cash_flow.loc[:, deb_cash_flow.columns.get_level_values(1).isin({'flow'})]
            deb_cash_flow.columns = deb_cash_flow.columns.get_level_values(0)
            deb_cash_flow = deb_cash_flow.groupby([deb_cash_flow.index.year, deb_cash_flow.index.month]).sum().sum(
                axis=1).to_frame(name='flow')
            deb_cash_flow.index = pd.to_datetime(deb_cash_flow.index.get_level_values(0).astype(str) + '-' +
                                                 deb_cash_flow.index.get_level_values(1).astype(str) + '-1',
                                                 format='%Y-%m-%d')
            deb_cash_flow = deb_cash_flow.loc[:date + timedelta(365)]
        else:
            deb_cash_flow = pd.DataFrame(columns=['flow'])

        dur_spread_pz = cm.deb_dur_spread_pz(date, 'FD' + fund_cnpj)

        last_trades = cm.get_last_trades(date - timedelta(120), date, 'FD' + fund_cnpj)
        last_trades.loc[:, 'Data da operação'] = last_trades.loc[:, 'Data da operação'].dt.strftime('%d/%m/%Y')

        last_trades.loc[:, 'Preço'] = last_trades.loc[:, 'Preço'].apply('R${:,.2f}'.format).str.replace(",",
                                                                                                        "X").str.replace(
            ".", ",").str.replace("X", ".")
        last_trades.loc[:, 'Taxa'] = last_trades.loc[:, 'Taxa'].apply('%{:,.2f}'.format).str.replace(".", ",")

        ativos_aprovados = pd.read_csv(r'Z:\Credito Privado\19-Comitê Crédito\ativosaprovados.csv', usecols=['Ativos'])
        ativos_aprovados = ativos_aprovados.iloc[18:, [0]]
        ativos_aprovados = cm.detalhamento_debentures(ativos_aprovados)

        # page 2
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1 - portifolio informatio - pie charts
                html.Div([

                    # sub_row1
                    html.Div([

                        # chart 1
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H6(
                                        children=pie_chart_list[0],
                                        className="subtitle pad line"
                                    ),
                                ]),
                                html.Div([
                                    cm.pie_chart(carteiras_lits[0], 'comp', 'index')
                                ], className='chart'),
                            ], className='chart-container', style={'height': '250px'}),
                            html.Div([
                                html.P([
                                    'Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                        '%d/%m/%Y') + ' 00:00'],
                                    style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                            ], style={'margin-top': '15px', 'vertical-align': 'center'}),

                        ], className='half_column_lam'),
                        # chart 2
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H6(
                                        children=pie_chart_list[1],
                                        className="subtitle pad line"
                                    ),
                                ]),
                                html.Div([
                                    cm.pie_chart(carteiras_lits[1], 'comp', 'index')
                                ], className='chart'),
                            ], className='chart-container', style={'height': '250px'}),
                            html.Div([
                                html.P([
                                    'Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                        '%d/%m/%Y') + ' 00:00'],
                                    style={'color': 'black', 'font-size': '7px'}),
                            ], style={'margin-top': '15px', 'vertical-align': 'center'}),

                        ], className='half_column_lam'),

                    ], className='full_column_lam'),

                    # sub_row2
                    html.Div([

                        # chart 1
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H6(
                                        children=pie_chart_list[2],
                                        className="subtitle pad line"
                                    ),
                                ]),
                                html.Div([
                                    cm.pie_chart(carteiras_lits[2], 'comp', 'index')
                                ], className='chart'),
                            ], className='chart-container', style={'height': '250px'}),
                            html.Div([
                                html.P([
                                    'Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                        '%d/%m/%Y') + ' 00:00'],
                                    style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                            ], style={'margin-top': '15px', 'vertical-align': 'center'}),

                        ], className='half_column_lam'),
                        # chart 2
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H6(
                                        "Enquadramento 12431",
                                        className="subtitle pad line"
                                    ),
                                ]),
                                html.Div([
                                    cm.pie_chart(carteira_12431, 'comp', 'index')
                                ], className='chart'),
                            ], className='chart-container', style={'height': '250px'}),
                            html.Div([
                                html.P([
                                    'Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                        '%d/%m/%Y') + ' 00:00'],
                                    style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                            ], style={'margin-top': '15px', 'vertical-align': 'center'}),

                        ], className='half_column_lam'),

                    ], className='full_column_lam'),

                ], className=''),

                # row 2 - carteira por empresa
                html.Div([
                    html.Div([
                        html.H6(
                            "Detalhamento do portifólio por empresa",
                            className="subtitle pad line"
                        ),
                    ]),
                    html.Div([
                        cm.generate_chart(carteira_empresas, ['comp'], color_palet=True, chartType='bar',
                                          bar_chart_orientation='h', axesNames=['% PL', ''],
                                          texttemplate='%{text:.2f}%', textposition='outside')
                    ], className='chart-container'),
                ], className='full_column_lam'),
                html.Div([
                    html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                        '%d/%m/%Y') + ' 00:00'],
                           style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                ], style={'margin-top': '15px', 'vertical-align': 'center'}),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno))
        ], className='page_lam'), )

        # page 3
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                "Carteira de crédito detalhada",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_dash_table(carteira_detalhada)
                        ]),
                    ]),
                    html.Br(),
                    html.Div([
                        html.P(["* Ratings Fitch, Moody's e S&P (Standard & Poor´s) respectivamente" + '\n' +
                                'Fonte: http://www.cvm.gov.br/, Bloomberg.  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px', 'white-space': 'pre'}),
                    ]),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                ["Fluxo de caixa projetado (cupons/amortizações)", html.Sup('1')],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_chart(deb_cash_flow, ['flow'], color_palet=True, chartType='bar',
                                              xaxis_dates=False, textposition='outside', texttemplate='R$ %{text:,.2f}',
                                              axesNames=['Meses', 'Fluxo projetado (R$)'])
                        ], className='chart-container'),
                    ]),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                               1 - Fluxo de caixa projetado dos pagamentos de cupons e amortizações nos próximos 12 meses apenas das debêntures.
                               '''))
        ], className='page_lam'), )

        # page 4
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                "Últimos ativos negociados",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_dash_table(last_trades)
                        ]),
                    ]),
                    html.Br(),
                    html.Div([
                        html.P(['Fonte: BDR AM.  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px', 'white-space': 'pre'}),
                    ]),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                ["Proximos eventos", html.Sup('1')],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_dash_table(deb_fut_events.iloc[:8]),
                        ]),
                    ]),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                                       1 - Proximos eventos de pagamentos de amortização e cupom das debêntures que fazem parte do patrimônio do fundo. Valores estimados com base na taxa de negociação da debênture no dia de referência deste informativo.

                                       '''))
        ], className='page_lam'), )

        # page 5
        threshold = 30
        for i in range(m.ceil(ativos_aprovados.shape[0] / threshold)):
            page.append(html.Div([
                html.Div(
                    cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

                html.Div([
                    # row 3
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6(
                                    ["Debêntures aprovadas para negociação", html.Sup('1')],
                                    className="subtitle pad line"
                                ),
                            ]),
                            html.Div([
                                cm.generate_dash_table(ativos_aprovados.iloc[threshold * i:threshold * (i + 1)]),
                            ]),
                            html.Br(),
                            html.Div([
                                html.P(["* Ratings Fitch, Moody's e S&P (Standard & Poor´s) respectivamente" + '\n' +
                                        'Fonte: http://www.cvm.gov.br/, Bloomberg.  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                                    '%d/%m/%Y') + ' 00:00'],
                                       style={'color': 'black', 'font-size': '7px', 'padding': '3px',
                                              'white-space': 'pre'}),
                            ]),
                        ]),

                    ], className='full_column_lam'),
                ], className='sub_page_lam'),
                html.Div(cm.footer(app,
                                   uso_interno=uso_interno,
                                   additional_text='''
                                       1 - Debêntures aprovadas pelo ''' + funds.loc[:, 'Administrador'].values[0] + ''' para negociação.
                                       '''))
            ], className='page_lam'))

        # page 6
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                children=["Prazo médio da carteira", html.Sup('1')],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_chart(dur_spread_pz, ['pz_med'], color_palet=True,
                                              axesNames=['', 'Prazo médio (anos)'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                            0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                children=["Duration média da carteira", html.Sup('2')],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_chart(dur_spread_pz, ['m_dur'], color_palet=True,
                                              axesNames=['', 'Duration modified (anos)'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                            0] + ', Anbima. Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),

                # row 3
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                children=["Spread de crédito médio da carteira", html.Sup('3')],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_chart(dur_spread_pz, ['spread'], color_palet=True,
                                              axesNames=['', 'Spread de crédito (%)'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                            0] + ', Anbima.  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),
                # row 4
                # html.Div([
                #     html.Div([
                #         html.Div([
                #             html.H6(
                #                 children=["Spread IPCA médio da carteira", html.Sup('5')],
                #                 className="subtitle pad line"
                #             ),
                #         ]),
                #         html.Div([
                #             cm.generate_chart(dur_spread_pz, ['spread_ipca'], color_palet=True,
                #                               axesNames=['', 'Spread de IPCA (%)'])
                #         ], className='chart-container', style={'height': '170px'}),
                #     ]),
                #     html.Div([
                #         html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                #             0] + ', Anbima.  Elaboração: BRD AM  Consulta em: ' + date.strftime(
                #             '%d/%m/%Y') + ' 00:00'],
                #                style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                #     ]),
                #
                # ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                               1 - Prazo médio da carteira, ponderando o prazo médio de cada ativo pelo peso dele na carteira.
                               2 - Duration modificada. Calculada apenas para os ativos de crédito (debêntures). Ponderada pelo peso de cada debênture na carteira.
                               3 - Spread de crédito médio das debêntures, ponderado pelo peso de cada debênture na carteira do fundo.
                               '''
                               ))
        ], className='page_lam'), )

        # page 7
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                children="Rentabilidade histórica",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            cm.generate_dash_table(perf)
                        ]),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),
                    html.Div([
                        html.Div([
                            html.H6(
                                children="Rentabilidade acumulada 24 mêses",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_table(perf)
                            cm.generate_chart(
                                cm.rentabilidade(fund, date, parameter='Nome',
                                                 cota=cota.loc[date - timedelta(365 * 2):], benchmark=bench,
                                                 pct_bench=pct_bench), ret.columns.values,
                                color_palet=True, legendPos='h', xaxis_dates=False,
                                axesNames=['', 'Retorno %'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text=''''''
                               ))
        ], className='page_lam'), )

        # page 8
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                children="Rentabilidade acumulada 12 meses",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_table(perf)
                            cm.generate_chart(
                                cm.rentabilidade(fund, date, parameter='Nome',
                                                 cota=cota.loc[date - timedelta(365):], benchmark=bench,
                                                 pct_bench=pct_bench), ret.columns.values,
                                color_palet=True, legendPos='h', xaxis_dates=True,
                                axesNames=['', 'Retorno %'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),
                    html.Div([
                        html.Div([
                            html.H6(
                                children="Rentabilidade acumulada 24 meses",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_table(perf)
                            cm.generate_chart(
                                cm.rentabilidade(fund, date, parameter='Nome',
                                                 cota=cota.loc[date - timedelta(365 * 2):], benchmark=bench,
                                                 pct_bench=pct_bench), ret.columns.values,
                                color_palet=True, legendPos='h', xaxis_dates=True,
                                axesNames=['', 'Retorno %'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),
                    html.Div([
                        html.Div([
                            html.H6(
                                children="Rentabilidade acumulada início",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_table(perf)
                            cm.generate_chart(
                                ret, ret.columns.values,
                                color_palet=True, legendPos='h', xaxis_dates=False,
                                axesNames=['', 'Retorno %'])
                        ], className='chart-container'),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text=''''''
                               ))
        ], className='page_lam'), )

    if 'p_fof' in cm.FUND_LAM_PARAMETERS['p2']:
        carteira_fundos = cm.carteira(date, fd_code, pct_pl=True, group_name='Nickname', drop_compromiss=False)
        carteira_fundos.set_index('index', inplace=True)
        carteira_fundos.sort_values(by=['comp'], inplace=True)

        # page 2
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([
                # row 2 - carteira por empresa
                html.Div([
                    html.Div([
                        html.H6(
                            "Detalhamento do portifólio",
                            className="subtitle pad line"
                        ),
                    ]),
                    html.Div([
                        cm.generate_chart(carteira_fundos, ['comp'], color_palet=True, chartType='bar',
                                          bar_chart_orientation='h', axesNames=['% PL', ''],
                                          texttemplate='%{text:.2f}%', textposition='outside')
                    ], className='chart-container'),
                ], className='full_column_lam'),
                html.Div([
                    html.P(['Fonte: ' + funds.loc[:, 'Administrador'].values[
                        0] + ' Elaboração: BRD AM  Consulta em: ' + date.strftime('%d/%m/%Y') + ' 00:00'],
                           style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                ], style={'margin-top': '15px', 'vertical-align': 'center'}),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno))
        ], className='page_lam'), )

        # page 3
        page.append(html.Div([
            html.Div(cm.header(app, full_name, 'CNPJ: ' + cnpj, cm.months_ptbr('{}'.format(date.strftime('%B | %Y'))))),

            html.Div([

                # row 1
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                "Carteira de crédito detalhada",
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_tabe(carteira_detalhada)
                        ]),
                    ]),
                    html.Div([
                        html.P(['Fonte: http://www.cvm.gov.br/ Elaboração: BRD AM  Consulta em: ' + date.strftime(
                            '%d/%m/%Y') + ' 00:00'],
                               style={'color': 'black', 'font-size': '7px', 'padding': '3px'}),
                    ]),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                ["Fluxo de caixa projetado (cupons/amortizações)"],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_chart(deb_cash_flow, ['flow'], color_palet=True, chartType='bar', xaxis_dates=True, textposition='outside', texttemplate='R$ %{text:,.2f}', axesNames=['Meses', 'Fluxo projetado (R$)'])
                        ], className='chart-container'),
                    ]),

                ], className='full_column_lam'),

                # row 2
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6(
                                ["Proximos eventos"],
                                className="subtitle pad line"
                            ),
                        ]),
                        html.Div([
                            # cm.generate_dash_tabe(deb_fut_events.iloc[:10]),
                        ]),
                    ]),

                ], className='full_column_lam'),

            ], className='sub_page_lam'),
            html.Div(cm.footer(app,
                               uso_interno=uso_interno,
                               additional_text='''
                               '''))
        ], className='page_lam'), )

    return html.Div(page)
