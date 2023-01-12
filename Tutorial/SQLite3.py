import sqlite3

# #Verify tables created:
# res = cur.execute("SELECT name FROM sqlite_master WHERE name='tutorial'")
# if (res.fetchone() is None):
#     con = sqlite3.connect("tutorial.db")

con = sqlite3.connect("tutorial.db")
cur = con.cursor()

cur.execute("CREATE TABLE if not exists movie(title, year, score)")
#cur.execute("DROP TABLE movie")

con.commit()

con.close()

###################################

con = sqlite3.connect("tutorial.db")
cur = con.cursor()

Name = "Nadir"

cur.execute("SELECT * FROM movie WHERE title=:c",{"c":Name})
data = cur.fetchall()

if (len(data)==0):
    cur.execute("INSERT INTO movie VALUES (?,?,?)",(Name, "2000", "9.5"))
else:
    print("Name already used")
# self.root.ids.inputID.text

con.commit()

con.close()

###################################


con = sqlite3.connect("tutorial.db")
cur = con.cursor()

cur.execute("DELETE FROM movie WHERE title=:c",{"c":"dANA"})

con.commit()

con.close()

###################################


con = sqlite3.connect("tutorial.db")
cur = con.cursor()

cur.execute("SELECT * FROM movie")
# cur.execute("SELECT * FROM movie WHERE title=:c",{"c":"Dragon"})

data = cur.fetchall()

print(data)

for elem in data:
    print(str(elem[0])+" "+str(elem[1])+" "+str(elem[2]))


con.commit()

con.close()







