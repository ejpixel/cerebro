import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy as sql
import hashlib
from helpers import *
import json
from sapixel import *

app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]


app.config["SESSION_COOKIE_SECURE"] = True


try:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]

except KeyError:
    raise ValueError("É necessário definir variável de ambiente DATABASE_URI com a chave de acesso do banco de dados.")

db = sql(app)
start_db(db)


@app.before_request
def before_request():
    if not request.is_secure():
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.route("/access", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        name = request.form["name"]
        hash_result = hashlib.sha256(request.form["key"].encode()).hexdigest()
        result = db.engine.execute("SELECT name, permissions FROM users INNER JOIN roles ON users.role_id=roles.id WHERE name = %s AND password = %s", name, hash_result).first()
        if result:
            session["user_id"] = result[0]
            session["roles"] = result[1]
            return redirect("/")
        else:
            flash("Username or password incorrect")
    return render_template("access.html")

@app.route("/")
@login_required
@admin_role
def index():
    contracts = db.engine.execute("SELECT COUNT(*) FROM services WHERE services.removed=false").first()[0]
    no_payments_contracts = db.engine.execute("SELECT COUNT(*) FROM services WHERE first_payment is null AND services.removed=false").first()[0]
    no_accepted_contracts = db.engine.execute("SELECT COUNT(*) FROM services WHERE acceptance_date is null AND services.removed=false").first()[0]
    clients = db.engine.execute("SELECT COUNT(*) FROM clients").first()[0]
    return render_template("index.html", contracts=contracts, no_payments_contracts=no_payments_contracts, no_accepted_contracts=no_accepted_contracts, clients=clients)

@app.route("/logout")
@login_required
def logout():
    session["user_id"] = None
    session["roles"] = None
    return redirect("/")

@app.route("/contracts_manager")
@login_required
@admin_role
def contracts_manager():
    raw_contracts = db.engine.execute("SELECT services.id, username, type, days_to_finish, total_price, payment_price, services.payment, description, contract_generation_date, acceptance_date, first_payment, client_id, count(payments.service_id) FROM services LEFT JOIN payments ON services.id=payments.service_id WHERE services.removed=false group by services.id order by services.id")
    contracts = []
    for contract in raw_contracts:
        short_description = contract[7]["short_description"]
        service_list = ", ".join(contract[7]["service_list"])
        contracts.append(list(contract[:7]) + [short_description, service_list] + list(contract[8:]))
    return render_template("contracts_manager.html", contracts=contracts)

@app.route("/clients_manager")
@login_required
@admin_role
def clients_manager():
    clients = db.engine.execute("SELECT * FROM clients ORDER BY id")
    return render_template("clients_manager.html", clients=list(clients))

@app.route("/access_manager")
@login_required
@admin_role
def access_manager():
    raw_accounts = db.engine.execute("SELECT name, role_id, permissions FROM users INNER JOIN roles on role_id=roles.id")
    accounts = [[name, role, " ".join(permissions)] for name, role, permissions in raw_accounts]
    roles = db.engine.execute("SELECT * FROM roles")
    return render_template("access_manager.html", accounts=list(accounts), roles=list(roles))

@app.route("/ata_manager")
@login_required
@admin_role
def ata_manager():
    atas = db.engine.execute("SELECT * FROM ej ORDER BY ata_date")
    return render_template("ata_manager.html", atas=list(atas))

@app.route("/access_creation", methods=["POST"])
@login_required
@admin_role
def access_creation():
    name = request.form['username']
    hash = hashlib.sha256(request.form['password'].encode()).hexdigest()
    role_id = request.form['role']
    db.engine.execute("INSERT INTO users(name, password, role_id) VALUES(%(name)s, %(hash)s, %(role)s)", name=name, hash=hash, role=role_id)
    return redirect(url_for("access_manager"))

@app.route("/role_creation", methods=["POST"])
@login_required
@admin_role
def role_creation():
    permissions = normalize_array(request.form['permissions'])
    db.engine.execute("INSERT INTO roles(permissions) VALUES(%(p)s)", p=permissions)
    return redirect(url_for("access_manager"))

@app.route("/edit_accounts", methods=["POST"])
@login_required
@admin_role
def edit_accounts():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        old = db.engine.execute("SELECT * FROM users WHERE name=%s", req["username"]).first()
        if len(old) == 0:
            flash("Cannot edit username")
            return redirect(url_for("access_manager"))
        db.engine.execute("UPDATE users SET role_id=%s WHERE name=%s", int(req["role id"]), req["username"])
    flash("Success")
    return redirect(url_for("access_manager"))


@app.route("/remove_accounts", methods=["POST"])
@login_required
@admin_role
def remove_accounts():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        db.engine.execute("DELETE FROM users WHERE name=%s", req["username"])
    return redirect(url_for("access_manager"))

@app.route("/ata_creation", methods=["POST"])
@login_required
@admin_role
def ata_creation():
    db.engine.execute("INSERT INTO ej(ata_date, president, president_rg, president_cpf, vice_president, vice_president_rg, vice_president_cpf) VALUES(%s, %s, %s, %s, %s, %s, %s)",
                      request.form["date"], request.form["president"], request.form["president_rg"], request.form["president_cpf"], request.form["vice_president"], request.form["vice_president_rg"], request.form["vice_president_cpf"])
    return redirect(url_for("ata_manager"))

@app.route("/remove_ata", methods=["POST"])
@login_required
@admin_role
def remove_ata():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        db.engine.execute("DELETE FROM ej WHERE ata_date=%s", req["ata_date"])
    return redirect(url_for("ata_manager"))

@app.route("/edit_clients", methods=["POST"])
@login_required
@admin_role
def edit_clients():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        old = db.engine.execute("SELECT * FROM clients WHERE id=%s", req["id"]).first()
        if len(old) == 0:
            return redirect(url_for("access_manager"))
        db.engine.execute("UPDATE clients SET store_name=%s, address=%s, cep=%s, cnpj=%s, client_name=%s, rg=%s, cpf=%s, email=%s WHERE id=%s", req["store_name"], req["address"], req["cep"], req["cnpj"], req["client_name"], req["rg"], req["cpf"], req["email"], req["id"])
    return redirect(url_for("access_manager"))

@app.route("/remove_clients", methods=["POST"])
@login_required
@admin_role
def remove_clients():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        db.engine.execute("UPDATE clients SET removed=true WHERE id=%s", req["id"])
    return redirect(url_for("access_manager"))

@app.route("/edit_contracts", methods=["POST"])
@login_required
@admin_role
def edit_contracts():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        old = db.engine.execute("SELECT * FROM services WHERE id=%s", req["id"]).first()
        if len(old) == 0:
            return redirect(url_for("access_manager"))
        descriptions = json.dumps({"short_description": req["short description"], "service_list": req["service list"].split(",")})
        db.engine.execute("UPDATE services SET type=%s, days_to_finish=%s, total_price=%s, payment_price=%s, payment=%s, description=%s, client_id=%s WHERE id=%s", req["type"], req["deadline"], req["price"], req["payment price"], req["payments"], descriptions, req["client id"], req["id"])
    return redirect(url_for("access_manager"))

@app.route("/accept_contracts", methods=["POST"])
@login_required
@admin_role
def accept_contracts():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        client_id, description = db.engine.execute("UPDATE services SET acceptance_date=now() WHERE id=%s RETURNING client_id, description", req["id"]).first()
        store_name, client_name = db.engine.execute("SELECT store_name, client_name from clients WHERE id=%s", client_id).first()
        event_first_payment(store_name, client_name, description["short_description"])
    return redirect(url_for("access_manager"))

@app.route("/add_payment", methods=["POST"])
@login_required
@admin_role
def add_payment():
    payment = int(request.form["payment"])
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])
    service_id = int(request.form["service-id"])
    date = request.form["date"]
    aliquota = float(request.form["aliquota"])
    cst = int(request.form["cst"])
    cnae = int(request.form["cnae"])
    cfps = int(request.form["cfps"])
    aedf = int(request.form["aedf"])
    baseCalcSubst = int(request.form["baseCalcSubst"])

    for i in range(quantity):
        payment_count = db.engine.execute("SELECT count(*) from payments WHERE service_id=%s", service_id).first()[0]
        service_payment = db.engine.execute("SELECT payment from services WHERE id=%s", service_id).first()[0]
        if payment_count + quantity <= service_payment:
            db.engine.execute("INSERT INTO payments(payment, price, service_id) VALUES(%s, %s, %s)", payment + i, price, service_id)
            client_id, description = list(db.engine.execute("SELECT client_id, description FROM services WHERE id=%s", service_id).first())
            store_name, client_name = list(db.engine.execute("SELECT store_name, client_name from clients WHERE id=%s",
                                                    client_id).first())
            event_payments(store_name, client_name, description["short_description"], payment_count + 1)
        else:
            flash(f"Cannot add more payments to {service_id}. Limit exceeded")
            return redirect(url_for("contracts_manager"))

    db.engine.execute("INSERT INTO service_payment_data (service_id, aliquota, cst, cnae, cfps, aedf, baseCalcSubst) VALUES(%s, %s, %s, %s, %s, %s, %s)", service_id, aliquota, cst, cnae, cfps, aedf, baseCalcSubst)
    new_nfe(db, service_id, date, quantity, aliquota, cst, cnae, cfps, aedf, baseCalcSubst)
    first_payment = db.engine.execute("SELECT first_payment FROM services WHERE id=%s", service_id).first()[0]
    if first_payment == None:
        db.engine.execute("UPDATE services SET first_payment=now() WHERE id=%s", service_id)

    flash("Success")

    return redirect(url_for("contracts_manager"))

@app.route("/remove_contracts", methods=["POST"])
@login_required
@admin_role
def remove_contracts():
    complete_request = json.loads(request.get_data().decode("utf-8"))
    for req in complete_request:
        db.engine.execute("UPDATE services SET removed=true WHERE id=%s", req["id"])
    return redirect(url_for("access_manager"))


@app.route("/get_contract_data", methods=["POST"])
@login_required
@admin_role
def get_contract_data():
    req = json.loads(request.get_data().decode("utf-8"))
    raw_response = db.engine.execute("SELECT * FROM service_payment_data WHERE service_id=%s", req["id"]).first()
    if raw_response is None:
        raw_response = [""] * 8
    else:
        raw_response = list(raw_response)
    response = {
        "service_id": raw_response[1],
        "aliquota": raw_response[2],
        "cst": raw_response[3],
        "cnae": raw_response[4],
        "cfps": raw_response[5],
        "aedf": raw_response[6],
        "baseCalcSubst": raw_response[7]
    }

    return jsonify(response)
