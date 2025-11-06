import pandas as pd
import sqlite3

need_medication=pd.read_excel(r'files/健保碼與許可證.xlsx')

conn=sqlite3.connect(r'files/med_info.db')

sql_nih_to_tfda="""
SELECT 藥品代號
, 許可證字號
, 單複方
FROM 健保藥品清單"""

nih_to_tfda=pd.read_sql(sql_nih_to_tfda,conn)

#先把許可證字號串起來
need_medication=pd.merge(need_medication,nih_to_tfda,how='left',left_on='健保碼', right_on='藥品代號')

#篩出沒有許可證字號的另外處理
need_medication[need_medication['許可證字號'].isnull()]

need_medication2=need_medication[need_medication['許可證字號'].isnull()]
need_medication2['許可證字號']=need_medication2['許可證字號_HIS']
need_medication2=need_medication2[need_medication2['許可證字號']!=' ']

need_medication=pd.concat([need_medication[~need_medication['許可證字號'].isnull()],need_medication2])

#簡化條件，先做單方
need_medication=need_medication[need_medication['單複方']=='單方']

sql_tfda_to_content="""
SELECT 成分名稱
, 成分代碼
, 含量
, 含量單位
, 許可證字號
FROM 詳細處方成分"""

tfda_to_content=pd.read_sql(sql_tfda_to_content, conn)



need_medication=pd.merge(need_medication,tfda_to_content,how='left',on='許可證字號')
# FDA的成分表裡面會有重複的資料
need_medication=need_medication.drop_duplicates(subset=['許可證字號','成分名稱','含量', '含量單位'])
need_medication=need_medication.dropna(subset='成分名稱')

def find_rxcui(tty_type, keyword):
    #rxnom sqlite link
    rxnorm_conn=sqlite3.connect('files/rxnorm_prescribe.db')
    sql_in="""
    SELECT RXCUI
    FROM RXNCONSO
    WHERE TTY='tty_type'
    AND UPPER(STR) like UPPER('%keyword%')"""
    #keyword='rosuvastatin calcium'
    sql_in=sql_in.replace('keyword',keyword)
    sql_in=sql_in.replace('tty_type',tty_type)
    in_df=pd.read_sql(sql_in, rxnorm_conn)
    return in_df

def add_rxcui(row):
    keyword=row['成分名稱']
    tty_type='PIN'
    in_df=find_rxcui(tty_type, keyword)
    if in_df.empty==False:
        return in_df['RXCUI'].iloc[0]
    else:
        return None

need_medication['PIN']=need_medication.apply(add_rxcui,axis=1)
