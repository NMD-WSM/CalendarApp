import pymysql
from dbutils.pooled_db import PooledDB
from pymysql import cursors
import configparser


config = configparser.ConfigParser()
config.read('config.ini')
db_host = config.get('database', 'host')
db_port_str = config.get('database', 'port')
db_port = int(db_port_str)
db_user = config.get('database', 'user')
db_passwd = config.get('database', 'passwd')

POOL = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    blocking=True,
    setsession=[],
    ping=0,

    host=db_host, port=db_port, user=db_user, passwd=db_passwd, charset='utf8', db='calendarapp'
)


def fetch_one(sql, params):
    conn = POOL.connection()
    cursor = conn.cursor(cursor=cursors.DictCursor)
    cursor.execute(sql, params)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def fetch_all(sql, params):
    conn = POOL.connection()
    cursor = conn.cursor(cursor=cursors.DictCursor)
    cursor.execute(sql, params)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def insert(sql, params):
    conn = POOL.connection()
    cursor = conn.cursor(cursor=cursors.DictCursor)
    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()


def update(sql, params):
    conn = POOL.connection()
    cursor = conn.cursor(cursor=cursors.DictCursor)
    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()
