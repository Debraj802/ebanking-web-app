import random
from flask import Flask, render_template, request , redirect, url_for
from db_config import get_db_connection
app = Flask(__name__,static_url_path='/static')
@app.route('/')

def home():
    return render_template('home.html')


@app.route('/balance',methods=['GET','POST'])
def balance():
    if request.method == 'POST':
        acc_id = request.form['acc_id']
        upi_pin = request.form['upi_pin']
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT name , avl_bal FROM users WHERE acc_id = %s AND upi_pin = %s", (acc_id,upi_pin))
        user = cursor.fetchone()
        db.close()
        if user:
            return render_template('balance.html' , name=user[0],balance=user[1])
        else:
            return render_template("error.html")
    return render_template('balance_form.html')

@app.route('/withdraw',methods=['GET','POST'])
def withdraw():
    if request.method == 'POST':
        upi_pin = request.form['upi_pin']
        amount=int(request.form['amount'])

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT avl_bal FROM users WHERE upi_pin = %s", (upi_pin,))
        result = cursor.fetchone()

        if result:
            current_balance = result[0]
            if amount > current_balance:
                return "Not Enough Balance To Withdraw"
            else:
                cursor.execute("UPDATE  users SET avl_bal = avl_bal-%s WHERE upi_pin=%s" , (amount,upi_pin))
                db.commit()
                cursor.execute("SELECT avl_bal FROM users WHERE upi_pin=%s",(upi_pin,))
                new_balance = cursor.fetchone()
                db.close()
                return redirect(url_for('home'))
        else:
            return "Invalid UPI PIN"
    return render_template('withdraw_form.html')

@app.route('/deposit', methods = ['GET' ,'POST'])
def deposit():
    if request.method == 'POST':
        acc_id = request.form['acc_id']
        amount=int(request.form['amount'])
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE acc_id = %s)",(acc_id,))
        account_exists = cursor.fetchone()[0]
        if account_exists:
            cursor.execute("UPDATE users SET avl_bal = avl_bal + %s WHERE acc_id = %s",(amount,acc_id))
            db.commit()
            cursor.execute("SELECT avl_bal FROM users WHERE acc_id = %s",(acc_id,))
            new_balance = cursor.fetchone()[0]
            db.close()
            return redirect(url_for('home'))
        else:
            return "Invalid Account ID"
    return render_template('deposit_form.html')

@app.route('/transfer', methods=['GET' , 'POST'])
def transfer():
    if request.method == 'POST':
        sender_pin = request.form['sender_pin']
        beneficiary_id=request.form['beneficiary_id']
        amount=int(request.form['amount'])

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT avl_bal FROM users WHERE upi_pin = %s", (sender_pin,))
        sender = cursor.fetchone()
        if not sender:
            return "Sender UPI PIN is Invalid"
        sender_balance = sender[0]

        cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE acc_id=%s)" , (beneficiary_id,))
        beneficiary_exists = cursor.fetchone()[0]
        if not beneficiary_exists:
            return "Beneficiary Account Id not Found"
        
        if amount>sender_balance:
            return "Insufficient Balance to transfer"
        
        cursor.execute("UPDATE users SET avl_bal = avl_bal - %s WHERE upi_pin = %s" , (amount,sender_pin))
        cursor.execute("UPDATE users SET avl_bal = avl_bal + %s WHERE acc_id = %s" , (amount,beneficiary_id))
        db.commit()
        db.close()

        return redirect(url_for('home'))
    return render_template('transfer_form.html')

@app.route('/create' , methods=['GET','POST'])
def create_account():
    if request.method == 'POST':
        acc_id=request.form['acc_id']
        a_count=len(str(abs(int(acc_id))))
        if a_count!=3:
            return "Account ID must be Exactly 3 digits"

        name = request.form['name']

        balance = int(request.form['balance'])
        if balance<3000:
            return "Cannot proceed Due to Less Amount"

        mobile = request.form['mobile']

        m_count=len(str(abs(int(mobile))))
        if m_count!=10:
            return "Mobile number must be Exactly 10 digits"

        dob = request.form['dob']
        
        email = request.form['email']
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE acc_id = %s)", (acc_id,))
        id_exists = cursor.fetchone()[0]
        if id_exists:
            return "Account Already Exists..."

        #generating the unique upi_pin
        while True:
            upi_pin = random.randint(1000,9999)
            cursor.execute("SELECT COUNT(*) FROM users WHERE upi_pin = %s" , (upi_pin,))
            pin_exists = cursor.fetchone()[0]
            if pin_exists == 0:
                break

        
        cursor.execute("INSERT INTO users (acc_id, name , avl_bal, upi_pin , mobile_no, DOB ,email) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        ,(acc_id, name , balance , upi_pin , mobile , dob , email))
        db.commit()
        db.close()
        return render_template(
            "create_success.html",
            name=name,
            acc_id=acc_id,
            upi_pin=upi_pin
        )
    return render_template('create_form.html')

@app.route('/delete' , methods=['GET','POST',])
def delete_account():
    if request.method == 'POST':
        acc_id=request.form['acc_id']
        upi_pin=request.form['upi_pin']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE  acc_id = %s AND upi_pin = %s)",(acc_id,upi_pin))
        exists=cursor.fetchone()[0]
        if not exists:
            db.close()
            return "Account not found or Wrong UPI PIN"
        cursor.execute("DELETE FROM users WHERE  acc_id = %s AND upi_pin = %s",(acc_id,upi_pin))
        db.commit()
        db.close()
        return f"Account with ID {acc_id} has been deleted successfully.<br><br> Dear user Your Account Has been Terminated if not Done by You Contact Immidiately to DBA"
    return render_template('delete_form.html')

@app.route('/update' , methods=['GET','POST'])
def update_contact():
    if request.method == 'POST':
        acc_id=request.form['acc_id']
        upi_pin=request.form['upi_pin']
        field=request.form['field']
        new_value=request.form['new_value']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT EXISTS(SELECT * FROM users WHERE  acc_id = %s AND upi_pin = %s)",(acc_id,upi_pin))
        exists=cursor.fetchone()[0]
        if not exists:
            db.close()
            return "Account not found or Wrong UPI PIN"
        if field == 'mobile':
            cursor.execute("UPDATE users SET mobile_no = %s WHERE  acc_id=%s", (new_value,acc_id))
        elif field == 'email':
            cursor.execute("UPDATE users SET email = %s WHERE  acc_id=%s", (new_value,acc_id))
        else:
            db.close()
            return "Invalid field Selected"
        db.commit()
        db.close()
        return f"{field.capitalize()} updated successfully for Account ID {acc_id}"
    return render_template('update_form.html')

if __name__ == '__main__':
    app.run(debug=True)
 