import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
import validators
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

DATABASE_URL = os.getenv('DATABASE_URL')


def get_conn():
    return psycopg2.connect(DATABASE_URL)


@app.route("/", methods=["GET"])
def index():
    return render_template("main_content.html")


@app.route("/urls", methods=["POST"])
def add_url():
    url = request.form.get("url", "").strip()
    if not validators.url(url) or len(url) > 255:
        flash("Некорректный URL", "danger")
        return redirect(url_for("urls"))
    parsed = urlparse(url)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name=%s", (normalized_url,))
            row = cur.fetchone()
            if row:
                flash("Страница уже существует", "info")
                return redirect(url_for("show_url", id=row[0]))
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            new_id = cur.fetchone()[0]
            flash("Страница успешно добавлена", "success")
            return redirect(url_for("show_url", id=new_id))


@app.route('/urls')
def urls():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT
            urls.id,
            urls.name,
            MAX(url_checks.created_at) AS last_check,
            MAX(url_checks.status_code) AS status_code
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        GROUP BY urls.id, urls.name
        ORDER BY urls.id DESC
        '''
    )
    urls = [
        {
            'id': row[0],
            'name': row[1],
            'last_check': row[2],
            'status_code': row[3]
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, name, created_at FROM urls WHERE id = %s',
        (id,)
    )
    url_row = cur.fetchone()
    url = {
        'id': url_row[0],
        'name': url_row[1],
        'created_at': url_row[2]
    } if url_row else None

    cur.execute(
        '''
        SELECT
            id,
            url_id,
            status_code,
            h1,
            title,
            description,
            created_at
        FROM url_checks
        WHERE url_id = %s
        ORDER BY id DESC
        ''',
        (id,)
    )
    checks = [
        {
            'id': row[0],
            'url_id': row[1],
            'status_code': row[2],
            'h1': row[3],
            'title': row[4],
            'description': row[5],
            'created_at': row[6]
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('SELECT name FROM urls WHERE id=%s', (id,))
        row = cur.fetchone()
        if not row:
            flash('Сайт не найден', 'danger')
            return redirect(url_for('urls'))
        url = row[0]

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')

        h1_tag = soup.h1
        h1 = h1_tag.get_text(strip=True) if h1_tag else None

        title_tag = soup.title
        title = title_tag.get_text(strip=True) if title_tag else None

        description = None
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            description = desc_tag['content'].strip()

        created_at = datetime.now()
        cur.execute(
            '''
            INSERT INTO url_checks (
                url_id,
                status_code,
                h1,
                title,
                description,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ''',
            (id, status_code, h1, title, description, created_at)
        )
        conn.commit()
        flash('Страница успешно проверена', 'success')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('show_url', id=id))