from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm
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
    return render_template('ToDo.html', title='ToDo.Com', listnames=userListNames)

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

@app.route('/create_item/', methods=['POST'])
@login_required
def create_item():
    newitemname = request.form['itemname'] #Gets the name for the new list from the post request.
    parentlist = List.query.filter_by(listname = request.form['parentlist']).first() #Gets the list object of the parent
    print(newitemname)
    print(parentlist)

    print('This is the result of the query', List.query.filter_by(listname=newitemname, user_id=current_user.id).first())
    if Item.query.filter_by(itemname=newitemname, list_id=parentlist.id).first(): #Checks to see if the name is in the system already (and under the ID that is trying to create the list)
        return jsonify({'isduplicatename': 'True'}) #CHANGE THIS RETURN STATEMENT
    else:
        newitem = Item(itemname=newitemname, user_id=current_user.id, list_id=parentlist.id)
        db.session.add(newitem)
        db.session.commit()
        outhtml = get_formatted_list(request.form['parentlist'])  #Runs the function to get the raw html for the list
        return jsonify({'isduplicatename': 'False', 'listhtml': outhtml}) #Only need to return the duplicate status, JS side already has a function for reloading the list of items

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

@app.route('/delete_item/', methods=['POST'])
@login_required
def delete_item():
    itemtodelete = Item.query.filter_by(itemname=request.form['itemtobedeleted'],   #Has the name we looking for
                                        list_id=List.query.filter_by(listname = request.form['parentlist']).first().id).first() #On the list we are on
    db.session.delete(itemtodelete) #Delete the item
    db.session.commit() #commit changes
    itemlist = get_formatted_list(request.form['parentlist'])
    return jsonify({'successful':'True', 'listhtml': itemlist})

@app.route('/item_class/', methods=['POST'])
@login_required
def change_item_class():
    itemtochanged = Item.query.filter_by(itemname=request.form['itemtobechanged'],   #Has the name we looking for
                                        list_id=List.query.filter_by(listname = request.form['parentlist']).first().id).first() #On the list we are on
    itemtochanged.completion_status = request.form['newstatus'] #Changes the current completion status
    db.session.commit() #commit changes
    return jsonify({'successful':'True'})   #Dont need to reload anything

@app.route('/select_list/', methods=['POST'])
@login_required
def select_list_jsonifier():
    return jsonify({'listhtml': get_formatted_list(request.form['text'])})

def get_formatted_list(listname):
    itemlist = select_list(listname)
    outputhtml = list_html(itemlist)
    return outputhtml

#Retrieves unformatted items from a list
def select_list(listname):      #This is AJAX Shit dunno how to do
    selectedlist = List.query.filter_by(listname = listname).first()
    listItems = selectedlist.items.all()
    itemList = [(item.itemname, item.completion_status) for item in listItems]  #Froms a list of tuples. Tuple[0] = name, Tuple[1] = status
    return itemList

def list_html(itemlist):
    outputhtml = ''
    for item in itemlist:
        newhtmlstring = f"""<div class="row" style="margin-top: 0.2em; margin-left 0.5em;">
        <div class='{item[1]} col-md-12' id='{item[0]}'> {item[0]} 
        <div class='btn-group pull-right' role='group'>
  <a href='javascript:change_item_status(\"{item[0]}\", \"NotStarted\")' class='btn btn-info'>Not Started</a>
  <a href='javascript:change_item_status(\"{item[0]}\", \"InProgress\")' class='btn btn-warning'>In Progress</a>
  <a href='javascript:change_item_status(\"{item[0]}\", \"Completed\")' class='btn btn-success'>Completed</a>
  <a href='javascript:delete_item(\"{item[0]}\")' class='btn btn-danger'>Delete</a>
</div></div></div>"""
        htmlstring = f"<li class='{item[1]}' id='{item[0]}'> {item[0]} <a href='javascript:change_item_status(\"{item[0]}\", \"Not Started\")' style='opacity: 0.5;'> N </a> <a href='javascript:change_item_status(\"{item[0]}\", \"In Progress\")' style='opacity: 0.5;'> P </a>  <a href='javascript:change_item_status(\"{item[0]}\", \"Completed\")' style='opacity: 0.5;'> C </a> <a href='javascript:delete_item(\"{item[0]}\")' style='opacity: 0.5;'>X</a></li>"
        outputhtml += newhtmlstring
    outputhtml += ''
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