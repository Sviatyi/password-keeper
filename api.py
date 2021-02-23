from flask import Flask, render_template, redirect, send_file, url_for, jsonify, request, flash
from firebase_admin import credentials, initialize_app, firestore
import datetime
from secrets import randbelow
from marshmallow import Schema, fields,validates,ValidationError
import json

def generate_id():
    return str(randbelow(1000000)) + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

class UserSchema(Schema):
    user_id = fields.String(required=False)
    name = fields.String(required=False)
    surname = fields.String(required=False)
    email = fields.Email(required=False)
    user_password = fields.String(required=False)
    phone_number = fields.String(required=False)

class PasswordSchema(Schema):
    date_of_creation = fields.String(required=False)
    expiration_date = fields.String(required=False)
    id = fields.Int(required=False)
    level_of_complication = fields.Int(required=False)
    password = fields.String(required=False)
    linked_to = fields.String(required=False)


# Initializing firestore
cred = credentials.Certificate(
                               "password-keeper-295516-firebase-adminsdk-sl8ud-dae4505236.json")
initialize_app(cred, {
    'projectId': 'password-keeper-295516',
})

db = firestore.client()

app = Flask(__name__, static_folder='build',
            static_url_path='/')


@app.route('/')
def home():
    return app.send_static_file('index.html')


#docs = db.collection(u'users').stream()
#passwords = db.collection(u'passwords').stream()


@app.route('/sign-up', methods=['GET', 'POST'])
def display_registration_page():
    return app.send_static_file('index.html')


@app.route('/check_if_registration_allowed', methods=['POST', 'GET'])
def check_if_user_exists():
    if request.method == 'POST':
        req_data = request.data
        try:
            data1 = json.loads(req_data.decode('utf-8'))#Тут перетворення з b{} в {}
            data = UserSchema().load(data1)#тут валідація
        except ValidationError as err:
            return jsonify({"ErrorMessage": "{0}".format(err.messages)})

        phone_number = data["phone_number"]
        docs = db.collection(u'users').stream()
        for doc in docs:
            if doc.to_dict()['phone_number'] == phone_number:
                return jsonify(registration_allowed=False), 400
        return jsonify(registration_allowed=True)


@app.route('/sign-in', methods=['POST', 'GET'])
def allow_login():
    if request.method == 'POST':
        req_data = request.data
        try:
            data1 = json.loads(req_data.decode('utf-8'))  # Тут перетворення з b{} в {}
            data = UserSchema().load(data1)  # тут валідація
        except ValidationError as err:
            return jsonify({"ErrorMessage": "{0}".format(err.messages)})

        phone_number = data["phone_number"]
        user_password = data['user_password']
        docs = db.collection(u'users').stream()
        for doc in docs:
            if doc.to_dict()['phone_number'] == phone_number:
                if doc.to_dict()['user_password'] == user_password:
                    return jsonify({"login_allowed": True,
                                    "user_id": str(doc.to_dict()["user_id"])})
        return jsonify(login_allowed=False)
    


@app.route('/add_user', methods=['POST', 'GET'])
def add_user():
    if request.method == "POST":
        req_data = request.data
        try:
            data1 = json.loads(req_data.decode('utf-8'))  # Тут перетворення з b{} в {}
            data = UserSchema().load(data1)  # тут валідація
        except ValidationError as err:
            return jsonify({"ErrorMessage": "{0}".format(err.messages)})

        email = data['email']
        name = data['name']
        phone_number = data['phone_number']
        surname = data['surname']
        user_password = data['user_password']
        user_id = generate_id()
        dat = {
            u'email': email,
            u'user_id': user_id,
            u'name': name,
            u'passwords': [],
            u'phone_number': phone_number,
            u'surname': surname,
            u'user_password': user_password
        }
        try:
            db.collection(u'users').document(user_id).set(dat)
            return jsonify({"status": "True"}), 200
        except:
            return jsonify({"status": "False",
                            "ErrorMessage": "Bad input parameters"})
    else:
        return app.send_static_file('index.html')


@app.route('/add_password/<string:user_id>', methods=['POST'])
def add_password(user_id):
    if request.method == 'POST':
        try:
            user = db.collection(u'users').document(u'{}'.format(user_id)).get().to_dict()
        except:
            return jsonify({"error message": "invalid id"})
        req_data = request.data
        try:
            data1 = json.loads(req_data.decode('utf-8'))  # Тут перетворення з b{} в {}
            data = PasswordSchema().load(data1)  # тут валідація
        except ValidationError as err:
            return jsonify({"ErrorMessage": "{0}".format(err.messages)})

        now = datetime.date.today()
        date_of_creation = now
        after_six_month = now
        try:
            after_six_month = after_six_month.replace(month=int(after_six_month.month)+6)
        except:
            after_six_month = after_six_month.replace(year=after_six_month.year+1)
            after_six_month = after_six_month.replace(month=(after_six_month.month+6) % 12)

        expiration_date = after_six_month
        id = generate_id()
        level_of_complication = data['level_of_complication']
        password = data['password']
        linked_to = data['linked_to']
        data = {
            u'id': id,
            u'date_of_creation': str(date_of_creation),
            u'expiration_date': str(expiration_date),
            u'level_of_complication': level_of_complication,
            u'password': password,
            u'linked_to': linked_to
        }
        try:
            db.collection(u'passwords').document(id).set(data)
            user["passwords"].append(id)
            db.collection(u'users').document(u"{}".format(user_id)).update({u"passwords": user["passwords"]})
            return jsonify({"status": "True"}), 200
        except:
            return jsonify({"status": "False",
                            "ErrorMessage": "Bad input parameters"})


# @app.route('/edit-password', methods=['GET', 'POST'])
# def edit_passwords(): #TODO password_id OR password_title
#     if request.method == 'POST':
#         password_id = request.form.get('password_id')
#         password_value = request.form.get('password_value')
#         password_title = request.form.get('password_title')
#         for doc in passwords:
#             if doc.to_dict()['password_id'] == password_id:
#                 doc.to_dict()['password_value'] = password_value


@app.route('/get_user_by_id/<string:id>', methods=['GET'])
def get_user_id(id):
    try:
        return jsonify(db.collection(u'users').document(u'{}'.format(id)).get().to_dict())
    except:
        return jsonify({"error message": "invalid id"})


@app.route('/get_passwords/<string:id>', methods=['GET'])
def get_password(id):
    try:
        ps_ids = db.collection(u'users').document(u'{}'.format(id)).get().to_dict()["passwords"]
        passwords = []
        for i in ps_ids:
            all_passwords = db.collection(u'passwords').stream()
            for ps in all_passwords:
                if ps.to_dict()['id'] == i:
                    passwords.append(ps.to_dict())
        return jsonify(passwords)
    except TypeError:
        return jsonify({"error message": "invalid id"})
    except:
        return jsonify({"error message": "something wrong"})


@app.route('/remove_password_by_id/<string:password_id>/<string:user_id>', methods=['GET'])
def remove_password(password_id, user_id):
    try:
        db.collection(u'passwords').document(u"{}".format(password_id)).delete()
    except:
        return jsonify({"error message": "invalid password_id"})

    try:
        user = db.collection(u'users').document(u'{}'.format(user_id)).get().to_dict()
    except:
        return jsonify({"error message": "invalid user_id"})
    try:
        user["passwords"].remove(password_id)
        db.collection(u'users').document(u"{}".format(user_id)).update({u"passwords": user["passwords"]})
    except:
        return jsonify({"error message": "invalid user_id"})
    return jsonify({"status": "True"}), 200


@app.route('/remove_user', methods=[])
def remove_user():
    pass


if __name__ == '__main__':
    app.run(port=4764, debug=True)