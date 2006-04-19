import anydbm

db = anydbm.open("from.db", "c")
for k in db:
    print(k)
    print(db[k])
