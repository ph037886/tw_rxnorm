CREATE TABLE rxnorm_name ( /*column開頭rn*/
    rn_rxcui TEXT PRIMARY KEY, /*主鍵，Rxcui代碼，不會重複*/
    rn_rxcui_name TEXT NOT NULL /*Rxnorm的藥物名稱*/
    rn_create_time TEXT DEFAULT (datetime('now', 'localtime')) /*建立時間*/
);

CREATE TABLE tfda_licence_to_rxnorm( /*column開頭tr*/
    tr_id INTEGER PRIMARY KEY AUTOINCREMENT, /*主鍵，自動建立*/
    tr_tfda_licence TEXT NOT NULL, /*許可證字號，同一個許可證字號可能對應到不同rxnorm不會是唯一值*/
    tr_rxcui TEXT NOT NULL, /*rxcui代碼，相同rxcui可能對應到不同藥品*/
    tr_tty TEXT NOT NULL, /*Rxnorm術語類型，如：IN、PIN、SCDC、MIN*/
    tr_create_time TEXT DEFAULT (datetime('now', 'localtime')) /*建立時間*/
);