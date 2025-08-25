import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

DATABASE_URL = os.getenv('DATABASE_URL')


def get_conn():
    return psycopg2.connect(DATABASE_URL)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not validators.url(url) or len(url) > 255:
            flash("Некорректный URL", "danger")
            return render_template("main_content.html")
        parsed = urlparse(url)
        normalized_url = f"{parsed.scheme}://{parsed.netloc}"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM urls WHERE name=%s",
                    (normalized_url,)
                    )
                row = cur.fetchone()
                if row:
                    flash("Страница уже существует", "info")
                    return redirect(url_for("url_show", id=row[0]))
                cur.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) "
                    "RETURNING id",
                    (normalized_url, datetime.now())
                )
                new_id = cur.fetchone()[0]
                flash("Страница успешно добавлена", "success")
                return redirect(url_for("url_show", id=new_id))
    return render_template("main_content.html")


@app.route("/urls")
def urls():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls ORDER BY id DESC"
                )
            urls = cur.fetchall()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def url_show(id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls WHERE id=%s", (id,)
                )
            url = cur.fetchone()
    if not url:
        flash("Страница не найдена", "danger")
        return redirect(url_for("urls"))
    return render_template("url.html", url=url)