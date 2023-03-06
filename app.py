# Following imports and configuration CR to:
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/#a-minimal-application
from flask import Flask, render_template, g, request, session, redirect, url_for, escape
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__)
app.secret_key = 'abbas'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
dbEngine = db.engine


# Here are SYH's helpers
# Find user according to username
def returnUserByUsername(username):
    sql = """SELECT * FROM Accounts
            WHERE Accounts.username = '{}'""".format(username)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res[0]


# Find all instructors
def returnInstructors():
    sql = """SELECT * FROM Accounts
            WHERE identity = 'Instructor'"""
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res


# Find a student's all marks
def returnStudentMarkBySid(sid):
    sql = """SELECT * FROM Marks
        WHERE Marks.sid = '{}'""".format(sid)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res


# Find all marks
def returnAllMarks():
    sql = """SELECT * FROM Marks"""
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res


# delete certain mid
def deleteMarkByMid(mid):
    sql = """DELETE from Marks
        WHERE mid = '{}'""".format(mid)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        return result


# return whether pair of sid and item exists
def markExists(sid, item):
    sql = """SELECT * FROM Marks
            WHERE sid = '{}' and item = '{}'""".format(sid, item)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        if len(res) != 0:
            return res[0]['mid']
        else:
            return -1


# update mark
def updateMarkByMid(mid, newMark):
    sql = """UPDATE Marks
        SET score = '{}'
        WHERE mid = '{}'""".format(newMark, mid)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        return result


# add new mark
def insertNewMark(sid, item, score):
    sql = """INSERT INTO Marks (sid, item, score)
            VALUES ('{}', '{}', '{}')""".format(sid, item, score)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        return result


# add new remark request
def insertRemark(mid, desc):
    sql = """INSERT INTO RemarkRequest (mid, desc)
        VALUES ('{}', '{}')""".format(mid, desc)
    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        return result


# add new remark request
def returnAllRemarks():
    sql = """SELECT * FROM RemarkRequest"""

    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res


# return 1 if sid exists, 0 if it doesn't
def sidExists(sid):
    sql = """SELECT
	            CASE WHEN exists(SELECT id FROM Accounts
						WHERE id = '{}') THEN 1
	            ELSE 0 END
	            AS RESULT""".format(sid)

    with dbEngine.begin() as connection:
        result = connection.execute(text(sql))
        res = [dict(row) for row in result]
        return res[0]


# SYH's database connector ends


# HT's code starts
# default route: (1) check status: whether logged in (2) check identity: student/instructor
@app.route('/')
def index():
    if 'username' in session:
        if session['username'][1] == 1:
            return render_template('s_index.html')
        elif session['username'][1] == 2:
            return render_template('i_index.html')
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        error = ''
        # all users
        username = request.form['username']
        query = text("select identity, username, password from ACCOUNTS where username == '{}'".format(username))
        result = db.engine.execute(query)

        # check status
        if result == "":
            error = "Username does not exist. Please sign up first."
            return render_template('login.html', error=error)
        for user in result:
            if user['username'] == request.form['username'] and user['password'] == request.form['password']:
                if user['identity'] == 'Student':
                    session['username'] = [username, 1]
                else:
                    session['username'] = [username, 2]
                return redirect(url_for('index'))
            else:
                error = "Username and Password did not match."
                return render_template('login.html', error=error)

    return render_template('login.html')


# Log out
# CR to Abbas in-class demo
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        error = ""
        i = request.form.get('identity')
        f = request.form['fname']
        l = request.form['lname']
        u = request.form['username']
        p1 = request.form['password1']
        p2 = request.form['password2']
        query = text("select identity, username, password from ACCOUNTS where username == '{}'".format(u))
        result = db.engine.execute(query)

        if '\'' in f or  '\'' in l or '\'' in u or '\'' in p1 or '\'' in p2 :
            return render_template('s_marks.html', message="Input contains single quotes, please try again.")
        if result != "":
            error = "Username already exists. Please try another one."
            return render_template('signup.html', error=error)
        elif p1 == p2:
            query = text(
                "INSERT INTO ACCOUNTS (identity, fname, lname, username, password) VALUES ('{}','{}','{}','{}','{}') ".format(
                    i, f, l, u, p1))
            db.engine.execute(query)
            return redirect(url_for('login'))
        else:
            error = 'Please try again.'
            return render_template('signup.html', error=error)
    return render_template('signup.html')


@app.route('/s_feedback', methods=['POST', 'GET'])
def s_feedback():
    if 'username' not in session:
        return render_template('login.html')
    elif session['username'][1] == 2:
        return render_template('i_index.html')

    query = text("SELECT username,fname,lname FROM ACCOUNTS WHERE identity = 'Instructor'")
    result = db.engine.execute(query)
    recipients = [dict(row) for row in result]

    message = ""
    if request.method == 'POST':
        i = request.form.get('recipients')
        n = request.form['name']
        e = request.form['email']
        q1 = request.form['q1']
        q2 = request.form['q2']
        q3 = request.form['q3']
        q4 = request.form['q4']

        if '\'' in q1 or '\'' in q2 or '\'' in q3 or '\'' in q4 or '\'' in e or '\'' in n:
            return render_template('s_feedback.html', message="Input contains single quotes, please try again.")

        query = text(
            "INSERT INTO FEEDBACK (iusername,sname,email,q1,q2,q3,q4) VALUES ('{}','{}','{}','{}','{}','{}','{}') ".format(
                i, n, e, q1, q2, q3, q4))
        db.engine.execute(query)
        message = "Successfully submitted!"
        return render_template('s_feedback.html', message=message)
    return render_template('s_feedback.html', recipients=recipients)


@app.route('/i_feedback', methods=['Get', 'POST'])
def i_feedback():
    if 'username' not in session:
        return render_template('login.html')
    elif session['username'][1] == 1:
        return render_template('s_index.html')

    user = session['username'][0]
    query = text("SELECT q1,q2,q3,q4 FROM FEEDBACK WHERE iusername = '{}'".format(user))
    result = db.engine.execute(query)
    res = [dict(row) for row in result]
    return render_template('i_feedback.html', feedbacks=res)


# Link static websites
@app.route('/<file>', methods=['GET'])
def link(file):
    # define valid static file names
    sites = ['calendar', 'lecNotes', 'labs',
             'assignments', 'tests', 'resources']

    path = str(file)
    web = ''

    # get a valid file name
    if path in sites:
        # check status
        if session['username'][1] == 1:
            web = 's_' + path + '.html'
            return render_template(web)
        elif session['username'][1] == 2:
            web = 'i_' + path + '.html'
            return render_template(web)

    if path == 'login' or 'signup':
        return render_template(path + '.html')
    return redirect(url_for(path))


# HT's code ends


# SYH part


@app.route('/s_marks', methods=['GET', 'POST'])
def s_mark():
    if 'username' not in session:
        return render_template('login.html')
    elif session['username'][1] == 2:
        return render_template('i_index.html')

    user = returnUserByUsername(session['username'][0])
    marks = returnStudentMarkBySid(user['id'])

    if request.method == 'POST':
        mid = request.form['mid']
        desc = request.form['DESC']
        desc = desc.strip()

        if mid == "" or desc == "":
            return render_template('s_marks.html', marks=marks, message="Please fill in description before you submit.")

        if '\'' in desc :
            return render_template('s_marks.html', marks=marks, message="Input contains single quotes, please try "
                                                                        "again.")

        insertRemark(mid, desc)

        return render_template('s_marks.html', marks=marks, message="Successfully submitted!")
    return render_template('s_marks.html', marks=marks, message="")


@app.route('/i_marks', methods=['GET', 'POST'])
def i_mark():
    if 'username' not in session:
        return render_template('login.html')
    elif session['username'][1] == 1:
        return render_template('s_index.html')

    user = returnUserByUsername(session['username'][0])
    marks = returnAllMarks()

    if request.method == 'POST':
        sid = request.form['SID']
        item = request.form['ITEM']
        score = request.form['SCORE']
        mid = request.form['MID']

        if (sid == "" or item == "" or score == "") and mid != "":
            return render_template('i_marks.html', marks=marks, message="Successfully Deleted")
        if sid == "" or item == "" or score == "":
            return render_template('i_marks.html', marks=marks, message="Please fill in all blanks before you submit.")
        elif sidExists(sid)['RESULT'] == 0:
            return render_template('i_marks.html', marks=marks, message="Student doesn't exist, please try again.")
        elif int(score) < 0 or int(score) > 100:
            return render_template('i_marks.html', marks=marks, message="Score must be between 0 and 100, please try "
                                                                        "again.")
        else:
            mid = markExists(sid, item)
            if mid != -1:
                updateMarkByMid(mid, score)
                return render_template('i_marks.html', marks=marks, message="Successfully updated!")
            else:
                insertNewMark(sid, item, score)
                return render_template('i_marks.html', marks=marks, message="Successfully submitted!")

    else:
        return render_template('i_marks.html', marks=marks, message="")


@app.route('/i_remarks', methods=["GET"])
def i_remarks():
    if 'username' not in session:
        return render_template('login.html')
    elif session['username'][1] == 1:
        return render_template('s_index.html')

    user = returnUserByUsername(session['username'][0])
    marks = returnAllMarks()
    remarks = returnAllRemarks()

    return render_template('i_remarks.html', marks=marks, remarks=remarks, message="")


if __name__ == "__main__":
    app.run(debug=True)
