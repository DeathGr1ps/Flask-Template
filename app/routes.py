from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateListForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, List, Item
from werkzeug.urls import url_parse
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # Gets all of the lists which the user has created and lists them
    userListNames = returnuserlists()

    # Form for creating new list
    form = CreateListForm()
    if form.validate_on_submit():
        newlist = List(listname = form.listname.data, user_id=current_user.id)
        db.session.add(newlist)
        db.session.commit()
        flash('Created New List!')
        return redirect(url_for('index'))#Have to change this for AJAXian, In thoery should redirect to "select_list/<newlist>". Maybe I need to do an if method='post' then return an empty json and call something after this in the javascript function.

    return render_template('ToDo.html', title='ToDo.Com', listnames=userListNames, form=form)

def returnuserlists():
    user = User.query.filter_by(id=current_user.id).first()
    userLists = user.lists.all()
    return [i.listname for i in userLists]

@app.route('/create_list/', methods=['POST'])
@login_required
def create_list():
    newlistname = request.form['text'] #Gets the name for the new list from the post request.
    #print('This is the result of the query', List.query.filter_by(listname=newlistname, user_id=current_user.id).first())
    if List.query.filter_by(listname=newlistname, user_id=current_user.id).first(): #Checks to see if the name is in the system already (and under the ID that is trying to create the list)
        return jsonify({'listhtml': '', 'listoflists': '', 'isduplicatename': 'True'})
    else:
        newlist = List(listname=newlistname, user_id=current_user.id)
        db.session.add(newlist)
        db.session.commit()
        print(returnuserlists())
        return jsonify({'listhtml': '', 'listoflists': returnuserlists(), 'isduplicatename': 'False'}) #Currently return a blank list, leaving this open as an oppurtunity to change in the future for whatever reason

@app.route('/delete_list/', methods=['POST'])
@login_required
def delete_list():
    listtodelete = List.query.filter_by(listname=request.form['text']).first() #Converts from just the name into the SQLAlchemy list object
    
    #First delete all items in the list (to save database space)
    itemstodelete = Item.query.filter_by(list_id = listtodelete.id).all() #Forms list of all items in the list to be deleted
    for item in itemstodelete:  #delete each item
        db.session.delete(item)
    #Then delete the list itself
    db.session.delete(listtodelete) #Delete the list
    db.session.commit() #commit changes
    return jsonify({'successful':'True', 'listoflists': returnuserlists()})

@app.route('/select_list/', methods=['POST'])
@login_required
def get_formatted_list():
    listname = request.form['text']
    itemlist = select_list(listname)
    print(itemlist)
    outputhtml = list_html(itemlist)
    return jsonify({'listhtml': outputhtml})

#Retrieves unformatted items from a list
def select_list(listname):      #This is AJAX Shit dunno how to do
    selectedlist = List.query.filter_by(listname = listname).first()
    listItems = selectedlist.items.all()
    itemList = [(item.itemname, item.completion_status) for item in listItems]  #Froms a list of tuples. Tuple[0] = name, Tuple[1] = status
    return itemList

def list_html(itemlist):
    outputhtml = '<ul>'
    for item in itemlist:
        htmlstring = f"<li class='{item[1]}'> {item[0]} </li>"
        outputhtml += htmlstring
    outputhtml += '</ul>'
    return outputhtml
    
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