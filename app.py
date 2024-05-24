from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date , timedelta
import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashTable import HashTable

load_dotenv()

'''
pip install flask
pip install apscheduler
pip install python-dotenv
'''

user_table = HashTable(100)
admin_table = HashTable(100)
house_table = HashTable(100)

sender_email = os.getenv("sender_email")
password = os.getenv("password")
to_email = os.getenv("to_email")

if sender_email is None or password is None or to_email is None:
    print("Error: One or more required environment variables are not set.")
    exit(1)

try:
    user_table.load_from_file("./static/data/user_table.json", 100)
    admin_table.load_from_file("./static/data/admin_table.json", 100)
    house_table.load_from_file("./static/data/house_table.json", 100)
except FileNotFoundError:
    print("Error: One or more JSON files not found.")
    exit(1)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config.update(
    SESSION_COOKIE_SECURE=True,  
    SESSION_COOKIE_HTTPONLY=True, 
    PERMANENT_SESSION_LIFETIME=timedelta(days=1), 
    SESSION_COOKIE_SAMESITE='Lax' 
)

fee_bhk=4000
fee_vehicles=100
fee_pets=100

def maintenance_fee_calculator(bhk,vehicles,pets):
    maintenance_fee=bhk*fee_bhk+vehicles*fee_vehicles+pets*fee_pets
    return maintenance_fee


def check_and_update_maintenance_fee():
    print("Maintenance fee update check triggered")
    today = date.today()
    
    if today.day == 24:
        print("Maintenance fee update condition met")
        
        for i, node in enumerate(user_table.table):   
            while node:    
                user_details = node.value["details"]
                flat_no = user_details["flat_no"]
                bhk = user_details["BHK"]
                vehicles = user_details["no_of_vehicles"]
                pets = user_details["no_of_pets"]
                resident=user_details["resident_name"]
                owner=user_details["owner_name"]

                if resident !="NA":
                    if resident==owner:
                        user_details["maintenance_fee"] = maintenance_fee_calculator(0,vehicles,pets)
                        user_details["payment_status"] = "Unpaid"

                    else:
                        user_details["maintenance_fee"] = maintenance_fee_calculator(bhk,vehicles,pets)
                        user_details["payment_status"] = "Unpaid"

                else:
                    user_details["maintenance_fee"] = 0
                    user_details["payment_status"] = "None"
                
                house_details = house_table.search(flat_no)
                if house_details:
                    house_details["maintenance_fee"] = house_details["BHK"]*fee_bhk
    
                node = node.next
        
        user_table.save_to_file('./static/data/user_table.json')
        house_table.save_to_file('./static/data/house_table.json')
        print("User and house tables saved to file")

check_and_update_maintenance_fee()

def send_mail(flat, name, email, subject, message):
    email_message = f"""
    <html>
      <body style="background-color:#222831; padding:20px; border-radius:10px; color:white;">
        <h1 style="font-size:18px;">Complaint Raised By: {name}</h1>
        <h1 style="font-size:18px;">Flat No: {flat}</h1>
        <h2 style="font-size:18px;">Complaint:</h2>
        <p style="font-size:16px;">{message}</p>
        <h2 style="font-size:18px;">Resident Email : {email}</h2>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    part = MIMEText(email_message, "html")
    msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, msg.as_string())

@app.route("/")
def homepage():
    return render_template("homePage.html")

@app.route("/login/<string:role>", methods=["GET", "POST"])
def login(role):
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if role == "admin":
            data = admin_table.search(username)
            
            if data is None:
                error = "Wrong Credentials. Try Again !!"
                return render_template("login.html", role=role, error=error)
            
            if data['password'] == password:
                session["admin_logged_in"] = True
                return redirect(url_for("admin"))
            else:
                error = "Wrong Credentials. Try Again !!"
                return render_template("login.html", role=role, error=error)
                
        elif role == "resident":
            data = user_table.search(username)

            if data is None:
                error = "Wrong Credentials. Try Again !!"
                return render_template("login.html", role=role, error=error)
            
            if data['password'] == password:
                session["logged_in"] = True
                return redirect(url_for("resident", user=username))
            
            else:
                error = "Wrong Credentials. Try Again !!"
                return render_template("login.html", role=role, error=error)
                
    return render_template("login.html", role=role)

@app.route("/resident")
def resident():
    if not session.get("logged_in"):
        return redirect(url_for('login', role="resident"))

    user_args = request.args.get("user")
    user_details = user_table.search(user_args)
    user = user_details["details"]

    users = []
    for node in user_table.table:
        while node is not None:
            if user_args != node.key:
                users.append({"username": node.key, "details": node.value["details"]})
            node = node.next  
    session.clear()
    return render_template("resident.html", user=user, users=users)

@app.route("/admin")
def admin():
    if not(session.get("admin_logged_in")):
        return redirect(url_for("login", role="admin"))
    
    users = []
    for node in user_table.table:
        while node is not None:
            users.append({"username": node.key, "details": node.value["details"]})
            node = node.next 

    return render_template("admin.html", users=users)

@app.route("/admin/edit/<string:username>", methods=["GET", "POST"])
def edit_user(username):
    if not session.get("admin_logged_in"):
        return redirect(url_for('login', role="admin"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "edit":
            user_details = user_table.search(username)
            house_details=house_table.search(username)
            password = request.form.get("password")
            new_owner = request.form.get("owner_name")
            new_owner_contact = request.form.get("owner_contact")
            new_resident = request.form.get("resident_name") or "NA"
            new_resident_contact = request.form.get("resident_contact") 
            new_email_address = request.form.get("email_address")
            new_residents = int(request.form.get("residents")) or 0
            new_vehicles = int(request.form.get("vehicles")) or 0
            new_pets =int(request.form.get("pets")) or 0
            payment_status = request.form.get("payment_status")
            bhk=int(request.form.get("bhk"))

            print(new_vehicles,bhk,new_pets)

            if new_resident!="NA":  
                house_status="Unavailable"
                if new_owner == new_resident:
                    new_payment = "None"
                    maintenance_fee=maintenance_fee_calculator(0,new_vehicles,new_pets)
                else:
                    new_payment = "Unpaid" if payment_status != "on" else "Paid"
                    maintenance_fee=maintenance_fee_calculator(bhk,new_vehicles,new_pets)
            else:  
                new_payment = "None"

            details = {
                "flat_no": username,
                "resident_name": new_resident,
                "resident_number": new_resident_contact,
                "email_address": new_email_address,
                "owner_name": new_owner,
                "owner_number": new_owner_contact,
                "status": "Unavailable",
                "no_of_residents":new_residents,
                "no_of_vehicles":new_vehicles,
                "no_of_pets":new_pets,
                "BHK": bhk,
                "maintenance_fee":maintenance_fee , 
                "payment_status": new_payment
            }

            house_details["status"]=house_status
            user_details["details"] = details
            user_details["password"] = password

        elif action=="remove":
            user_details=user_table.search(username)
            flat_no = user_details["details"]["flat_no"]
            details={"flat_no":user_details["details"]["flat_no"],"resident_name": "NA","resident_number":"NA","email_address":"NA" ,"owner_name":user_details["details"]["owner_name"], "owner_number":user_details["details"]["owner_number"],"status":"Available", "no_of_residents": 0, "no_of_vehicles":0, "no_of_pets":0,"BHK":user_details["details"]["BHK"], "maintenance_fee": 0,"payment_status": "None" }
            user_details["details"]=details
            house_table.search(flat_no)['status'] = 'Available'
            return redirect(url_for("admin"))
        
        user_table.save_to_file('./static/data/user_table.json')
        house_table.save_to_file('./static/data/house_table.json')

        return redirect(url_for("admin"))

    user_details = user_table.search(username)
    return render_template("edit_user.html", username=username, user_details=user_details)


@app.route("/admin/add", methods=["GET", "POST"])
def add_flats():
    if not session.get("admin_logged_in"):
        return redirect(url_for('login', role="admin"))

    if request.method == "POST":
        password = request.form.get("password")
        flat_no = request.form.get("flat_no")
        owner_name = request.form.get("owner_name")
        owner_contact = request.form.get("owner_contact")
        BHK = int(request.form.get("bhk"))
        maintenance_fee=fee_bhk*BHK


        details = {
            "flat_no": flat_no,
            "resident_name": "NA",
            "resident_number": "NA",
            "email_address": "NA",
            "owner_name": owner_name,
            "owner_number": owner_contact,
            "status": "Unavailable",
            "no_of_residents":0,
            "no_of_vehicles": 0,
            "no_of_pets": 0,
            "BHK": BHK,
            "maintenance_fee": maintenance_fee,
            "payment_status": "None"
        }

        user_table.insert(flat_no, {"details": details, "password": password})
        house_table.insert(flat_no, {"status": "Available", "maintenance_fee": maintenance_fee, "BHK": BHK})
        user_table.save_to_file('./static/data/user_table.json')
        house_table.save_to_file('./static/data/house_table.json')

        return redirect(url_for("admin"))

    return render_template("add_flats.html")

@app.route("/guest")
def guest():
    house_status = {}
    for node in house_table.table:
        if node:
            house_status[node.key] = node.value
    return render_template("guest.html", house_status=house_status)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("homepage"))

@app.route("/complaint/<string:username>", methods=["GET", "POST"])
def complaint(username):
    if request.method == "POST":
        flat = username
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")
        send_mail(flat, name, email, subject, message)
        return redirect(url_for("homepage"))
    
    user_details = user_table.search(username)
    user = user_details["details"]
    return render_template("complaint.html", user=user)

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_update_maintenance_fee, 'interval', days=1)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
