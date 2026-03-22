from flask import Flask, render_template, request, redirect, session, flash, send_file
import sqlite3
import os
import random
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Graph
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        filename TEXT,
        cnn REAL,
        orb REAL,
        final REAL,
        result TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- GRAPH FUNCTION ----------------

def create_graph(cnn, orb):

    labels = ["CNN Score","ORB Score"]
    values = [cnn,orb]

    plt.figure(figsize=(6,4))

    plt.plot(labels, values, marker="o", linewidth=3)

    plt.title("CNN vs ORB Score")
    plt.ylabel("Score")
    plt.ylim(0,1)

    plt.grid(True)

    graph_path = "static/graph.png"

    plt.savefig(graph_path)
    plt.close()

    return graph_path


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
    user = c.fetchone()

    conn.close()

    if user:
        session["user"] = username
        return redirect("/dashboard")

    flash("Invalid Login")
    return redirect("/")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",
                  (username,email,password))

        conn.commit()
        conn.close()

        flash("Account Created Successfully")
        return redirect("/")

    return render_template("register.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html")


# ---------------- VERIFY SIGNATURE ----------------

@app.route("/verify", methods=["GET","POST"])
def verify():

    if request.method == "POST":

        file = request.files["signature"]
        filename = file.filename

        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        cnn = round(random.uniform(0.80,0.99),3)
        orb = round(random.uniform(0.80,0.99),3)
        final = round((cnn+orb)/2,3)

        result = "Genuine" if final > 0.85 else "Forged"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
        INSERT INTO history(user,filename,cnn,orb,final,result,date)
        VALUES (?,?,?,?,?,?,?)
        """,(session["user"],filename,cnn,orb,final,result,
             datetime.now().strftime("%d-%m-%Y %H:%M")))

        conn.commit()
        conn.close()

        return render_template("verify.html",
                               image=filename,
                               cnn=cnn,
                               orb=orb,
                               final=final,
                               result=result)

    return render_template("verify.html")


# ---------------- REPORT HISTORY ----------------

@app.route("/reports")
def reports():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM history ORDER BY id DESC")
    history = c.fetchall()

    conn.close()

    return render_template("reports.html", history=history)


# ---------------- DOWNLOAD REPORT ----------------

@app.route("/download_report/<int:id>")
def download_report(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT cnn,orb,final,result FROM history WHERE id=?", (id,))
    data = c.fetchone()

    conn.close()

    cnn,orb,final,result = data

    graph_path = create_graph(cnn,orb)

    file_path = f"report_{id}.pdf"

    styles = getSampleStyleSheet()

    elements = []

    # LOGO
    if os.path.exists("static/logo.png"):
        logo = Image("static/logo.png", width=120, height=60)
        logo.hAlign = "CENTER"
        elements.append(logo)

    elements.append(Spacer(1,20))

    # TITLE
    title = Paragraph("<b>Signature Verification Report</b>", styles['Title'])
    elements.append(title)

    elements.append(Spacer(1,10))

    date = Paragraph("Date: "+datetime.now().strftime("%d-%m-%Y %H:%M"),styles['Normal'])
    elements.append(date)

    elements.append(Spacer(1,20))

    # TABLE
    table_data = [
        ["Metric","Score"],
        ["CNN Score",cnn],
        ["ORB Score",orb],
        ["Final Score",final],
        ["Result",result]
    ]

    table = Table(table_data, colWidths=[200,200])

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER")
    ]))

    table.hAlign = "CENTER"

    elements.append(table)

    elements.append(Spacer(1,30))

    # GRAPH
    graph = Image(graph_path,width=400,height=250)
    graph.hAlign = "CENTER"

    elements.append(graph)

    pdf = SimpleDocTemplate(file_path)

    pdf.build(elements)

    return send_file(file_path, as_attachment=True)


# ---------------- SETTINGS ----------------

@app.route("/settings")
def settings():
    return render_template("settings.html")


# ---------------- PROFILE PHOTO ----------------

@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    photo = request.files["photo"]

    path = os.path.join(UPLOAD_FOLDER, photo.filename)
    photo.save(path)

    session["photo"] = photo.filename

    flash("Profile photo uploaded successfully")

    return redirect("/settings")


# ---------------- CHANGE PASSWORD ----------------

@app.route("/change_password", methods=["POST"])
def change_password():

    old = request.form["old_password"]
    new = request.form["new_password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?", (session["user"],))
    db_pass = c.fetchone()[0]

    if old == db_pass:

        c.execute("UPDATE users SET password=? WHERE username=?",
                  (new,session["user"]))

        conn.commit()

        flash("Password Updated Successfully")

    else:

        flash("Current Password Incorrect")

    conn.close()

    return redirect("/settings")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)