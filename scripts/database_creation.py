import os

import pandas as pd
import sqlite3

conn = sqlite3.connect('../flask_app/database.db')

for f in os.listdir('../data'):
    if f.endswith('.csv'):
        try:
            pd.read_csv('../data/' + f).to_sql(f[:f.find('.csv')], con=conn, if_exists='replace')
            os.remove('../data/' + f)
        except FileNotFoundError:
            pass

conn.commit()
conn.close()
