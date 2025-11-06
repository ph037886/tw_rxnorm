import sqlite3, csv, os, sys
from pathlib import Path

# 使用方式：python load_rxnorm_to_sqlite.py /path/to/rrf rxnorm_prescribe.db
#rrf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("rrf")
#db_path = sys.argv[2] if len(sys.argv) > 2 else "rxnorm_prescribe.db"
rrf_dir = Path(r'C:\Users\cjs01\Downloads\RxNorm_full_prescribe_10062025\rrf')
db_path = "files/rxnorm_prescribe.db"

def ensure_table(conn, table, n_cols):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if cur.fetchone():
        return
    cols = ", ".join([f"c{i} TEXT" for i in range(1, n_cols+1)])
    cur.execute(f"CREATE TABLE {table} ({cols})")

def count_cols_of_first_line(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter='|')
        first = next(reader)
        # RRF 每行最後有一個空欄位（因為結尾 '|')，去掉最後一個空字串
        if len(first) > 0 and first[-1] == '':
            first = first[:-1]
        return len(first)

def rows_generator(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter='|')
        for row in reader:
            if row and row[-1] == '':
                row = row[:-1]  # 去掉尾端空欄位
            yield [None if x == "" else x for x in row]

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=OFF;")
conn.execute("PRAGMA temp_store=MEMORY;")
conn.execute("PRAGMA cache_size=-200000;")  # 大記憶體快取

targets = ["RXNCONSO.RRF", "RXNREL.RRF", "RXNSAT.RRF", "RXNSTY.RRF"]
for fname in targets:
    fpath = rrf_dir / fname
    if not fpath.exists():
        continue
    table = fname.replace(".RRF", "")
    n = count_cols_of_first_line(fpath)
    ensure_table(conn, table, n)

    qmarks = ",".join(["?"]*n)
    sql = f"INSERT INTO {table} VALUES ({qmarks})"
    with conn:
        conn.executemany(sql, rows_generator(fpath))
    print(f"Imported {fname} -> {table}")

# 常用索引（可以加速查詢）
conn.executescript("""
CREATE INDEX IF NOT EXISTS idx_conso_rxcui ON RXNCONSO(RXCUI);
CREATE INDEX IF NOT EXISTS idx_conso_code  ON RXNCONSO(CODE);
CREATE INDEX IF NOT EXISTS idx_conso_tty   ON RXNCONSO(TTY);
CREATE INDEX IF NOT EXISTS idx_conso_sab   ON RXNCONSO(SAB);
CREATE INDEX IF NOT EXISTS idx_rel_rxcui1  ON RXNREL(RXCUI1);
CREATE INDEX IF NOT EXISTS idx_rel_rxcui2  ON RXNREL(RXCUI2);
CREATE INDEX IF NOT EXISTS idx_rel_rela    ON RXNREL(RELA);
CREATE INDEX IF NOT EXISTS idx_sat_rxcui   ON RXNSAT(RXCUI);
CREATE INDEX IF NOT EXISTS idx_sat_atn     ON RXNSAT(ATN);
""")
conn.close()
print("Done.")
