import functools
import json

from flask import Flask, request, render_template, redirect, session, flash
from redis import StrictRedis
import hashlib
from datetime import datetime

from qiniu import Auth, put_data
import uuid

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'lkasjflasjdfzxcnvmn'
})

#需要填写你的 Access Key 和 Secret Key
access_key = '1H3USr1wF7hQ80AeRlq_BF0KoEnoJq2atE4UULwp'
secret_key = 'awFedibl6FB3L-4FSXG1NY4Qq3MFwiDoZcNFDKTF'

#构建鉴权对象
q = Auth(access_key, secret_key)
bucket_name = 'bohan'

redis_client = StrictRedis(decode_responses=True)


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')

        return f(*args, **kwargs)

    return wrapper


@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/stories')
@login_required
def stories():
    return render_template('stories.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form['username']
    password = request.form['password']
    md5 = hashlib.md5()
    md5.update(password.encode())
    encoded_password = str(md5.hexdigest())

    user = redis_client.hgetall('users:' + username)
    if not user:
        redis_client.hmset('users:' + username, {
            'password': encoded_password,
            'username': username,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        flash('注册成功!', category='success')
        return redirect('/login')
    else:
        flash('用户名已存在!', category='error')
        return render_template('register.html')


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
        redis_client.hset('users:' + username, 'updated_at', datetime.now().isoformat())

        session['user'] = user
        flash('登录成功!', category='success')
        return redirect('/')
    else:
        flash('用户名或密码错误!', category='error')
        return render_template('login.html')


@app.route('/story', methods=['GET', 'POST'])
@login_required
def create_story():
    user = session.get('user')

    if request.method == 'POST':
        description = request.form.get('description')
        f = request.files['file']
        # upload file to qiniu
        key = str(uuid.uuid4()) + '.jpg'
        token = q.upload_token(bucket_name, key, 3600)
        ret, info = put_data(token, key, f)
        print(ret, info)
        url = 'http://7d9pyw.com1.z0.glb.clouddn.com/' + key

        story_id = redis_client.incr('users:%s:stories:next-id' % user.get('username'))
        redis_client.hmset('users:%s:stories:%s' % (user.get('username'), story_id), {
            'url': url,
            'description': description,
            'created_at': datetime.now().isoformat()
        })
        redis_client.rpush('users:%s:stories' % user.get('username'), story_id)
        flash('上传成功!', category='success')
        return redirect('/stories')
    else:
        return render_template('create_story.html')


@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    page = int(request.args.get('page', 1))
    size = 10

    user = session.get('user')
    story_ids = redis_client.lrange('users:%s:stories' % user.get('username'), (page - 1) * size, page * size)
    stories = []
    for story_id in story_ids:
        story = redis_client.hgetall('users:%s:stories:%s' % (user.get('username'), story_id))
        stories.append(story)

    return json.dumps(stories)


if __name__ == '__main__':
    app.run(debug=True)
