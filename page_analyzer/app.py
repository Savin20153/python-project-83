import os

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from page_analyzer.data_base import (
    add_check,
    add_url,
    get_all_urls,
    get_checks_by_url,
    get_url_by_id,
    get_url_by_name,
)
from page_analyzer.parser import parse_html
from page_analyzer.url_validator import normalize_url, validate_url

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # NOSONAR


@app.route("/", methods=["GET"])
def index():
    return render_template("main_content.html")


@app.route("/urls", methods=["POST"])
def add_new_url():
    url = request.form.get("url", "").strip()
    if not validate_url(url):
        flash("Некорректный URL", "danger")
        return render_template("main_content.html"), 422

    normalized_url = normalize_url(url)
    existing = get_url_by_name(normalized_url)

    if existing:
        flash("Страница уже существует", "info")
        return redirect(url_for("show_url", id=existing[0]))

    new_id = add_url(normalized_url)
    flash("Страница успешно добавлена", "success")
    return redirect(url_for("show_url", id=new_id))


@app.route("/urls")
def urls():
    urls = get_all_urls()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    url_row = get_url_by_id(id)
    if not url_row:
        flash("Сайт не найден", "danger")
        return redirect(url_for("urls"))

    url = {
        "id": url_row[0],
        "name": url_row[1],
        "created_at": url_row[2],
    }
    checks = get_checks_by_url(id)

    return render_template("url.html", url=url, checks=checks)


@app.route("/urls/<int:id>/checks", methods=["POST"])
def url_checks(id):
    url_row = get_url_by_id(id)
    if not url_row:
        flash("Сайт не найден", "danger")
        return redirect(url_for("urls"))

    url = url_row[1]

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        status_code = response.status_code
        h1, title, description = parse_html(response.text)
        add_check(id, status_code, h1, title, description)
        flash("Страница успешно проверена", "success")

    except requests.RequestException:
        flash("Произошла ошибка при проверке", "danger")

    return redirect(url_for("show_url", id=id))
