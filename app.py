from flask import Flask, request, render_template, redirect, session
from redis import StrictRedis
import hashlib

app = Flask(__name__)
app.config.update({'SECRET_KEY': 'lkasjflasjdfzxcnvmn'})

redis_client = StrictRedis(decode_responses=True)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    md5 = hashlib.md5()
    md5.update(password.encode())
    encoded_password = str(md5.hexdigest())

    user = redis_client.hgetall('users:' + username)
    if user and encoded_password == user.get('password'):
        session['user'] = user
        return redirect('/')
    else:
        return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
