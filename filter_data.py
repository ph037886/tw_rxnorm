import pandas as pd
import sqlite3

need_medication=pd.read_excel(r'files/健保碼與許可證.xlsx')

conn=sqlite3.connect(r'files/med_info.db')

sql="""
SELECT 藥品代號
, 許可證字號
FROM 健保藥品清單"""

nih_to_tfda=pd.read_sql(sql,conn)

#先把許可證字號串起來
need_medication=pd.merge(need_medication,nih_to_tfda,how='left',left_on='健保碼', right_on='藥品代號')

#篩出沒有許可證字號的另外處理
need_medication[need_medication['許可證字號'].isnull()]

need_medication2=need_medication[need_medication['許可證字號'].isnull()]
need_medication2['許可證字號']=need_medication2['許可證字號_HIS']
need_medication2=need_medication2[need_medication2['許可證字號']!=' ']

need_medication=pd.concat([need_medication[~need_medication['許可證字號'].isnull()],need_medication2])
