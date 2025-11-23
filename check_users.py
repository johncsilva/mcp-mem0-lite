#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import sys

conn = sqlite3.connect('mem0.db')
cur = conn.cursor()

# Check tables
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cur.fetchall()
print(f'Tables: {tables}')

# Check memories by user_id
cur.execute('SELECT user_id, COUNT(*) FROM memories GROUP BY user_id')
print('\nMemorias por user_id:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} memorias')

# List all user_ids
cur.execute('SELECT DISTINCT user_id FROM memories')
print('\nTodos os user_ids:')
for row in cur.fetchall():
    print(f'  - {row[0]}')

conn.close()
