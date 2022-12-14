from flask import Flask, render_template, request, session, url_for, redirect, flash

import pymysql, logging, json

# from flask_bcrypt import Bcrypt

import bcrypt
try:
    from werkzeug.utils import secure_filename
except:
    from werkzeug import secure_filename


app = Flask(__name__)
app.secret_key = 'abcdefg'

db = pymysql.connect(host = 'localhost',
                     port = 3306,
                     user = 'root',
                     passwd = '1234',
                     db = 'mapaltofu',
                     charset = 'utf8')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #파일 업로드 용량 제한 단위:바이트 (현재 16메가 세팅)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:Guswl1219@localhost:3306/mapaltofu"
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']

# cursor = db.cursor(pymysql.cursors.DictCursor)
cursor = db.cursor()

@app.route('/feed', methods=['GET'])
def get_feed():
    sql = """
    select * from feed as f left join `user` as u on f.user_id = u.id
    """
    cursor.execute(sql)
    rows = cursor.fetchall() # 피드에있는 데이터를 다 가져온다
    json_str = json.dumps(rows, indent=4, sort_keys=True, default=str) # json포맷으로 변환
    db.commit()
    return json_str, 200


# 로그 생성
logger_info = logging.getLogger(' ')
logger_error = logging.getLogger(' ')
# 로그의 출력 기준 설정
logger_info.setLevel(logging.INFO)
logger_error.setLevel(logging.ERROR)

# log 출력 형식 ( '%(asctime)s - %(name)s - %(levelname)s - %(message)s' )
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger_info.addHandler(stream_handler)
logger_error.addHandler(stream_handler)

# log를 파일에 출력
file_handler = logging.FileHandler('my.log')
file_handler.setFormatter(formatter)
logger_info.addHandler(file_handler)
logger_error.addHandler(file_handler)

##################################

##################################

@app.route('/')
def main():
    if 'login_id' in session:
        user_id = session['login_id']
        login_name = session['login_name']

        return render_template('main.html', logininfo=user_id, loginName=login_name)
    else:
        user_id = None
        return render_template('main.html', logininfo=user_id)


@app.route('/login_try')
def login_try():
    return render_template("login_try.html")


# @app.route('/write')
# def write():
#     return render_template('write.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['login_id']
        user_pw = request.form['login_pw']

        cursor = db.cursor()
        sql = "SELECT * FROM `user` where login_id = %s"
        cursor.execute(sql, user_id)
        data = cursor.fetchall()

        for row in data:
            pk_id = row[0]
            db_pw = row[3]
            login_name = row[2]
            print(row)
            print(pk_id)

        if data:
            if bcrypt.checkpw(user_pw.encode('utf-8'), db_pw.encode('utf-8')):
                session['pk_id'] = pk_id
                session['login_id'] = user_id
                session['login_name'] = login_name
                print(session['pk_id'])
                logger_info.info(f'login Success')
                return render_template('main.html', logininfo=user_id, loginName=login_name, pkId = pk_id )

            else:
                logger_error.error(f'login Fail : None Data')
                return render_template('login_error.html')
        else:
            logger_error.error(f'login Fail : None Data')
            logger_info.error(f'login Fail : None Data')
            return render_template('login_error.html')
    else:
        logger_error.error(f'login Fail : Request Method == Not POST')
        return render_template('login_error.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['register_id']

        user_pw = request.form['register_pw']
        input_bcrypt = bcrypt.hashpw(user_pw.encode('utf-8'), bcrypt.gensalt())
        input_decode = input_bcrypt.decode('utf-8')

        user_name = request.form['register_name']
        user_email = request.form['register_email']

        cursor = db.cursor()

        sql = "select * from `user` where login_id = %s and email = %s"
        value = (user_id, user_email)
        cursor.execute(sql, value)
        data = (cursor.fetchall())

        if data:
            return render_template('register.html')
        else:
            sql = "insert into `user` (login_id, pw, name, email) values (%s,%s,%s,%s)"
            value = (user_id, input_decode, user_name, user_email)
            cursor.execute(sql, value)
            cursor.fetchall()
            db.commit()
            # db.close()
            logger_info.info(f'register Success')
            return render_template('main.html')
    else:
        return render_template('register.html')

@app.route('/user_edit', methods=['GET', 'POST'])
def user_edit():
    if request.method == 'POST':
        if 'login_id' in session:
            login_id = session['login_id']

            edit_name = request.form['edit_name']
            edit_pw = request.form['edit_pw']
            input_bcrypt = bcrypt.hashpw(edit_pw.encode('utf-8'), bcrypt.gensalt())
            input_decode = input_bcrypt.decode('utf-8')

            edit_email = request.form['edit_email']

            cursor = db.cursor()
            sql = "update `user` set name = %s, pw = %s, email = %s where login_id = %s"
            value = (edit_name, input_decode, edit_email, login_id)

            cursor.execute(sql, value)

            session['login_id'] = login_id

            db.commit()

            logger_info.info(f'user Info Update Success')
            return render_template('edit_success.html', logininfo=login_id )
        else:
            logger_error.error(f'user Info Update : None Data')
            return render_template('login_error.html')
    else:
        return render_template('user_edit.html')


@app.route('/mypage')
def mypage():
    if 'login_id' in session:
        user_id = session['login_id']
        login_name = session['login_name']
        return render_template('mypage.html', logininfo=user_id, loginName=login_name)

@app.route("/api/mypage", methods=['GET'])
def mypages():
    if request.method == "GET":
        # curs = db.cursor()
        # 여기 foreign key 방식으로 다시 써야됨!!!!
        sql = """
        select * 
        from feed as f
        LEFT JOIN `user` as u
        ON f.user_id = u.id
        """
        cursor.execute(sql)
        rows = cursor.fetchall()


        json_str = json.dumps(rows, indent=4, sort_keys=True, default=str)
        db.commit()
        # db.close()
        return json_str, 200


@app.route('/edit_success')
def edit_success():
    return render_template('edit_success.html')



@app.route("/modify")
def modify_feed():
    if 'login_id' in session:
        user_id = session['login_id']
        login_name = session['login_name']
        return render_template('modify.html', logininfo=user_id, loginName=login_name)

@app.route("/api/modify", methods=['POST'])
def edit_feed():
    if request.method == "POST":
        feed_id = request.form['id']
        title = request.form['title']
        description = request.form['description']

        sql = """
                    UPDATE feed
                    SET title = %s,
                     description = %s
                     WHERE id = %s;
                    """

        value = (title, description, feed_id)

        cursor.execute(sql, value)

        db.commit()

        return json.dumps('post modified successfully!')


@app.route('/feed_page')
def feed_pages():
    if 'login_id' in session:
        user_id = session['login_id']
        login_name = session['login_name']

        return render_template('feed_page.html', logininfo = user_id, loginName=login_name)
    else:
        return render_template('feed_page.html')


@app.route("/feed_page/<login_id>/<id>", methods=["GET"])
def feed_page(login_id, id):

    sql = """
    select * 
    from feed as f
    LEFT JOIN `user` as u
    ON f.user_id = u.id
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    json_str = json.dumps(rows, indent=4, sort_keys=True, default=str)
    db.commit()
    return json_str, 200

@app.route("/api/delete", methods=['POST'])
def delete_feed():
    if request.method == "POST":
        feed_id = request.form['id']
        sql = """
                       DELETE FROM feed WHERE id = %s;
                                   """

        value = feed_id
        cursor.execute(sql, value)

        db.commit()
        logger_info.info(f'user feed delete Success')
        return json.dumps('post deleted successfully!')

@app.route('/write_success')
def write_success():
    if'login_id' in session:
        user_id = session['login_id']
        return render_template('write_success.html', logininfo=user_id)


@app.route('/write', methods=['GET','POST'])
def write():
    if request.method == 'POST':
        if 'login_name' in session:
            title = request.form['title']
            description = request.form['description']
            file = request.files['file']
            pk_id = session['pk_id']
            file.save('./static/images/' + secure_filename(file.filename))
            image = './static/images/' + file.filename
            sql = "insert into feed(title, description, image, user_id) values (%s, %s, %s, %s)"
            value = (title, description, image, pk_id)
            cursor.execute(sql, value)
            db.commit()

            logger_info.info(f'feed write Success')
            return redirect(url_for('write_success'))
        else:
            logger_error.error(f'feed write Fail : None session')
            return render_template('login_error.html')
    else:
        if 'login_name' in session:
            login_id = session['login_id']
            login_name = session['login_name']
            return render_template('write.html', logininfo=login_id, loginName=login_name)
        else:
            logger_error.error(f'feed write Fail : Request Method == Not POST')
            return render_template('main.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)


