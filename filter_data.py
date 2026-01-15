import pandas as pd
import numpy as np
import sqlite3
import requests
from xml.etree import ElementTree

def reuse_dict(keyword):
    _dict={'search_field_type':['學名', '英文名', '中文名', 'ATC_CODE', '許可證字號', '健保碼']}
    return _dict[keyword]

def his_link_licence(need_medication): #HIS藥檔轉許可證字號
    """need_medication：HIS藥檔
    
    HIS藥檔轉許可證字號
    
    說明：
    HIS藥檔需要欄位：'院內碼', '健保碼', '許可證字號_HIS'
    """
    #藥檔的資料
    need_medication=pd.read_excel(r'files/健保碼與許可證.xlsx')

    #政府開放資源的藥品資訊
    conn=sqlite3.connect(r'files/med_info.db')

    #政府開放資源中取健保碼、許可證字號、單複方
    sql_nih_to_tfda="""
    SELECT 藥品代號 --健保碼
    , 許可證字號
    , 單複方
    FROM 健保藥品清單"""
    nih_to_tfda=pd.read_sql(sql_nih_to_tfda,conn)

    #先把許可證字號串起來
    need_medication=pd.merge(need_medication,nih_to_tfda,how='left',left_on='健保碼', right_on='藥品代號')

    #篩出沒有許可證字號的另外處理，這些可能是自費藥，所以沒有健保碼
    need_medication2=need_medication[need_medication['許可證字號'].isnull()]
    #HIS內有建一些許可證字號，看有沒有
    need_medication2['許可證字號']=need_medication2['許可證字號_HIS']
    #沒有的話就在篩掉
    need_medication2=need_medication2[need_medication2['許可證字號']!=' ']

    #有許可證字號和沒有的合併
    need_medication=pd.concat([need_medication[~need_medication['許可證字號'].isnull()],need_medication2])
    return need_medication

def merge_contain_dose_from_tfda(need_medication): #把成分、含量、含量單位加回去，這邊要注意有可能一個許可證字號有不同含量
    #政府開放資源的藥品資訊
    conn=sqlite3.connect(r'files/med_info.db')
    
    sql_tfda_to_content="""
    SELECT 成分名稱
    , 成分代碼
    , 含量
    , 含量單位
    , 許可證字號
    FROM 詳細處方成分"""

    tfda_to_content=pd.read_sql(sql_tfda_to_content, conn)

    #串TFDA的藥品含量與單位
    need_medication=pd.merge(need_medication,tfda_to_content,how='left',on='許可證字號')
    # FDA的成分表裡面會有重複的資料
    need_medication=need_medication.drop_duplicates(subset=['許可證字號','成分名稱','含量', '含量單位'])
    need_medication=need_medication.dropna(subset='成分名稱')
    return need_medication

def find_licence_in_tfda(keyword: str, field_type: str, used: bool = True):
    """
    藥品關鍵字查詢許可證字號
    
    :param keyword: 搜尋關鍵字
    :param flied_type: 查詢類別
    :param used: 使用中->True, 停用->False,  預設使用中
    :return: 說明
    :rtype: DataFrame
    """
    #政府開放資源的藥品資訊
    conn=sqlite3.connect(r'files/med_info.db')
    if field_type.lower()=='all':
        field_type=reuse_dict('search_field_type')
    else:
        field_type=[field_type]
    
    field_sql_dict={'學名': 'lower(全部藥品許可證.主成分略述) like lower("%_keyword_%")',
                    '英文名': 'lower(全部藥品許可證.英文品名) like lower("%_keyword_%")',
                    '中文名': 'lower(全部藥品許可證.中文品名) like lower("%_keyword_%")',
                    'ATC_CODE': 'lower(ATC_code.代碼) like lower("_keyword_%")',
                    '許可證字號': 'lower(全部藥品許可證.許可證字號) like lower("%_keyword_%")',
                    '健保碼': 'lower(健保藥品清單.藥品代號) like ("%_keyword_%")',}
    result=pd.DataFrame()
    for type in field_type:
        sql="""
        SELECT 全部藥品許可證.許可證字號 許可證字號
        , 全部藥品許可證.英文品名 英文名
        , 全部藥品許可證.中文品名 中文名
        , 全部藥品許可證.主成分略述 學名
        FROM 全部藥品許可證
        LEFT JOIN ATC_code ON 全部藥品許可證.許可證字號=ATC_code.許可證字號 
        LEFT JOIN 健保藥品清單 ON 全部藥品許可證.許可證字號=健保藥品清單.許可證字號 
        WHERE 
        """
        sql=sql+field_sql_dict[type]
        if used==True:
            sql=sql+'\n'+"""AND 全部藥品許可證.註銷狀態<>'已廢止'
                            AND 全部藥品許可證.註銷狀態<>'已註銷'"""
        sql=sql.replace('_keyword_', keyword)
        temp=pd.read_sql(sql, conn)
        result=pd.concat([temp,result])
        result=result.drop_duplicates(subset=['許可證字號'])
    return result

def find_rxcui(tty_type, keyword): #用TTY和學名找RXNORM
    """tty_type：Rxnorm術語類型，如：IN、PIN、SCDC
    keyword：藥物學名
    結果：Dataframe，內容是rxnorm
    說明
    rxnom sqlite link
    這邊使用離線的rxnorm資料庫，這個資料庫的缺點是只有目前還在使用中的處方藥"""
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

def add_rxcui_in_pin_scdc(row, tty_type):
    """
    row：所需欄位：'成分名稱', '成分串接', '含量', '含量單位'
    tty_type：Rxnorm術語類型，目前只接受下列tty：IN、PIN、SCDC、MIN
    給dataframe的apply用，輸出原始的row，另外添加一個column為tty，值為rxnorm的結果。如果沒有資料則返回原來的row
    """
    if tty_type in row.index.tolist(): #先判斷dataframe的column有沒有tty
        if row.isna()[tty_type]!=True: #在判斷tty裡面有沒有資料，有的話先不取代，也不做後續
            row['error']=tty_type + '已存在資料'
            return row
    if tty_type=='SCDC':
        try: #有些含量會是空白，用try去迴避
            dose=float(row['含量'])
            if dose.is_integer()==True: #整數的時候刪掉.0的部分
                dose=str(int(dose))
            else:
                dose=str(dose)
            keyword=row['成分名稱']+' '+ dose + ' ' + row['含量單位']
        except Exception as e:
            row['error']='SCDC error: ' + str(e)
            return row
    elif (tty_type=='IN') or (tty_type=='PIN'):
        keyword=row['成分名稱']
    elif tty_type=='MIN':
        keyword=row['成分串接']
    #tty_type='PIN'
    in_df=find_rxcui(tty_type, keyword)
    if in_df.empty==False: #有查到資料的狀況下，把column_name用tty命名，內部的值放rxnorm
        row[tty_type]= in_df['RXCUI'].iloc[0]
    return row

def get_text_using_node_from_url(url: str, node: str):
    """使用requests由網址取得xml，並搜尋特定節點文字
    url: 網址
    node: xml的節點"""
    response=requests.get(url)
    root=ElementTree.fromstring(response.text)
    if root.find(node) is not None:
        return root.find(node).text
    else:
        return None

def find_without_rxnorm_db(row):
    #沒有資料才做
    if (row.isna()['IN']==True) & (row.isna()['PIN']==True) & (row.isna()['SCDC']==True):
        #IN、PIN、SCDC沒有資料再作
        keyword=row['成分名稱']
        #依API的規則文字處理，如果有鹽基本來是用空格分開，要改用+
        keyword=keyword.replace(' ', '+')
        #findRxcuiByString
        get_rxcui=f'https://rxnav.nlm.nih.gov/REST/rxcui?name={keyword}&search=1'
        rxcui=get_text_using_node_from_url(get_rxcui,'.//rxnormId')
        if rxcui is not None:
            #有找到rxcui才做下一步
            #下一步找tty
            get_tty=f'https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties'
            tty=get_text_using_node_from_url(get_tty,'.//tty')
            row[tty]=rxcui
    return row

def fill_in_pin(row):#用PIN和SCDC把IN或PIN加回去
    def requests_in_pin(row, tty_term):
        key_rxcui=row[tty_term]
        url=f'https://rxnav.nlm.nih.gov/REST/rxcui/{key_rxcui}/related.xml?tty=IN+PIN'
        try:
            response=requests.get(url)
            root=ElementTree.fromstring(response.text)
            _dict=dict()
            for term in root.findall('.//conceptProperties'):
                tty=term.find('.//tty').text
                rxcui=term.find('.//rxcui').text
                if (tty=='PIN') & (row.isna()['PIN']==False) & (row['PIN']!=rxcui): #確認PIN在復原得時候有沒有和之前查出來的結果不一樣
                    row['error']='API PIN is ' + rxcui
                row[tty]=rxcui
        except Exception as e:
            print(url)
            print(e)
            print(row['許可證字號'])
        return row
    if (row.isna()['PIN']==True) & (row.isna()['SCDC']==True): #PIN和SDC都沒有，就pass
        return row
    elif (row.isna()['SCDC']==False): #有SCDC的時候用SCDC做
        return requests_in_pin(row, 'SCDC')
    elif (row.isna()['PIN']==False): #用PIN做
        return requests_in_pin(row, 'PIN')

def for_single_contain(need_medication):
    """單方可以先串上FDA的含量資料後，可以依序查詢
    1. 單方的IN、PIN、SCDC
    2. 由於rxnorm_prescribe裡面只有FDA目前有處方的藥品，有已經沒有處方藥品的DB好像要會員才能取得，因此用API去取得目前不再FDA處方中的
    
    剩餘藥物後續再另外當個案處理
    """
    #區分單複方
    #need_medication=need_medication[need_medication['單複方']=='單方']
    #串上FDA的成分與含量資料
    need_medication=merge_contain_dose_from_tfda(need_medication)
    #這邊要先把column加進去，不然如果查詢結果沒有這些column，在find_without_rxnorm_db會出錯
    need_medication[['IN', 'PIN', 'SCDC']]=np.nan

    need_medication=need_medication.apply(add_rxcui_in_pin_scdc,args=('IN',),axis=1)
    need_medication=need_medication.apply(add_rxcui_in_pin_scdc,args=('PIN',),axis=1)
    need_medication=need_medication.apply(add_rxcui_in_pin_scdc,args=('SCDC',),axis=1)

    need_medication=need_medication.apply(find_without_rxnorm_db, axis=1)
    need_medication=need_medication.apply(fill_in_pin, axis=1)
    return need_medication
    #need_medication=pd.read_pickle('files/temp_single_contain.pkl')

def for_complex_contain(need_medication):
    #區分單複方
    #need_medication=need_medication[need_medication['單複方']=='複方']
    #複方應該要用許可證字號做group去分每個group操作
    need_medication=merge_contain_dose_from_tfda(need_medication)
    need_medication_grouped = (need_medication.groupby("許可證字號")["成分名稱"]
                .agg(lambda x: " / ".join(sorted(pd.Series(x).unique(), key=str.lower)))
                #              分隔字符       不區分大小寫排序   排除重複
                .reset_index()
                .rename(columns={"成分名稱": "成分串接"}))
    need_medication_grouped=need_medication_grouped.apply(add_rxcui_in_pin_scdc,args=('MIN',),axis=1)
    return need_medication
    #筆記一下目前試過的方法
    #1. 把複方的成分串接之後丟上去查MIN，找出來的MIN只有8個，，主要應該是因為MIN的的成分通常沒有鹽基，但TFDA的資料幾乎都有鹽基
    #2. 用FDA api https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getMultiIngredBrand.html
    #   查商品名的API，這個會有的問題是它會查出包含輸入成分的美國商品名，但是不是完全相同，可能會發生台灣有個商品包含2個成分，但美國有某個商品包含有3個，其中有那兩個
    #   錯誤舉例： 衛署藥輸字第023964號 成分：lidocaine / neomycin / polymyxin B，結果： https://rxnav.nlm.nih.gov/REST/brands?ingredientids=8536+7299+6387
    #   但是這個品項是有四個成分的1089096，成分：bacitracin / lidocaine / neomycin / polymyxin B
    #
    #   目前覺得：用單方的方式，把複方的成分都跑出結果，再用RxNav去逐一查品項，產生MIN、SBDC、SCD等
