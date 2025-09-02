import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


def add_url(name):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
            (name, datetime.now())
        )
        return cur.fetchone()["id"]


def get_url_by_name(name):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM urls WHERE name=%s", (name,))
        return cur.fetchone()  


def get_url_by_id(url_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, created_at
            FROM urls
            WHERE id = %s
            """,
            (url_id,)
        )
        return cur.fetchone()


def get_all_urls():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            SELECT urls.id, urls.name,
                   MAX(url_checks.created_at) AS last_check,
                   MAX(url_checks.status_code) AS status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            GROUP BY urls.id, urls.name
            ORDER BY urls.id DESC
            '''
        )
        return cur.fetchall()  


def add_check(url_id, status_code, h1, title, description):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO url_checks (
                url_id, status_code, h1, title, description, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ''',
            (url_id, status_code, h1, title, description, datetime.now())
        )


def get_checks_by_url(url_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            SELECT id, url_id, status_code, h1, title, description, created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY id DESC
            ''',
            (url_id,)
        )
        return cur.fetchall()
