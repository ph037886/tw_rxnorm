CREATE TABLE rxnorm_name ( /*column開頭rn*/
    rn_rxcui TEXT PRIMARY KEY, /*主鍵，Rxcui代碼，不會重複*/
    rn_rxcui_name TEXT NOT NULL, /*Rxnorm的藥物名稱*/
    rn_create_time TEXT DEFAULT (datetime('now', 'localtime')) /*建立時間*/
);

/* 留著當教材，有遞移相依的問題，RXCUI和TTY是關聯的
CREATE TABLE tfda_licence_to_rxnorm( /*column開頭tr*/
    tr_id INTEGER PRIMARY KEY AUTOINCREMENT, /*主鍵，自動建立*/
    tr_tfda_licence TEXT NOT NULL, /*許可證字號，同一個許可證字號可能對應到不同rxnorm不會是唯一值*/
    tr_rxcui TEXT NOT NULL, /*rxcui代碼，相同rxcui可能對應到不同藥品*/
    tr_tty TEXT NOT NULL, /*Rxnorm術語類型，如：IN、PIN、SCDC、MIN*/
    tr_create_time TEXT DEFAULT (datetime('now', 'localtime')) /*建立時間*/
);
*/

CREATE TABLE MEDICATION_CODE_TYPE( /*COLUMN開頭MCT，代碼類別對應代碼內容，如RXNORM, LEXIDRUG GLOBAL ID等*/
    MCT_CODE_TYPE INTEGER PRIMARY KEY AUTOINCREMENT, /*主鍵，自動建立，CODE TYPE的代號，也用於和其他表串接*/
    MCT_CODE_SYSTEM TEXT NOT NULL UNIQUE,  /*藥品代碼類別，如RXNORM, LEXIDRUG GLOBAL ID*/
    MCT_DESCRIPTION TEXT, /*藥品代碼類別敘述*/
    MCT_CREATE_TIME TEXT DEFAULT (datetime('now', 'localtime')) /*建立時間*/
);

CREATE TABLE TFDA_LICENCE_TO_CODE( /*COLUMN開頭是TC*/
    CT_ID INTEGER PRIMARY KEY AUTOINCREMENT, /*主鍵，自動建立*/
    CT_TFDA_LICENCE TEXT NOT NULL, /*許可證字號，同一個許可證字號可能對應到不同rxnorm不會是唯一值*/
    CT_CODE_TYPE INTEGER NOT NULL, /*藥品代碼類別的代碼，對應到MEDICATION_CODE_TYPE的MCT_CODE_TYPE*/
    CT_CODE TEXT NOT NULL, /*藥品代碼*/
    CT_CREATE_TIME TEXT DEFAULT (datetime('now', 'localtime')), /*建立時間*/
    UNIQUE (CT_TFDA_LICENCE, CT_CODE_TYPE, CT_CODE),
    FOREIGN KEY (CT_CODE_TYPE) REFERENCES MEDICATION_CODE_TYPE(MCT_CODE_TYPE)
);

CREATE INDEX IF NOT EXISTS idx_tc_licence_type
ON TFDA_LICENCE_TO_CODE(CT_TFDA_LICENCE, CT_CODE_TYPE);

CREATE INDEX IF NOT EXISTS idx_tc_type_code
ON TFDA_LICENCE_TO_CODE(CT_CODE_TYPE, CT_CODE);