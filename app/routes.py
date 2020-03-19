from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateListForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, List
from werkzeug.urls import url_parse
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # Gets all of the lists which the user has created and lists them
    user = User.query.filter_by(id=current_user.id).first()
    userLists = user.lists.all()
    userListNames = [i.listname for i in userLists]

    # Form for creating new list
    form = CreateListForm()
    if form.validate_on_submit():
        newlist = List(listname = form.listname.data, user_id=current_user.id)
        db.session.add(newlist)
        db.session.commit()
        flash('Created New List!')
        return redirect(url_for('index'))#Have to change this for AJAXian, In thoery should redirect to "select_list/<newlist>"

    return render_template('ToDo.html', title='shit', listnames=userListNames, form=form)

@app.route('/select_list/', methods=['POST'])
@login_required
def get_formatted_list():
    listname = request.form['text']
    itemlist = select_list(listname)
    print('itemlist worked')
    print(itemlist)
    outputhtml = '<ul>'
    for item in itemlist:
        htmlstring = f"<li class='{item[1]}'> {item[0]} </li>"
        outputhtml += htmlstring
    outputhtml += '</ul>'
    print('Backend worked')
    return jsonify({'listhtml': outputhtml})

#Retrieves unformatted items from a list
def select_list(listname):      #This is AJAX Shit dunno how to do
    selectedlist = List.query.filter_by(listname = listname).first()
    listItems = selectedlist.items.all()
    itemList = [(item.itemname, item.completion_status) for item in listItems]  #Froms a list of tuples. Tuple[0] = name, Tuple[1] = status
    return itemList
    
    #for item in listItems: #HERE
        #{'Name': item.itemname, "Status": item.completion_status}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)