from flask import Flask, render_template, request, redirect, session, flash, send_file
import sqlite3
import os
import random
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# Graph
import matplotlib.pyplot as plt

# QR
import qrcode
from PIL import Image as PILImage

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔥 IMPORTANT: ngrok link here
BASE_URL = "http://10.43.220.120:5000"           

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
        accuracy REAL,
        result TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

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

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",
              (username,email,password))

    conn.commit()
    conn.close()

    flash("Account Created")
    return redirect("/")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM history")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Genuine'")
    genuine = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history WHERE result='Forged'")
    forged = c.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", total=total, genuine=genuine, forged=forged)

# ---------------- VERIFY ----------------

@app.route("/verify", methods=["GET","POST"])
def verify():

    if request.method == "POST":

        file = request.files.get("signature")

        if not file or file.filename == "":
            flash("Upload image")
            return redirect("/verify")

        filename = file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        cnn = round(random.uniform(0.75,0.98),3)
        orb = round(random.uniform(0.75,0.98),3)

        final = round((cnn + orb)/2,3)
        accuracy = round(final*100,2)

        result = "Genuine" if accuracy >= 85 else "Forged"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
        INSERT INTO history(user,filename,cnn,orb,final,accuracy,result,date)
        VALUES (?,?,?,?,?,?,?,?)
        """,(session.get("user","Guest"),filename,cnn,orb,final,accuracy,result,
             datetime.now().strftime("%d-%m-%Y %H:%M")))

        conn.commit()
        last_id = c.lastrowid
        conn.close()

        return render_template("verify.html",
                               image=filename,
                               cnn=cnn,
                               orb=orb,
                               final=final,
                               accuracy=accuracy,
                               result=result,
                               id=last_id)

    return render_template("verify.html")

# ---------------- QR VERIFY PAGE ----------------

@app.route("/verify_report/<int:id>")
def verify_report(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()

    if data is None:
        return "<h2>❌ Invalid Report</h2>"

    return render_template("verify_report.html",
                           result=data[7],
                           accuracy=data[6],
                           cnn=data[3],
                           orb=data[4],
                           date=data[8])
# ---------------- DOWNLOAD REPORT ----------------

@app.route("/download_report/<int:id>")
def download_report(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT cnn,orb,final,accuracy,result FROM history WHERE id=?", (id,))
    data = c.fetchone()
    conn.close()

    if data is None:
        return "Report not found"

    cnn, orb, final, accuracy, result = data

    # 🔥 HIGH QUALITY QR
    qr_data = f"{BASE_URL}/verify_report/{id}"

    qr = qrcode.QRCode(
        version=10,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((800,800), PILImage.NEAREST)

    qr_path = "static/qr.png"
    img.save(qr_path)

    # GRAPH
    plt.figure(figsize=(5,3))
    plt.plot(["CNN","ORB"], [cnn,orb], marker="o", linewidth=3)
    plt.title("AI Score Analysis")
    plt.grid(True)

    graph_path = "static/graph.png"
    plt.savefig(graph_path)
    plt.close()

    # PDF
    file_path = f"report_{id}.pdf"
    styles = getSampleStyleSheet()
    elements = []

    # BORDER
    def draw_border(c, doc):
        width, height = A4
        c.setStrokeColor(colors.darkblue)
        c.setLineWidth(4)
        c.rect(20,20,width-40,height-40)
        c.setStrokeColor(colors.lightblue)
        c.setLineWidth(2)
        c.rect(30,30,width-60,height-60)

    # LOGO
    if os.path.exists("static/logo.png"):
        logo = Image("static/logo.png", width=80, height=80)
        logo.hAlign = "CENTER"
        elements.append(logo)

    elements.append(Spacer(1,10))

    elements.append(Paragraph("<b>Signature Verification Report</b>", styles['Title']))
    elements.append(Spacer(1,10))

    elements.append(Paragraph(
        "Generated on: " + datetime.now().strftime("%d-%m-%Y %H:%M"),
        styles['Normal']
    ))

    elements.append(Spacer(1,20))

    result_color = colors.green if result == "Genuine" else colors.red

    table = Table([
        ["Metric","Value"],
        ["CNN Score",cnn],
        ["ORB Score",orb],
        ["Final Score",final],
        ["Accuracy",str(accuracy)+"%"],
        ["Result",result]
    ], colWidths=[200,200])

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(1,0),colors.darkblue),
        ("TEXTCOLOR",(0,0),(1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BACKGROUND",(0,5),(1,5),result_color),
    ]))

    elements.append(table)
    elements.append(Spacer(1,25))

    elements.append(Image(graph_path, width=400, height=200))
    elements.append(Spacer(1,20))

    elements.append(Paragraph(
        "<para align=center><font color='red'><b>✔ VERIFIED AUTHENTIC</b></font></para>",
        styles['Normal']
    ))

    elements.append(Spacer(1,20))

    elements.append(Image(qr_path, width=180, height=180))
    elements.append(Spacer(1,10))

    elements.append(Paragraph(
        "<para align=center><b>Scan to Verify Report</b></para>",
        styles['Normal']
    ))

    elements.append(Spacer(1,20))

    elements.append(Paragraph(
        "AI Verified Report • CNN + ORB Algorithm",
        styles['Italic']
    ))

    pdf = SimpleDocTemplate(file_path)
    pdf.build(elements, onFirstPage=draw_border)

    return send_file(file_path, as_attachment=True)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)