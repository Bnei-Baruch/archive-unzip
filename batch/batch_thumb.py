import psycopg2
import os
import requests


DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')


conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, password=DB_PASS)
cur = conn.cursor()
cur.execute("""select uid from content_units limit 30;""")
rows = cur.fetchall()


counter_created = 0
counter_failed = 0
counter_main = 0

for row in rows:
    a = requests.get('http://127.0.0.1:5000/thumbnail/{}'.format(row[0]))
    print("{}. creating thumbnail from unit {} gor response {}".format(counter_main, row[0],a.status_code))
    counter_main += 1
    if a.status_code == 200:
        counter_created += 1
    else:
        counter_failed += 1

print("created {} thumbnails".format(counter_created))
print("failed  {} thumbnails".format(counter_failed))
    # try:
    #     logger.info("creating thumbnail for unit: {}".format(row[0]))
    #     get('http://127.0.0.1:5000/thumbnail/{}'.format(row[0]))
    # except:
    #     logger.info("could not fetch file uid for unit: {}".format(row[0]))

