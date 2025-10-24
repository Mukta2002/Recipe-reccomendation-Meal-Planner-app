# database_setup/add_dates.py
import os
import mysql.connector

# read simple creds file if present
if os.path.isfile('../credentials.txt'):
    with open("../credentials.txt", "r") as reader:
        u, p = [line.strip() for line in reader.readlines()]
else:
    u = input("Enter database user: ")
    p = input("Enter database password: ")

cnx = mysql.connector.connect(
    host="127.0.0.1",
    port=3308,                 # <- match your config.py port
    user=u,
    password=p,
    database="meals"           # <- match your config.py database
)

cur = cnx.cursor()

# get meal names
cur.execute("SELECT Name FROM MealsTable;")
meals = [r[0] for r in cur.fetchall()]

# set a date on each
sql = "UPDATE MealsTable SET Last_Made = %s WHERE Name = %s"
for name in meals:
    cur.execute(sql, ("2021-04-23", name))

cnx.commit()
cur.close()
cnx.close()
print("✔ Last_Made backfilled.")
