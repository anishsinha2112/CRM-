from flask import Flask, render_template, request, redirect, session, send_file, flash
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB = "crm.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                follow_up_date TEXT,
                follow_up_time TEXT,
                remark TEXT
            )
        """)
        conn.commit()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session["username"] = username
                return redirect("/dashboard")
            else:
                flash("Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash("Registration successful. Please log in.")
                return redirect("/")
            except:
                flash("Username already exists.")
    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect("/")
    if request.method == "POST":
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO customers 
                (name, email, phone, company, follow_up_date, follow_up_time, remark) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                    request.form["name"],
                    request.form["email"],
                    request.form["phone"],
                    request.form["company"],
                    request.form["follow_up_date"],
                    request.form["follow_up_time"],
                    request.form["remark"]
                ))
            conn.commit()
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)
    return render_template("dashboard.html", customers=df.to_dict(orient="records"))

@app.route("/export/<fmt>")
def export(fmt):
    if fmt not in ["csv", "excel"]:
        return "Invalid format"
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query("SELECT * FROM customers", conn)
    file_path = f"/mnt/data/customers_export.{ 'xlsx' if fmt == 'excel' else 'csv' }"
    if fmt == "excel":
        df.to_excel(file_path, index=False)
    else:
        df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
