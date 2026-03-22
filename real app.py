from flask import Flask, request, render_template, redirect, flash, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# DATABASE CREATE
# -----------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/settings")
    return render_template("login.html")


# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not all([username,email,password]):
            flash("All fields required!", "error")
            return redirect(url_for("register"))

        try:
            # DB insert
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username,email,password) VALUES (?, ?, ?)",
                      (username,email,generate_password_hash(password,'sha256')))
            conn.commit()
            conn.close()
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or Email already exists!", "error")
            return redirect(url_for("register"))

    return render_template("register.html")
# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username,password))

    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = username
        flash("✅ Login successful", "success")
        return redirect("/settings")

    else:
        flash("❌ Invalid login", "danger")
        return redirect("/")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect("/")


# -----------------------------
# SETTINGS PAGE
# -----------------------------
@app.route("/settings")
def settings():

    if "user" not in session:
        return redirect("/")

    return render_template("settings.html")


# -----------------------------
# UPDATE PROFILE
# -----------------------------
@app.route("/update_profile", methods=["POST"])
def update_profile():

    if "user" not in session:
        return redirect("/")

    new_username = request.form["username"]
    email = request.form["email"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?", (new_username,))
    user = c.fetchone()

    if user and new_username != session["user"]:
        flash("⚠ Username already exists", "danger")
        conn.close()
        return redirect("/settings")

    try:
        c.execute("""
        UPDATE users
        SET username=?, email=?
        WHERE username=?
        """,(new_username,email,session["user"]))

        conn.commit()
        session["user"] = new_username

        flash("✅ Profile updated", "success")

    except sqlite3.IntegrityError:
        flash("❌ Database error", "danger")

    conn.close()

    return redirect("/settings")


# -----------------------------
# UPLOAD PROFILE PHOTO
# -----------------------------
@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    if "photo" not in request.files:
        flash("No file selected", "danger")
        return redirect("/settings")

    photo = request.files["photo"]

    if photo.filename == "":
        flash("Choose a file", "warning")
        return redirect("/settings")

    path = os.path.join(UPLOAD_FOLDER, photo.filename)
    photo.save(path)

    session["photo"] = photo.filename

    flash("📸 Profile photo uploaded", "success")

    return redirect("/settings")


# -----------------------------
# CHANGE PASSWORD
# -----------------------------
@app.route("/change_password", methods=["POST"])
def change_password():

    old = request.form["old_password"]
    new = request.form["new_password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?",
              (session["user"],))

    data = c.fetchone()

    if data[0] != old:
        flash("❌ Incorrect current password", "danger")
        return redirect("/settings")

    c.execute("UPDATE users SET password=? WHERE username=?",
              (new,session["user"]))

    conn.commit()
    conn.close()

    flash("🔒 Password updated", "success")

    return redirect("/settings")


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)