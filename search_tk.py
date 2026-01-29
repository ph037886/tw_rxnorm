import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np

import get_rxnorm

#全域變數集中區
loop_entry=list()
#original_rxnorm=dict()
original_rxnorm=list()

def choose_medication(event):
    global original_rxnorm
    e=event.widget
    choose_result=e.item(e.identify('item', event.x, event.y), 'text') #許可證字號
    choose_result_dict={'許可證字號':[choose_result]}
    chooseee_detail=e.item(e.identify('item', event.x, event.y), 'values') #輸出一個values的set，(英文名, 中文名, 學名)
    choose_result_df=pd.DataFrame.from_dict(choose_result_dict) 
    single_contain=get_rxnorm.for_single_contain(choose_result_df)
    single_contain=single_contain.fillna('')
    complex_contain=get_rxnorm.for_complex_contain(choose_result_df)
    complex_contain=complex_contain.fillna('')
    complex_contain=complex_contain[['許可證字號', 'MIN']]
    single_contain=pd.merge(single_contain,complex_contain,how='left',on='許可證字號')
    
    #以下開始把資料插入
    #許可證字號
    tk.Label(choose_result_frame,text=choose_result).grid(column=1,row=0,padx=5,pady=5,sticky='w')
    #商品名、英文名
    tk.Label(choose_result_frame,text=chooseee_detail[0]).grid(column=1,row=1,padx=5,pady=5,sticky='w')
    #中文名
    tk.Label(choose_result_frame,text=chooseee_detail[1]).grid(column=3,row=1,padx=5,pady=5,sticky='w')
    
    i=0
    while i<len(single_contain):
        #row4開始
        tk.Label(choose_result_frame,text=single_contain.iloc[i]['成分名稱']).grid(column=0,row=4+i,padx=5,pady=5,sticky='w')
        tk.Label(choose_result_frame,text=str(float(single_contain.iloc[i]['含量'])) + ' ' + single_contain.iloc[i]['含量單位']).grid(column=1,row=4+i,padx=5,pady=5,sticky='e')
        i+=1
    original_rxnorm=[choose_result] #第0個是許可證字號
    tty_chinese=get_rxnorm.reuse_dict('tty_chinese')
    count=1 #計算rxnorm_result_frame的grid的row使用
    for tty, chinese in tty_chinese.items():
        i=0
        while i < len(single_contain[tty]):
            if single_contain[tty].iloc[i] !='':
                save_var=tk.BooleanVar(value=True)
                tk.Checkbutton(rxnorm_result_frame,variable=save_var).grid(column=0,row=count,padx=5,pady=5)
                rxcui=str(single_contain[tty].iloc[i]) 
                key=tk.Entry(rxnorm_result_frame) 
                key.grid(column=1,row=count,padx=5,pady=5)
                value=tk.Entry(rxnorm_result_frame)
                value.grid(column=2,row=count,padx=5,pady=5)
                original_rxnorm.append((save_var, key, value)) #是否存檔,Rxcui,tty
                key.insert(0, rxcui) 
                value.insert(0, str(tty))
                tk.Label(rxnorm_result_frame,text='(' + chinese + ')').grid(column=3,row=count,padx=5,pady=5)
                drug_name_entry=tk.Label(rxnorm_result_frame)
                drug_name_entry.grid(column=4,row=count,padx=5,pady=5)
                drug_name=get_rxnorm.find_drug_name_use_rxcui(rxcui)
                if drug_name==None: #應該是不會發生
                    pass
                else: 
                    drug_name_entry['text']=drug_name
                count+=1
            i+=1    
    
def do_search(event=None):
    #result_tree.tag_configure('evenColor', background='lightblue')
    result_tree.delete(*result_tree.get_children())
    result_df=get_rxnorm.find_licence_in_tfda(keyword.get(), search_type_var.get(), dc_type_var.get())
    column_name=result_df.columns.to_list()
    i=0
    while i<len(column_name):
        result_tree.heading('#'+str(int(i)),text=column_name[i])
        i+=1
    i=0
    while i<len(result_df):
        result_tree.insert("",index='end',text=result_df.iloc[i]['許可證字號'],values=(result_df.iloc[i]['英文名'], result_df.iloc[i]['中文名'], result_df.iloc[i]['學名']))
        i+=1

def save_to_db():
    global original_rxnorm
    out_rxnorm={'check_save': list(),
            'tr_tfda_licence': list(),
            'tr_rxcui': list(),
            'tr_tty': list(),}
    i=1 #0一定是許可證字號
    while i<len(original_rxnorm):
        out_rxnorm['check_save'].append(original_rxnorm[i][0].get())
        out_rxnorm['tr_tfda_licence'].append(original_rxnorm[0])
        out_rxnorm['tr_rxcui'].append(original_rxnorm[i][1].get())
        out_rxnorm['tr_tty'].append(original_rxnorm[i][2].get())
        i+=1  
    print(out_rxnorm)
    #get_rxnorm.save_licence_rxcui_in_db(output)

root=tk.Tk()

root.title('台灣藥品查詢Rxnorm系統')

#Frame集中
top_frame=tk.Frame(root)
top_frame.pack(fill='x')
main_frame=tk.Frame(root)
main_frame.pack(fill='x')
tail_frame=tk.Frame(root)
tail_frame.pack(fill='x')

#top_frame，查詢介面
#row0
tk.Label(top_frame,text='台灣藥品查詢Rxnorm系統').grid(column=0,row=0,padx=5,pady=5, sticky='e')
#row1
tk.Label(top_frame,text='類別：').grid(column=0,row=1,padx=5,pady=5)
search_type_var=tk.StringVar()
search_type=ttk.Combobox(top_frame,textvariable=search_type_var)
search_type.grid(column=1,row=1,padx=5,pady=5)
search_field_type=(get_rxnorm.reuse_dict('search_field_type'))
search_field_type.append('all')
search_type['value']=search_field_type
search_type.current(0)
tk.Label(top_frame,text='關鍵字：').grid(column=2,row=1,padx=5,pady=5)
keyword=tk.Entry(top_frame)
keyword.grid(column=3,row=1,padx=5,pady=5)
keyword.bind('<Return>', do_search)
ttk.Button(top_frame,text='搜尋',command=do_search).grid(column=4,row=1,padx=5,pady=5)
#row3
dc_type_var=tk.BooleanVar()
tk.Checkbutton(top_frame,text='忽略停用藥品',variable=dc_type_var).grid(column=0,row=3,padx=5,pady=5)

#main_frame，結果介面
#在做兩個框架分別接收查詢結果和rxnorm結果
search_result_frame=tk.LabelFrame(main_frame,text="查詢結果")
search_result_frame.pack(fill='x')
choose_result_frame=tk.LabelFrame(main_frame,text="選擇藥品")
choose_result_frame.pack(fill='both')
rxnorm_result_frame=tk.LabelFrame(main_frame,text="Rxnorm結果")
rxnorm_result_frame.pack(fill='both')

#search_result_frame
result_tree=ttk.Treeview(search_result_frame,columns=('english', 'chinese', 'chemical'))
result_tree.pack()
result_tree.bind('<Double-1>', choose_medication)

#choose_result_frame
#row0
tk.Label(choose_result_frame,text='許可證字號：').grid(column=0,row=0,padx=5,pady=5)
#row1
tk.Label(choose_result_frame, text='商品名：').grid(column=0,row=1,padx=5,pady=5)
tk.Label(choose_result_frame, text='中文名：').grid(column=2,row=1,padx=5,pady=5)
#row2
tk.Label(choose_result_frame, text='學名 + 劑量：').grid(column=0,row=2,padx=5,pady=5)
#row3
tk.Label(choose_result_frame, text='學名').grid(column=0,row=3,padx=5,pady=5)
tk.Label(choose_result_frame, text='劑量').grid(column=1,row=3,padx=5,pady=5)

#rxnorm_result_frame
#row0
tk.Label(rxnorm_result_frame, text='存檔').grid(column=0,row=0,padx=5,pady=5)
tk.Label(rxnorm_result_frame, text='Rxnorm代碼').grid(column=1,row=0,padx=5,pady=5)
tk.Label(rxnorm_result_frame, text='TTY').grid(column=2,row=0,padx=5,pady=5)
tk.Label(rxnorm_result_frame, text='(TTY術語類型)').grid(column=3,row=0,padx=5,pady=5)
tk.Label(rxnorm_result_frame, text='Rxnorm內容').grid(column=4,row=0,padx=5,pady=5)
ttk.Button(rxnorm_result_frame, text='修改', command=save_to_db).grid(column=5,row=0,padx=5,pady=5)

#row4


root.mainloop()