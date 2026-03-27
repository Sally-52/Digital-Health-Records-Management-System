from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        user="root",
        password="", 
        database="CuraTrack", # Corrected name with Capitals
        unix_socket="/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock"
    )
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # FAIL-SAFE: This lets you in if you use these credentials
        # You can change 'admin' to whatever you like
        if username == 'admin' and password == 'password123':
            return redirect(url_for('dashboard'))
        
        # DATABASE CHECK (Optional but good to have)
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close(); conn.close()

        if user:
            return redirect(url_for('dashboard'))
        else:
            # If it fails, it just reloads. 
            # For the demo, just use the fail-safe credentials above!
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')

@app.route('/')
def dashboard():
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as c FROM patients"); p = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM appointments"); a = cursor.fetchone()['c']
    cursor.close(); conn.close()
    return render_template('admin_dashboard.html', p_count=p, a_count=a)

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute("INSERT INTO patients (name, dob, gender, contact) VALUES (%s, %s, %s, %s)",
                       (request.form['name'], request.form['dob'], request.form['gender'], request.form['contact']))
        conn.commit()
    cursor.execute("SELECT * FROM patients")
    pts = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('patients.html', patients=pts)

@app.route('/view-records/<int:p_id>')
def view_records(p_id):
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (p_id,))
    pt = cursor.fetchone()
    cursor.execute("SELECT * FROM appointments WHERE patient_id = %s ORDER BY date DESC", (p_id,))
    appts = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('patient_records.html', patient=pt, appointments=appts)

@app.route('/manage-users')
def manage_users():
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    # This pulls everyone from your users table
    cursor.execute("SELECT id, username, role FROM users")
    all_users = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('manage_users.html', users=all_users)

@app.route('/add-visit', methods=['POST'])
def add_visit():
    p_id = request.form.get('p_id')
    date = request.form.get('date')
    reason = request.form.get('reason')
    meds = request.form.get('medication')
    
    # Merging medication into the reason string for a quick presentation-ready fix
    full_note = f"{reason} | RX: {meds}"
    
    conn = get_db()
    cursor = conn.cursor()
    # Ensure your table columns match: patient_id, date, reason
    cursor.execute("INSERT INTO appointments (patient_id, date, reason) VALUES (%s, %s, %s)", 
                   (p_id, date, full_note))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_records', p_id=p_id))

@app.route('/logout')
def logout():
    return redirect(url_for('login')) # This now points to 'def login():'

if __name__ == '__main__':
    app.run(debug=True)