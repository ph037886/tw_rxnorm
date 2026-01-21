import tkinter as tk
from tkinter import ttk
import pandas as pd

import get_rxnorm

def choose_medication(event):
    e=event.widget
    choose_result=e.item(e.identify('item', event.x, event.y), 'text') #許可證字號
    choose_result_dict={'許可證字號':[choose_result]}
    chooseee_detail=e.item(e.identify('item', event.x, event.y), 'values') #輸出一個values的set，(英文名, 中文名, 學名)
    choose_result_df=pd.DataFrame.from_dict(choose_result_dict) 
    single_contain=get_rxnorm.for_single_contain(choose_result_df)
    complex_contain=get_rxnorm.for_complex_contain(choose_result_df)
    
    #以下開始把資料插入
    #許可證字號
    tk.Label(rxnorm_result_frame,text=choose_result).grid(column=1,row=0,padx=5,pady=5,sticky='w')
    #商品名、英文名
    tk.Label(rxnorm_result_frame,text=chooseee_detail[0]).grid(column=1,row=1,padx=5,pady=5,sticky='w')
    #中文名
    tk.Label(rxnorm_result_frame,text=chooseee_detail[1]).grid(column=3,row=1,padx=5,pady=5,sticky='w')
    #學名 + 劑量
    chemical_dose=''
    i=0
    while i<len(single_contain):
        print(single_contain.iloc[i])
        chemical_dose=chemical_dose + single_contain.iloc[i]['成分名稱'] + '\t' + str(float(single_contain.iloc[i]['含量'])) + ' ' + single_contain.iloc[i]['含量單位'] + '\n'
        i+=1
    tk.Label(rxnorm_result_frame,text=chemical_dose).grid(column=1,row=2,padx=5,pady=5,sticky='w')
    print(single_contain)
    
    
def do_search():
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

root=tk.Tk()

#Frame集中
top_frame=tk.Frame(root)
top_frame.pack()
main_frame=tk.Frame(root)
main_frame.pack()
tail_frame=tk.Frame(root)
tail_frame.pack()

#top_frame，查詢介面
#row0
tk.Label(top_frame,text='Rxnorm查詢系統').grid(column=0,row=0,padx=5,pady=5)
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
ttk.Button(top_frame,text='搜尋',command=do_search).grid(column=4,row=1,padx=5,pady=5)
#row3
dc_type_var=tk.BooleanVar()
tk.Checkbutton(top_frame,text='忽略停用藥品',variable=dc_type_var).grid(column=0,row=3,padx=5,pady=5)

#main_frame，結果介面
#在做兩個框架分別接收查詢結果和rxnorm結果
search_result_frame=tk.LabelFrame(main_frame,text="查詢結果")
search_result_frame.pack(fill='x')
rxnorm_result_frame=tk.LabelFrame(main_frame,text="Rxnorm結果")
rxnorm_result_frame.pack(fill='both')

result_tree=ttk.Treeview(search_result_frame,columns=('english', 'chinese', 'chemical'))
result_tree.pack()
result_tree.bind('<Double-1>', choose_medication)

#row0
tk.Label(rxnorm_result_frame,text='許可證字號：').grid(column=0,row=0,padx=5,pady=5)
#license_text=tk.Entry(rxnorm_result_frame)
#license_text.grid(column=1,row=0,padx=5,pady=5)
#row1
tk.Label(rxnorm_result_frame, text='商品名：').grid(column=0,row=1,padx=5,pady=5)
tk.Label(rxnorm_result_frame, text='中文名：').grid(column=2,row=1,padx=5,pady=5)
#row4
tk.Label(rxnorm_result_frame, text='學名 + 劑量：').grid(column=0,row=2,padx=5,pady=5)
#row3
tk.Label(rxnorm_result_frame, text='Rxnorm：').grid(column=0,row=3,padx=5,pady=5)
#row4


root.mainloop()