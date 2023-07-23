from pprint import pprint
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
import requests
import flask
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('git_req'))
    else:
        return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('git_req'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('git_req'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('git_req'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already taken')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/git_req', methods=['GET', 'POST'])
def git_req():
    if current_user.is_authenticated:
        if request.method == 'POST':
            git_hub_username = request.form['git_hyb_username']
            git_hub_rep = request.form['git_hyb_rep']
            git_hub_request = request.form.get('TypeGitRequest')
            # username = "natkaida"
            # repository = "flask_projects"

            # url to request
            git_link = f"https://api.github.com/repos/{git_hub_username}/{git_hub_rep}"
            # make the request and return the json
            user_data = requests.get(git_link).json()
            # print(user_data)
            if user_data.get('message') == 'Not Found':
                flash('Такой репозиторий не был найден :(')
            else:
                # pretty print JSON data
                # pprint(user_data)
                with open('buff.txt', 'w') as f:
                    f.write(git_hub_username + " ")
                    f.write(git_hub_rep + " ")
                    f.write(str(git_hub_request))
                return redirect(url_for('info_about_rep'))

        return render_template('git_req.html')
    else:
        return redirect(url_for('login'))


@app.route('/info_about_rep')
def info_about_rep():
    if current_user.is_authenticated:
        with open('buff.txt', 'r') as f:
            a = f.read().split(" ")
        git_hub_username = a[0]
        git_hub_rep = a[1]
        git_hub_request = a[2]
        link = ""
        if git_hub_request == "get_rep_det":
            link = f"repos/{git_hub_username}/{git_hub_rep}"
        elif git_hub_request == "get_all_pull":
            link = f'repos/{git_hub_username}/{git_hub_rep}/pulls?state=all'
        elif git_hub_request == "get_list_2_week":
            days = datetime.timedelta(days=14)
            today = datetime.datetime.today()
            date = (today - days).strftime("%Y-%m-%d")
            link = f'search/issues?q=is:pr+is:unmerged+created:<={date}+repo:{git_hub_username}/{git_hub_rep}'
        elif git_hub_request == "get_all_issues":
            link = f"repos/{git_hub_username}/{git_hub_rep}/issues"
        elif git_hub_request == "get_all_forks":
            link = f"repos/{git_hub_username}/{git_hub_rep}/forks"
        reply = requests.get(f'https://api.github.com/' + link).json()
        # pprint(reply)

        return render_template('info_about_rep.html', reply=reply)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
