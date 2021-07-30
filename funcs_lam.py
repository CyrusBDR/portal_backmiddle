import pandas as pd

est=pd.read_csv('estoque.csv',thousands=',',decimal='.')
meses=est['Mês da operação'].drop_duplicates().values
infg=pd.DataFrame()
for m in meses:
    estq=est.loc[est['Mês da operação']==m]
    estq['valor_negociado_mes']=estq['Líquido'].astype(float).sum()
    estq['prazo_medio_carteira']=estq['Prazo Médio Ponderado'].astype(float).sum()
    estq['taxa']=((estq['Desconto'].astype(float)/estq['Valor C/Abatim.'].astype(float))*100)
    estq['taxa_media_ponderada']=(estq['taxa']*(estq['Líquido'].astype(float)/estq['Líquido'].astype(float).sum()))
    estq['taxa_media_carteira'] =str(estq['taxa_media_ponderada'].astype(float).sum())+'%'
    estq['numero_operacoes_mes']=len(estq['Mês da operação'])
    estq['total_cedentes']=len(estq['Fundo'].drop_duplicates())
    estq['ticket_medio_carteira']=estq['Líquido'].astype(float).mean()
    estq['volume_ced']=pd.Series()
    for ced in estq['Fundo'].drop_duplicates().values:
        ind=estq.loc[estq['Fundo']==ced].index.values.tolist()
        estq['volume_ced'][ind]=estq.loc[estq['Fundo']==ced]['Líquido'].astype(float).sum()
    estq['maxima_exp_cedente']=estq['volume_ced'].max()
    estq['volume_sac'] = pd.Series()
    for sac in estq['Nome'].drop_duplicates().values:
        indi = estq.loc[estq['Nome'] == sac].index.values.tolist()
        estq['volume_sac'][indi] = estq.loc[estq['Nome'] == sac]['Líquido'].astype(float).sum()
    estq['maxima_exp_sacado']=estq['volume_sac'].max()
    cedentes=estq.drop_duplicates(subset='Fundo')
    cedentes=cedentes.sort_values(by='volume_ced',ascending=False).reset_index(drop=True)
    top5c=cedentes.loc[:5]['volume_ced'].sum()
    sacados = estq.drop_duplicates(subset='Nome')
    sacados =sacados.sort_values(by='volume_sac', ascending=False).reset_index(drop=True)
    top5s = sacados.loc[:5]['volume_sac'].sum()
    estq['5_maiores_cedentes']=top5c
    estq['5_maiores_sacados']=top5s
    caracteristicas=estq[['Mês da operação','valor_negociado_mes','prazo_medio_carteira','taxa_media_carteira','numero_operacoes_mes',
                          'total_cedentes','ticket_medio_carteira','maxima_exp_cedente','maxima_exp_sacado','5_maiores_cedentes','5_maiores_sacados']]
    infg=infg.append(caracteristicas)

stop


