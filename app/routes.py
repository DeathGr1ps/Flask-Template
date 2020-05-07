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
def index():    #Main Webpage
    # Gets all of the lists which the user has created and lists them
    userListNames = returnuserlists()
    return render_template('ToDo.html', title='ToDo.Com', listnames=userListNames)

def returnuserlists():  #Function for returning all lists associated with the currently logged in user
    user = User.query.filter_by(id=current_user.id).first()
    userLists = user.lists.all()
    return [i.listname for i in userLists]

#All methods which require database entry / modification are handeled through POST requests from the browser
@app.route('/create_list/', methods=['POST'])   #Creates a list
@login_required
def create_list():
    newlistname = request.form['text'] #Gets the name for the new list from the post request.
    if List.query.filter_by(listname=newlistname, user_id=current_user.id).first(): #Checks to see if the name is in the system already (and under the ID that is trying to create the list)
        return jsonify({'listhtml': '', 'listoflists': '', 'isduplicatename': 'True'})
    else:
        newlist = List(listname=newlistname, user_id=current_user.id)   #Creates the List object and adds to the database
        db.session.add(newlist)
        db.session.commit()
        print(returnuserlists())
        return jsonify({'listhtml': '', 'listoflists': returnuserlists(), 'isduplicatename': 'False'}) #Currently return a blank list, leaving this open as an oppurtunity to change in the future for whatever reason

@app.route('/create_item/', methods=['POST'])       #Creates an item
@login_required
def create_item():
    newitemname = request.form['itemname'] #Gets the name for the new list from the post request.
    parentlist = List.query.filter_by(listname = request.form['parentlist']).first() #Gets the list object of the parent
    if Item.query.filter_by(itemname=newitemname, list_id=parentlist.id).first(): #Checks to see if the name is in the system already (and under the ID that is trying to create the list)
        return jsonify({'isduplicatename': 'True'})
    else:
        newitem = Item(itemname=newitemname, user_id=current_user.id, list_id=parentlist.id)    #Creates the Item object and adds to the database
        db.session.add(newitem)
        db.session.commit()
        outhtml, itemtimes = get_formatted_list(request.form['parentlist'])  #Runs the function to get the raw html for the list
        return jsonify({'isduplicatename': 'False', 'listhtml': outhtml, 'itemtimes': itemtimes}) #Only need to return the duplicate status, JS side already has a function for reloading the list of items

@app.route('/delete_list/', methods=['POST'])       #Deletes a list
@login_required
def delete_list():
    listtodelete = List.query.filter_by(listname=request.form['text']).first() #Converts from just the name into the SQLAlchemy list object
    #First delete all items in the list (to save database space)
    itemstodelete = Item.query.filter_by(list_id = listtodelete.id).all() #Forms list of all items in the list to be deleted
    for item in itemstodelete:  #Delete each item
        db.session.delete(item)
    #Then delete the list itself
    db.session.delete(listtodelete) #Delete the list
    db.session.commit() #Commit changes
    return jsonify({'successful':'True', 'listoflists': returnuserlists()})

@app.route('/delete_item/', methods=['POST'])   #Deletes an item. Simpler version of deleting a list
@login_required
def delete_item():
    #Find the item that:
    itemtodelete = Item.query.filter_by(itemname=request.form['itemtobedeleted'],   #Has the name we looking for
                                        list_id=List.query.filter_by(listname = request.form['parentlist']).first().id).first() #Is on the list we are on
    db.session.delete(itemtodelete) #Delete the item
    db.session.commit() #Commit changes
    itemlist, itemtimes = get_formatted_list(request.form['parentlist'])
    return jsonify({'successful':'True', 'listhtml': itemlist, 'itemtimes': itemtimes})

@app.route('/item_class/', methods=['POST'])    #Method for changing an items class (as listed in the database)
@login_required
def change_item_class():
    timetosend=None
    #Find the item that:
    itemtochanged = Item.query.filter_by(itemname=request.form['itemtobechanged'],   #Has the name we looking for
                                        list_id=List.query.filter_by(listname = request.form['parentlist']).first().id).first() #On the list we are on
    itemtochanged.completion_status = request.form['newstatus'] #Changes the current completion status
    if request.form['newstatus'] == 'Completed':
        itemtochanged.completion_time = datetime.now()
    else:   #This acts as a reset for if the item goes from completed to uncompleted
        itemtochanged.completion_time = None
    db.session.commit() #Commit changes
    print(itemtochanged.completion_time)
    return jsonify({'successful':'True', 'timecompleted': itemtochanged.completion_time})   #Dont need to reload anything; all handled through CSS.

@app.route('/select_list/', methods=['POST'])   #Returns the html for items in a list (when a list is selected)
@login_required
def select_list_jsonifier():
    formatted_list, itemtimes = get_formatted_list(request.form['text'])
    return jsonify({'listhtml': formatted_list, 'itemtimes': itemtimes})

def get_formatted_list(listname):   #Kept seperate from list selection to be called to update list when an item is added or removed
    itemlist = select_list(listname)
    outputhtml = list_html(itemlist)
    itemtimes=[]
    for item in itemlist:
        if item[2] != None:
            itemtimes.append((item[0], item[2]))#Newlist that stores pairs of values of datetime completion times and the associated item
    print(itemtimes)
    return outputhtml, itemtimes

def select_list(listname):  #Retrieves the data pertaining to the items in a given list
    selectedlist = List.query.filter_by(listname = listname).first()
    listItems = selectedlist.items.all()
    itemList = [(item.itemname, item.completion_status, item.completion_time) for item in listItems]  #Froms a list of tuples. Tuple[0] = name, Tuple[1] = status
    return itemList

def list_html(itemlist):    #Kept seperate from list selection to be called to update listoflists when an List is added or removed
    outputhtml = ''
    for item in itemlist:   #Creates html code for each item in a list
        newhtmlstring = f"""<div class="row {item[1]}" style="margin-top: 0.2em; margin-left 0.5em;">
                                <div class='classname col-xs-3' id='{item[0]}'> {item[0]}
                                </div>
                                <div id = "{item[0]}timecompleted" class="col-xs-2 timecompleted"></div>
                                <div class="pull-right col-xs-7">
                                    <div class='btn-group pull-right' role='group'>
                                    
                                        <a href='javascript:change_item_status(\"{item[0]}\", \"NotStarted\")' class='btn btn-info'>Not Started</a>
                                        <a href='javascript:change_item_status(\"{item[0]}\", \"InProgress\")' class='btn btn-warning'>In Progress</a>
                                        <a href='javascript:change_item_status(\"{item[0]}\", \"Completed\")' class='btn btn-success'>Completed</a>
                                        <a href='javascript:delete_item(\"{item[0]}\")' class='btn btn-danger'>Delete</a>
                                    </div>
                                </div>
                            </div>"""
        outputhtml += newhtmlstring
    outputhtml += ''
    return outputhtml

@app.route('/login', methods=['GET', 'POST'])   #Login route
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

@app.route('/logout')   #Logout Route
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])    #Register Route
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