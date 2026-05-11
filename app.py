from flask import Flask, render_template, request, redirect, session
import sqlite3
import cv2
import qrcode
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE INIT ----------------
 
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll_no TEXT,
            phone TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT
        )
    ''')

    # Attendance table
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll_no TEXT,
        date TEXT,
        time TEXT,
        status TEXT
    )
''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_no TEXT,
            route TEXT,
            location TEXT,
            status TEXT
        )
    ''')
    
    # Feedback table
    c.execute('''  
       CREATE TABLE IF NOT EXISTS feedback (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT,
           message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if email == "nachi@gmail.com" and password == "1234":
            session["user"] = email
            return redirect("/dashboard")

        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM logs")
    logs = c.fetchall()

    conn.close()

    return render_template("dashboard.html", logs=logs)


# ---------------- MANAGE PASS ----------------
@app.route("/manage_pass")
def manage_pass():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM students")
    students = c.fetchall()

    conn.close()

    return render_template("manage.html", students=students)

# ---------------- SEARCH STUDENT ----------------
@app.route("/search", methods=["GET", "POST"])
def search():

    student = None

    if request.method == "POST":

        roll_no = request.form["roll_no"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))

        student = c.fetchone()

        conn.close()

    return render_template("search.html", student=student)


# ---------------- ADD PASS ----------------
@app.route("/add_pass", methods=["GET", "POST"])
def add_pass():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll_no"]
        phone = request.form["phone"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO students (name, roll_no, phone) VALUES (?, ?, ?)",
                  (name, roll, phone))

        conn.commit()
        conn.close()

        student_data = f"{name} | {roll} | {phone}"

        qr = qrcode.make(student_data)
        os.makedirs("static/qrcodes", exist_ok=True)

        qr_path = f"static/qrcodes/{roll}.png"

        qr.save(qr_path)

        return redirect("/manage_pass")

    return render_template("add.html")


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM students WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/manage_pass")

# ---------------- UPDATE STUDENT ----------------
@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # FORM SUBMIT
    if request.method == "POST":

        name = request.form["name"]
        roll_no = request.form["roll_no"]
        phone = request.form["phone"]

        c.execute("""
            UPDATE students
            SET name=?, roll_no=?, phone=?
            WHERE id=?
        """, (name, roll_no, phone, id))

        conn.commit()
        conn.close()

        return redirect("/manage_pass")

    # OLD DATA FETCH
    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()

    conn.close()

    return render_template("update.html", student=student)


# ---------------- SCAN PAGE ----------------
@app.route("/scan")
def scan():
    if "user" not in session:
        return redirect("/login")
    return render_template("scan.html")

@app.route("/start_scan")
def start_scan():
    qr_data = start_qr_scanner()

    if qr_data:
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        now = datetime.now()
        today = now.strftime("%d-%m-%Y")
        current_time = now.strftime("%H:%M:%S")

        # Logs save
        c.execute(
            "INSERT INTO logs (name, time) VALUES (?, ?)",
            (qr_data, now.strftime("%d-%m-%Y %H:%M:%S"))
        )

        # Attendance save
        c.execute(
            "INSERT INTO attendance (name, roll_no, date, time, status) VALUES (?, ?, ?, ?, ?)",
            (qr_data, qr_data, today, current_time, "Present")
        )

        conn.commit()
        conn.close()

    return redirect("/dashboard")


# ---------------- FACE DETECTION ----------------

def start_qr_scanner():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data, bbox, _ = detector.detectAndDecode(frame)

        if data:
            cap.release()
            cv2.destroyAllWindows()
            return data

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None
def start_camera():
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow("Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


@app.route("/face")
def face():
    start_camera()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO logs (name, time) VALUES (?, ?)",
              ("Face Detected", "Now"))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

 # ---------------- BUS TRACKING ----------------
@app.route("/bus_tracking", methods=["GET", "POST"])
def bus_tracking():

    if request.method == "POST":

        bus_no = request.form["bus_no"]
        route = request.form["route"]
        location = request.form["location"]
        status = request.form["status"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO buses (bus_no, route, location, status) VALUES (?, ?, ?, ?)",
            (bus_no, route, location, status)
        )

        conn.commit()
        conn.close()

        return redirect("/bus_tracking")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM buses")
    buses = c.fetchall()

    conn.close()

    return render_template("bus_tracking.html", buses=buses)

# ---------------- FEEDBACK ----------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():

    if request.method == "POST":

        name = request.form["name"]
        message = request.form["message"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO feedback (name, message) VALUES (?, ?)",
            (name, message)
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("feedback.html")

@app.route("/view_feedback")
def view_feedback():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM feedback")
    feedbacks = c.fetchall()

    conn.close()

    return render_template("view_feedback.html", feedbacks=feedbacks)

@app.route("/attendance")
def attendance():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM attendance")
    records = c.fetchall()

    conn.close()

    return render_template("attendance.html", records=records)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)