from flask import Flask,redirect,url_for,render_template,request,session,send_file
from datetime import datetime
from io import BytesIO
import json
import re
from mail import send_email
import random

app = Flask(__name__)
app.secret_key = 'atm55'


def generate_otp():
    return str(random.randint(100000,999999))

def get_data():
    with open('data.json','r') as file:
        data = json.load(file)
        return data

def update_data(data):
    with open('data.json','w') as file:
        json.dump(data,file,indent=4)

def get_current_balance(data):
    for user in data["users"]:
        if user["id"] == session.get("id"):
            return user["balance"]
    return 0


def build_pdf(lines):
    """Create a small, readable PDF receipt without an extra package."""
    escape = lambda value: str(value).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    stream_lines = ['BT', '/F1 18 Tf', '72 740 Td']
    for index, line in enumerate(lines):
        if index:
            stream_lines.append('0 -28 Td')
        stream_lines.append(f'({escape(line)}) Tj')
    stream_lines.append('ET')
    stream = '\n'.join(stream_lines).encode('latin-1', errors='replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'\nendstream',
    ]
    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{number} 0 obj\n'.encode())
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')
    xref_offset = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode())
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode())
    pdf.extend(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF'.encode())
    return bytes(pdf)


def receipt_from_history(entry):
    match = re.match(r'([\d.]+)\s+(deposited|Withdraw)', entry)
    if not match:
        return {'type': 'Transaction', 'amount': entry, 'balance': ''}
    return {'type': 'Deposit' if match.group(2) == 'deposited' else 'Withdrawal', 'amount': match.group(1), 'balance': ''}


def make_receipt_response(receipt):
    lines = [
        'ATM BANKING - TRANSACTION RECEIPT',
        f"Account holder: {receipt['username']}",
        f"Transaction: {receipt['type']}",
        f"Amount: Rs. {receipt['amount']}",
        f"Balance after transaction: Rs. {receipt['balance']}",
        f"Date: {receipt['date']}",
    ]
    return send_file(BytesIO(build_pdf(lines)), mimetype='application/pdf', as_attachment=True, download_name='atm-transaction-receipt.pdf')


@app.route('/download_receipt')
def download_receipt():
    receipt = session.get('last_receipt')
    if not receipt or receipt.get('user_id') != session.get('id'):
        return redirect(url_for('viewtransactions'))
    return make_receipt_response(receipt)


@app.route('/download_receipt/<int:transaction_index>')
def download_history_receipt(transaction_index):
    data = get_data()
    user = next((user for user in data['users'] if user['id'] == session.get('id')), None)
    if not user or transaction_index < 0 or transaction_index >= len(user['history']):
        return redirect(url_for('viewtransactions'))
    receipt = receipt_from_history(user['history'][transaction_index])
    receipt.update({'user_id': user['id'], 'username': user['username'], 'date': datetime.now().strftime('%d %b %Y, %I:%M %p')})
    return make_receipt_response(receipt)
    

@app.route('/')
def base():
    return redirect('login')

@app.route('/login',methods = ['GET','POST'])
def login():
    info=request.args.get('info')
    if request.method == 'POST':
        email = request.form.get('email')
        pin = request.form.get('pin')
        data = get_data()
        users = data["users"]
        for i in users:
            if i["email"] == email and  i["pin"]==pin:
                session['username'] = i["username"]
                session['id'] = i["id"]
                return redirect(url_for('dashboard', user=i["username"]))
        else:
            return render_template('login.html', info="Invalid login")

    return render_template('login.html', info=info)

@app.route('/register',methods=['GET','POST'])
def register():
    info=request.args.get('info')
    if request.method == 'POST':
        username = request.form.get('uname')
        email = request.form.get('email')
        pin = request.form.get('pin')
        data = get_data()
        users = data["users"]

        for i in users:
            if i["email"] == email:
                return render_template("register.html",info="Email is already registered")
        details = {
            "id": len(users)+1,
            "username":username,
            "email":email,
            "pin":pin,
            "history": [],
            "balance": 0
        }
        users.append(details)
        update_data(data)
        return redirect('login')

    return render_template("register.html")

@app.route('/forgotpin',methods=['GET','POST'])
def forgotpin():
    info=request.args.get('info')
    if request.method == 'POST':
        email = request.form.get('email')
        data = get_data()
        users = data["users"]
        for i in users:
            if email == i["email"]:
                username = i["username"]
                otp = generate_otp()
                send_email(email,username,otp)
                session["otp"]=otp
                session['email']=email
                return redirect('verify')
            
        return render_template('forgotpin.html',info="Email is not registered yet")

    return render_template('forgotpin.html')

@app.route('/verify',methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        otp = request.form.get('otp')
        if otp == session["otp"]:
            session['otp']=None
            return redirect('resetpin')
        return render_template('verify.html',info="Invalid OTP")
    return render_template('verify.html')

@app.route('/resetpin',methods=['GET','POST'])
def resetpin():
    if request.method == 'POST':
        npin = request.form.get('npin')
        cpin = request.form.get('cpin')
        if npin == cpin:
            data = get_data()
            users = data["users"]
            for i in users:
                if i["email"] == session['email']:
                    i["pin"] = npin
                    update_data(data)
                    return redirect('login')

        return render_template('resetpin.html',info="Confirm the pin properly")
    return render_template('resetpin.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('login')

@app.route('/dashboard/<user>')
def dashboard(user):
    return render_template("dashboard.html",username=user)

@app.route('/checkBalance')
def checkBalance():
    data = get_data()
    users = data["users"]
    for i in users:
        if i["id"]==session['id']:
            balance = i["balance"]
            return render_template('checkbalance.html',
                           username = session['username'],
                           balance=balance)

@app.route('/deposit',methods=['GET','POST'])
def deposit():
    if request.method=='POST':
        try:
            amount = int(request.form.get('amount'))
        except Exception:
            return render_template("deposit.html",
                                username = session['username'],
                                balance = get_current_balance(get_data()),
                                info="Enter the proper amount")
        data = get_data()
        users = data["users"]
        for i in users:
            if i["id"] == session["id"]:
                i["balance"]+=amount
                i["history"].append(f"{amount} deposited")
                update_data(data)
                session['last_receipt'] = {'user_id': i['id'], 'username': i['username'], 'type': 'Deposit', 'amount': amount, 'balance': i['balance'], 'date': datetime.now().strftime('%d %b %Y, %I:%M %p')}
                return redirect('checkBalance')
    return render_template("deposit.html", balance=get_current_balance(get_data()))

@app.route('/withdraw',methods=['POST','GET'])
def withdraw():
    if request.method=='POST':
        try:
            amount = int(request.form.get('amount'))
            if amount < 0:
                raise Exception("Enter the proper amount")
        except Exception:
            return render_template("withdraw.html",
                                username = session['username'],
                                balance = get_current_balance(get_data()),
                                info="Enter the proper amount")
        
        data = get_data()
        users = data["users"]
        for i in users:
            if i["id"] == session["id"]:
                if i["balance"]>=amount:
                    i["balance"]-=amount
                    i["history"].append(f"{amount} Withdraw")
                    update_data(data)
                    session['last_receipt'] = {'user_id': i['id'], 'username': i['username'], 'type': 'Withdrawal', 'amount': amount, 'balance': i['balance'], 'date': datetime.now().strftime('%d %b %Y, %I:%M %p')}
                    return redirect('checkBalance')
                else:
                    return render_template("withdraw.html",
                                username = session['username'],
                                balance = i["balance"],
                                info="Insufficient balance")

    return render_template('withdraw.html', balance=get_current_balance(get_data()))

@app.route('/viewtransactions')
def viewtransactions():
    data = get_data()
    users = data["users"]
    for i in users:
        if i["id"]==session["id"]:
            history = i["history"]
            length = len(history)
            return render_template("viewtransactions.html",
                                   history=history,
                                   length=length)

if __name__ == '__main__':
    app.run(debug=True)