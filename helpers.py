from functools import wraps
from flask import session, request, redirect, url_for, flash
from enum import Enum
import datetime
import sapixel
import nfe


class Roles(Enum):
    CREATION = "CREATION"
    ADMIN = "ADMIN"


def start_db(db):
    commands = ['''
    CREATE TABLE IF NOT EXISTS ej (
        id serial primary key,
        ata_date date not null,
        president text not null,
        president_rg text not null,
        president_cpf text not null,
        vice_president text not null,
        vice_president_rg text not null,
        vice_president_cpf text not null
        )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS roles (
        id serial primary key,
        permissions text[]
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS users (
        id serial primary key,
        name text not null unique,
        password text not null,
        role_id integer REFERENCES roles(id) not null
        )
    ''',
        '''
    CREATE TABLE IF NOT EXISTS clients (
        id serial primary key,
        store_name text,
        address text not null,
        cep text not null,
        cnpj text,
        client_name text not null,
        rg text not null,
        cpf text not null,
        email text not null,
        removed boolean not null default false
        )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS services (
        id serial primary key,
        username text not null,
        type text not null,
        days_to_finish integer not null,
        total_price float not null,
        payment_price float not null,
        payment integer not null,
        description json not null,
        contract_generation_date date not null default now(),
        acceptance_date date,
        first_payment date,
        client_id integer REFERENCES clients(id) not null,
        removed boolean not null default false
        )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS payments (
        id serial primary key,
        payment serial not null,
        price float not null,
        service_id integer REFERENCES services(id)
    )
    '''
    ]
    for command in commands:
        db.engine.execute(command)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id"):
            return f(*args, **kwargs)
        return redirect(url_for('access'))
    return decorated_function


def creation_role(f):
    return role(f, roles=[Roles.CREATION.name])


def admin_role(f):
    return role(f, roles=[Roles.ADMIN.name])


def role(f, roles):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") and session.get("roles") and check_roles(roles, session["roles"]):
            return f(*args, **kwargs)
        flash("You don't have permission to see this page")
        return redirect(url_for('access'))
    return decorated_function


def check_roles(roles, user_roles):
    for role in roles:
        if role in user_roles:
            return True
    return False


def normalize_array(array):
    return array.replace(" ", "").split(",")


def event_first_payment(client_store_name, client_name, short_description):
    start_date = datetime.datetime.now() + datetime.timedelta(days=30)
    end_date = datetime.datetime.now() + datetime.timedelta(days=30)
    model = "first_payment"
    new_calendar_event(model, start_date, end_date, client_store_name, client_name, short_description)


def event_payments(client_store_name, client_name, short_description, payment):
    start_date = datetime.datetime.now() + datetime.timedelta(days=30)
    end_date = datetime.datetime.now() + datetime.timedelta(days=30)
    model = "payments"
    new_calendar_event(model, start_date, end_date, client_store_name, client_name, short_description, title=payment)


def new_calendar_event(model, start_date, end_date, client_store_name, client_name, short_description, title):
    title = f" {title} {client_store_name} de {client_name}"
    description = " pelo serviço " + short_description
    sapixel.new_calendar_event_from_model(model_name=model, start_date=start_date, end_date=end_date, title=title, description=description)


def new_nfe(db, service_id, date, quantity, aliquota, cst, cnae, cfps, aedf, baseCalcSubst):
    client_neighborhood, price, cep, email, client_cpf, client_cnpj, street, store_name, service_description = list(db.engine.execute("SELECT neighborhood, total_price, cep, email, cpf, cnpj, street, store_name, description from services INNER JOIN clients ON services.client_id=clients.id WHERE services.id=%s", service_id).first())
    args = {
        "aliquota": aliquota,
        "cst": cst,
        "cnae": cnae,
        "cfps": cfps,
        "aedf": aedf,
        "baseCalcSubst": baseCalcSubst,
        "date_iso_format": date,
        "quantity": quantity,
        "client_neighborhood": client_neighborhood,
        "price": price,
        "client_cep": cep,
        "client_email": email,
        "client_cpf_or_cnpj": client_cpf if not client_cnpj else client_cnpj,
        "client_street": street,
        "client_store_name": store_name,
        "service_description": service_description["short_description"]
    }
    nfe.gen_xml_payment(**args)
