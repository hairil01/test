from flask import Flask, render_template, url_for, request,Response, session,redirect, render_template
import pytesseract
from PIL import Image
import os
import io
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import plotly.express as px
import re
matplotlib.use('Agg')  # Set the backend before importing pyplot
from datetime import datetime

os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

app = Flask(__name__)
app.secret_key = b'W"\x07\xb5\x98\xea\x17\x00\xe6\xd6\xb5\xcb\x92\xe4U\xc3Ol\xb6\xf2\x84x\x19#'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def connect_to_database():
    try:
        conn = mysql.connector.connect(user='root', password='root', host='localhost', database='fypdb')
        print("Connection established successfully")
        return conn
    except mysql.connector.Error as error:
        print("Failed to connect to database: {}".format(error))

@app.route('/register_login')
def register_login():
    return render_template('login.html')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    password = request.form['password']
    phone = request.form['phone']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    
    # Connect to the database
    conn = connect_to_database()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO users (username, user_password, user_phone, user_email, first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (name, password, phone, email, first_name, last_name)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        alert_script = 'Registration Succesfull'
        return render_template('login.html', alert_script=alert_script)
    else:
        return "Failed to connect to database"
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/register_login')
    
@app.route('/login', methods=['POST'])
def login():
    conn = connect_to_database()
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username FROM users WHERE username=%s AND user_password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['username'] = user['username']
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

@app.route('/notification')
def budget():
    user_id = session.get('user_id')
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    
    # Get the current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Calculate the total expenses for the current month and year
    sql_expenses = "SELECT SUM(COALESCE(amount, 0)) AS total_amount FROM daily_expenses WHERE user_id = %s AND MONTH(date) = %s AND YEAR(date) = %s"
    cursor.execute(sql_expenses, (user_id, current_month, current_year))
    result_expenses = cursor.fetchone()

    if result_expenses is not None:
        total_expenses = result_expenses['total_amount']
    else:
        total_expenses = 0

    print(total_expenses)

    # Retrieve the budget amount for the current month and year
    sql_budget = "SELECT amount FROM budget WHERE user_id = %s AND month = %s AND year = %s"
    cursor.execute(sql_budget, (user_id, current_month, current_year))
    result_budget = cursor.fetchone()

    if result_budget is not None:
        budget_amount = result_budget['amount']
    else:
        budget_amount = 0

    print(budget_amount)

    if total_expenses > budget_amount:
        notification = f"Budget exceeded! Total expenses: {total_expenses}, Budget: {budget_amount}"
    else:
        notification = "Budget not exceeded"

    return render_template('home.html', notification=notification)

@app.route('/home')
def home():
    username = session.get('username')
    if username:
        user_id = session.get('user_id')
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        # Get the current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Perform budget calculations
       # Calculate the total expenses for the current month and year
        sql_expenses = "SELECT IFNULL(SUM(amount), 0) AS total_amount FROM daily_expenses WHERE user_id = %s AND MONTH(date) = %s AND YEAR(date) = %s"
        cursor.execute(sql_expenses, (user_id, current_month, current_year))
        result_expenses = cursor.fetchone()
        total_expenses = result_expenses['total_amount']
        print(total_expenses)

        # Retrieve the budget amount for the current month and year
        sql_budget = "SELECT amount FROM budget WHERE user_id = %s AND month = %s AND year = %s"
        cursor.execute(sql_budget, (user_id, current_month, current_year))
        result_budget = cursor.fetchone()
        budget_amount = result_budget['amount'] if result_budget and 'amount' in result_budget else 0
        print(budget_amount)

        if total_expenses > budget_amount:
            notification = f"Budget exceeded! Total expenses: {total_expenses}, Budget: {budget_amount}"
        else:
            notification = f"Budget not exceeded! Total expenses: {total_expenses}, Budget: {budget_amount}"

        return render_template('home.html', username=username, notification=notification)


@app.route('/nav')
def nav():
    username = session.get('username')
    if username:
        return render_template('nav.html', username=username)
    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))

@app.route('/sejarah')
def sejarah():
    username = session.get('username')
    if username:
        user_id = session.get('user_id')
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        sql_expenses = "SELECT * FROM daily_expenses WHERE user_id = %s ;"

        cursor.execute(sql_expenses, (user_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('sejarah.html', result=result)
    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))

@app.route('/ikutMonth',methods=['GET','POST'])
def ikutMonth():
    username = session.get('username')
    if username:
        month = request.form.get('month')
        user_id = session.get('user_id')
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
        sql_expenses = "SELECT * FROM daily_expenses WHERE user_id = %s AND MONTH(date) = %s;"

        cursor.execute(sql_expenses, (user_id,month))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('sejarah.html', result=result)
        # Retrieve the budget amount for the current month and year
    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))
    
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    username = session.get('username')
    if username:
        expense_id = request.form.get('expense_id')

        user_id = session.get('user_id')
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        sql_expenses = "DELETE FROM daily_expenses WHERE expense_id = %s ;"
        print(sql_expenses)
        cursor.execute(sql_expenses, (expense_id,))
        conn.commit()  # Commit the deletion to the database
        cursor.close()
        conn.close()

        # Redirect to the 'sejarah' page after successful deletion
        alert_script = 'Spending succesfully deleted'
        return render_template('sejarah.html', alert_script=alert_script)

    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    username = session.get('username')
    if username:
        if request.method == 'POST':
            expense_id = request.form['id']
            date = request.form['date']
            amount = request.form['amount']
            category = request.form['category']

            conn = connect_to_database()
            cursor = conn.cursor()

            # Update the expense data in the database
            sql_update = "UPDATE daily_expenses SET date = %s, amount = %s, category = %s WHERE expense_id = %s"
            cursor.execute(sql_update, (date, amount, category, expense_id))
            conn.commit()

            cursor.close()
            conn.close()

            alert_script = 'Spending succesfully edited'
            return render_template('sejarah.html', alert_script=alert_script)
            # Redirect to the 'sejarah' page after successful update

        else:
            expense_id = request.args.get('id')

            # Retrieve the expense data from the database based on the expense_id
            conn = connect_to_database()
            cursor = conn.cursor(dictionary=True)

            sql_select = "SELECT * FROM daily_expenses WHERE expense_id = %s"
            cursor.execute(sql_select, (expense_id,))
            expense = cursor.fetchone()

            cursor.close()
            conn.close()

            return render_template('edit.html', expense=expense)
    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))
    
@app.route('/set_budget',methods=['GET','POST'])
def set_budget():
    user_id=session.get('user_id')
    
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        amount = request.form.get('amount')

        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)
        
      
        # Insert the budget data into the database
        query = "INSERT INTO budget (user_id, month, year,amount) VALUES (%s, %s, %s,%s)"
        values = (user_id, month, year,amount)
        cursor.execute(query, values)

        conn.commit()

        cursor.close()
        conn.close()

        alert_script = 'Budget data inserted succesfully!'
        return render_template('set_budget.html', alert_script=alert_script )
    
    return render_template("set_budget.html")
    
    

@app.route('/add_expense',methods=['GET','POST'])
def add_expense():
    user_id=session.get('user_id')

    amount = request.args.get('amount', default=None)  # Get the 'amount' query parameter

    if request.method == 'POST':
        date = request.form.get('date')
        category = request.form.get('category')
        amount = request.form.get('amount')

        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        # Insert the budget data into the database
        query = "INSERT INTO daily_expenses (user_id, date, category,amount) VALUES (%s, %s, %s,%s)"
        values = (user_id, date, category,amount)
        cursor.execute(query, values)

        conn.commit()

        cursor.close()
        conn.close()

        alert_script = 'Spending succesfully added'
        return render_template('sejarah.html', alert_script=alert_script)
    
    return render_template("add_expense.html", amount=amount)

@app.route('/manual_tambah',methods=['GET','POST'])
def manual_tambah():
    user_id=session.get('user_id')


    if request.method == 'POST':
        date = request.form.get('date')
        category = request.form.get('category')
        amount = request.form.get('amount')

        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        # Insert the budget data into the database
        query = "INSERT INTO daily_expenses (user_id, date, category,amount) VALUES (%s, %s, %s,%s)"
        values = (user_id, date, category,amount)
        cursor.execute(query, values)

        conn.commit()

        cursor.close()
        conn.close()

        alert_script = 'Spending succesfully added'
        return render_template('sejarah.html', alert_script=alert_script)
    
    return render_template("sejarah.html")

@app.route('/chart')
def chart():
    username = session.get('username')
    if username:
        user_id = session.get('user_id')
        
        return render_template('expenses_chart.html')
    else:
        # Handle the case when the username is not available
        return redirect(url_for('login'))


@app.route('/expenses_chart', methods=['GET', 'POST'])
def expenses_chart():
    user_id = session.get('user_id')
    if request.method == 'POST':
        month = request.form.get('months')
        conn = connect_to_database()
        cursor = conn.cursor(dictionary=True)

        # Query the database to get expenses for each category in a specific month
        sql = 'SELECT category, SUM(amount) AS total_amount FROM daily_expenses WHERE user_id = %s AND MONTH(date) = %s GROUP BY category'
        cursor.execute(sql, (user_id, month))
        expenses = cursor.fetchall()
        cursor.close()

        # Extract category labels and corresponding amounts
        categories = [expense['category'] for expense in expenses]
        amounts = [expense['total_amount'] for expense in expenses]

        # Create a dataframe for the chart
        df = pd.DataFrame({'Category': categories, 'Total Amount': amounts})
        if int(month) == 1:
            ayam = 'January'
        
        elif int(month) == 2:
            ayam = 'February'

        elif int(month) == 3:
            ayam = 'March'

        elif int(month) == 4:
            ayam = 'April'

        elif int(month) == 5:
            ayam = 'May'

        elif int(month) == 6:
            ayam = 'June'

        elif int(month) == 7:
            ayam = 'July'

        elif int(month) == 8:
            ayam = 'August'

        elif int(month) == 9:
            ayam = 'September'

        elif int(month) == 10:
            ayam = 'October'

        elif int(month) == 11:
            ayam = 'November'

        elif int(month) == 12:
            ayam = 'December'
            

        title = "Expense for " + ayam
        print(title)
        # Generate the pie chart using plotly
        fig = px.pie(df, values='Total Amount', names='Category')

        # Save the chart as HTML file
        chart_file = r"C:\Users\muham\OneDrive - Universiti Teknologi MARA\Documents\Degree Sem 6\PROJECT\fyp2\static\expenses_chart.html"
        fig.write_html(chart_file)

        return render_template('expenses_chart.html', chart_file=chart_file, title=title)
    
    # Handle GET request (render the form)
    return render_template('expenses_chart.html')

@app.route('/try')
def ayam():
    return render_template("tambah.html")

@app.route('/ocr')
def ocr():
    return render_template("index.html")

@app.route('/manual')
def manual():
    return render_template("manual.html")

@app.route('/hello')
def hello():
    data = "Hello, World!"
    return render_template('hello.html', data=data)

def ocr_core(filename):
    text = pytesseract.image_to_string(Image.open(filename))
    return text

@app.route('/upload', methods=['POST'])
def upload():
    if 'images' not in request.files:
        return 'No image uploaded!', 400

    image_file = request.files['images']
    image = Image.open(image_file)
    try:
        ocr_result = pytesseract.image_to_string(image)
        currency_symbol = "TOTAL"
        total_price_index = ocr_result.find(currency_symbol)
        amount_paid_pattern = r"Amount Paid\s*RM\s*([\d,.]+)"

        if total_price_index != -1:
            total_price = ocr_result[total_price_index + len(currency_symbol) + 1:].split()[0]
            print("Total price: ", total_price)

            # Check if the 'total_price' contains a valid numeric value
            try:
                total_price = float(total_price)
                print("Valid total price: ", total_price)
                return redirect(url_for('add_expense', amount=total_price))
            except ValueError:
                print("Invalid total price:", total_price)

        # Find the "Amount Paid" value using regular expression
        match = re.search(amount_paid_pattern, ocr_result)
        if match:
            amount_paid = match.group(1).replace(',', '.')  # Replace comma with dot for decimal separator
            print("Amount Paid: ", amount_paid)

            # Check if the 'amount_paid' contains a valid numeric value
            try:
                amount = float(amount_paid)
                print("Valid amount: ", amount)
                return redirect(url_for('add_expense', amount=amount))
            except ValueError:
                print("Invalid amount:", amount_paid)

        if match:
            debit_paid = match.group(1).replace(',', '.')  # Replace comma with dot for decimal separator
            print("debit Paid: ", debit_paid)

            try:
                debit_amount = float(debit_paid)
                print("Valid amount: ", debit_amount)
                return redirect(url_for('add_expense', amount=debit_amount))
            except ValueError:
                print("Invalid amount:", debit_paid)

        return "No valid total price or amount found in OCR result."
        
    except Exception as e:
        return f'Error extracting text from the image: {str(e)}', 500


@app.route('/result')
def result():
    return render_template("result.html")   

@app.route('/')
def index():
    return render_template('ayam.html')

@app.route('/snackbar')
def snackbar():
    return render_template('snackbar.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000) 
