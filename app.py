import functools

from flask import Flask, request, render_template, redirect, session
from redis import StrictRedis
import hashlib

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'lkasjflasjdfzxcnvmn'
})

redis_client = StrictRedis(decode_responses=True)


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')

        return f(*args, **kwargs)

    return wrapper


@app.route('/')
@login_required
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


@app.route('/api/story', methods=['POST'])
@login_required
def create_story():
    pass


@app.route('/api/stories', methods=['POST'])
@login_required
def get_stories():
    user = session.get('user')
    return redis_client.lrange('users:%s:stories' % user.get('name'), 0, -1)


if __name__ == '__main__':
    app.run(debug=True)
