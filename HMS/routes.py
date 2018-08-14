import os
import secrets
from PIL import *
from flask import render_template, url_for, flash, redirect, request, abort
from HMS import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from HMS.models import User, Hostel, Payment, Room, Beds, Images, Announcement
from HMS.static.tourcontent import tourContent
from HMS.static.reportContent import reportContent
from HMS.forms import SignupForm, LoginForm, AnnouncementForm, AddRoomForm, EditRoomForm, \
    UpdateAccountForm, EditRoomPricingForm, AdminAddPaymentForm, ChangePasswordForm, EditHostelDetailsForm, \
    StudentPaymentForm
from HMS.tables import TotalRoomReport, TotalStudentsReport, TotalFullPaidStudentsReport


@app.route("/")
@app.route("/home")
def home():
    return render_template('Home.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.role == "student":
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('student'))
                else:
                    flash('Login Unsuccessful. Please check email and password', 'danger')
            if user.role == "admin":
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('admin'))
                else:
                    flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(firstname=form.firstname.data, lastname=form.lastname.data, email=form.email.data,
                    number=form.number.data, gender=form.gender.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Sign Up', form=form)


@app.route("/about")
def about():
    return render_template('about.html', title="About")


@app.route("/tour")
def tour():
    return render_template('tour.html', title="Take A Tour", tourContent=tourContent)


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role == 'admin':
        hostel = Hostel.query.filter_by(hostel_id=current_user.hostel_id).first()
        hostelName = hostel.hostel_name
        totalNumOfRooms = len(hostel.rooms)
        totalNumofStudents = 0
        totalNumOfMales = 0
        totalNumOfFemales = 0
        totalNumofFullyPaid = 0

        for student in hostel.occupants:
            if student.room_id != None:
                totalNumofStudents += 1
            if student.gender == 'M' and student.room_id != None:
                totalNumOfMales += 1
            elif student.gender == 'F' and student.room_id != None:
                totalNumOfFemales += 1

        fullyOccupiedRooms = 0
        occupied_rooms = db.engine.execute(
            "Select * from rooms where rooms.beds = (select count(*) from Users where users.room_id == rooms.room_num) and rooms.hostel_id == " + str(
                hostel.hostel_id))
        for room in occupied_rooms:
            fullyOccupiedRooms += 1

        for payment in Payment.query.all():
            if payment.amount_remaining == 0:
                totalNumofFullyPaid += 1

        return render_template('admin_home.html', hostelName=hostelName, totalNumOfRooms=totalNumOfRooms,
                               totalNumofStudents=totalNumofStudents, fullyOccupiedRooms=fullyOccupiedRooms,
                               totalNumOfFemales=totalNumOfFemales,
                               totalNumOfMales=totalNumOfMales, totalNumofFullyPaid=totalNumofFullyPaid)
    else:
        return render_template('logInError.html')


@app.route("/admin/addroom", methods=['GET', 'POST'])
@login_required
def addroom():
    if current_user.role == 'admin':
        form = AddRoomForm()

        if form.validate_on_submit():
            room_num = form.room_num.data
            beds = form.beds.data
            hostel_id = current_user.hostel_id
            hostel_name = Hostel.query.filter_by(hostel_id=hostel_id).first()
            hostel_name = hostel_name.hostel_name.lower()
            bed = f'{hostel_name}{beds}'
            spec_bed = Beds.query.filter_by(beds_id=bed).first()
            price = spec_bed.price
            room_gen = form.gender.data
            room = Room(room_num=room_num, beds=beds, price=price, hostel_id=current_user.hostel_id, room_gen= room_gen)
            db.session.add(room)
            db.session.commit()
            flash('Room successfully added', 'success')
            return redirect(url_for('addroom'))

        return render_template('addroom.html', title='Add Room',
                               form=form, legend='Add New Room')
    else:
        return render_template('logInError.html')


@app.route("/admin/occupants_details", methods=['GET', 'POST'])
@login_required
def occupants_details():
    if current_user.role == 'admin':

        hostel = Hostel.query.filter_by(hostel_id=current_user.hostel_id).first()
        table = TotalStudentsReport(
            db.engine.execute("select * from Users where room_id not null and hostel_id == " + str(hostel.hostel_id)))
        return render_template('occupants_details.html', title='Occupants Details',
                               table=table)
    else:
        return render_template('logInError.html')


@app.route("/admin/viewrooms", methods=['GET'])
@login_required
def viewrooms():
    if current_user.role == 'admin':

        rooms = Room.query.filter_by(hostel_id=current_user.hostel_id).all()
        return render_template('view_rooms.html', rooms=rooms)
    else:
        return render_template('logInError.html')


@app.route("/admin/account", methods=['GET', 'POST'])
@login_required
def updateaccount():
    if current_user.role == 'admin':
        form = UpdateAccountForm()

        if form.validate_on_submit():
            current_user.firstname = form.firstname.data
            current_user.lastname = form.lastname.data
            current_user.number = form.number.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('updateaccount'))
        elif request.method == 'GET':
            form.firstname.data = current_user.firstname
            form.lastname.data = current_user.lastname
            form.number.data = current_user.number
            form.email.data = current_user.email
        return render_template('updateaccount.html', title='Account', form=form)

    else:
        return render_template('logInError.html')


@app.route('/admin/reports', methods=['GET', 'POST'])
@login_required
def reports():
    if current_user.role == 'admin':

        hostelName = Hostel.query.filter_by(hostel_id=current_user.hostel_id).first().hostel_name
        return render_template('reports.html', title='Reports', hostelName=hostelName, reportContent=reportContent)
    else:
        return render_template('logInError.html')


@app.route('/admin/reports/detailed_report/<string:id>', methods=['GET', 'POST'])
@login_required
def detailed_report(id):
    if current_user.role == 'admin':
        hostel = Hostel.query.filter_by(hostel_id=current_user.hostel_id).first()
        if (id == "totRooms"):
            table = TotalRoomReport(hostel.rooms)
            return render_template('detailed_reports.html', table=table)
        if (id == 'totStu'):
            table = TotalStudentsReport(db.engine.execute(
                "select * from Users where room_id not null and users.hostel_id == " + str(hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totStuPaid'):
            table = TotalFullPaidStudentsReport(db.engine.execute(
                "SELECT Users.firstname, Users.lastname,Users.email,Users.number,Payments.amount_paid,Payments.amount_remaining" +
                " FROM Users INNER JOIN Payments ON Payments.user_id = Users.id where Payments.amount_remaining <= 0 and Users.hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totNotFullPaid'):
            table = TotalFullPaidStudentsReport(db.engine.execute(
                "SELECT Users.firstname, Users.lastname,Users.email,Users.number,Payments.amount_paid,Payments.amount_remaining" +
                " FROM Users INNER JOIN Payments ON Payments.user_id = Users.id where Payments.amount_remaining > 0 and Users.hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totFullRooms'):
            table = TotalRoomReport(db.engine.execute(
                "Select * from rooms where rooms.beds = (select count(*) from Users where users.room_id == rooms.room_num) and rooms.hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totNotFullRooms'):
            table = TotalRoomReport(db.engine.execute(
                "Select * from rooms where rooms.beds != (select count(*) from Users where users.room_id == rooms.room_num) and rooms.hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totMaleStu'):
            table = TotalStudentsReport(db.engine.execute(
                "select * from Users where gender == 'M' and room_id not null and hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
        if (id == 'totFemStu'):
            table = TotalStudentsReport(db.engine.execute(
                "select * from Users where gender == 'F' and room_id not null and hostel_id == " + str(
                    hostel.hostel_id)))
            return render_template('detailed_reports.html', table=table)
    else:
        return render_template('logInError.html')


@app.route('/admin/viewrooms/room_details/<string:id>', methods=['GET', 'POST'])
@login_required
def default_roomview(id):
    if current_user.role == 'admin':

        room = Room.query.filter_by(room_num=id).first()
        table = TotalStudentsReport(room.occupants)
        return render_template('default_roomview.html', room=room, table=table)
    else:
        return render_template('logInError.html')


@app.route('/admin/viewrooms/room_details/<string:id>/update', methods=['GET', 'POST'])
@login_required
def room_details(id):
    global table
    if current_user.role == 'admin':

        form = EditRoomForm()
        room = Room.query.filter_by(room_num=id).first()
        hostel_id = current_user.hostel_id
        hostel_name = Hostel.query.filter_by(hostel_id=hostel_id).first()
        hostel_name = hostel_name.hostel_name.lower()

        if form.validate_on_submit():
            room.room_num = form.room_num.data
            room.beds = form.beds.data
            beds = room.beds
            bed = f'{hostel_name}{beds}'
            price = Beds.query.filter_by(beds_id=bed).first()
            room.price = price.price
            room_gen = form.gender.data
            room.room_gen = room_gen
            db.session.commit()
            form.room_num.data = room.room_num
            form.beds.data = int(room.beds)
            flash('Room Sucessfully Updated!', 'success')
            return redirect(url_for('room_details', id=room.room_num))
        elif request.method == 'GET':
            form.room_num.data = room.room_num
            form.beds.data = int(room.beds)
            form.gender.data = str(room.room_gen[0])
            table = TotalStudentsReport(room.occupants)
        return render_template('room_details.html', legend='Edit Room', form=form, table=table, room=room)
    else:
        return render_template('logInError.html')


@app.route('/admin/viewrooms/room_details/<string:id>/delete', methods=['POST'])
@login_required
def deleteroom(id):
    if current_user.role == 'admin':
        hostel_id = current_user.hostel_id
        room = Room.query.filter_by(room_num=id, hostel_id=hostel_id).first()
        return_url = request.referrer
        if len(room.occupants) > 0:
            flash('Room cannot be deleted. Check if room is empty', 'danger')
            return redirect(return_url)
        else:
            db.session.delete(room)
            db.session.commit()
            flash('Room has been deleted!', 'success')
            return redirect(url_for('viewrooms'))
    else:
        return render_template('logInError.html')


@app.route("/admin/editroompricing", methods=['GET', 'POST'])
@login_required
def editroompricing():
    if current_user.role == 'admin':
        form = EditRoomPricingForm()
        if form.validate_on_submit():
            beds = form.beds.data
            price = form.price.data
            hostel_id = current_user.hostel_id
            db.engine.execute("Update beds set price = " + str(price) + " where beds.bednum = " + str(
                beds) + " and beds.hostel_id = " + str(hostel_id))
            db.engine.execute(
                "Update rooms set price = " + str(price) + " where rooms.beds = " + str(
                    beds) + " and rooms.hostel_id = " + str(
                    hostel_id))
            flash('Room Pricing have been updated', 'success')
            return redirect(url_for('editroompricing'))

        return render_template('edit_roompricing.html', form=form, legend="Edit Room Pricing")
    else:
        return render_template('logInError.html')


@app.route('/admin/payments', methods=['GET', 'POST'])
@login_required
def payments():
    if current_user.role == 'admin':
        # page = request.args.get('page', 1, type=int)

        payment = Images.query.filter_by(processed="False").order_by(
            Images.date_posted.desc()).all()  # .paginate(page=page, per_page=6)
        return render_template('payments.html', payment=payment, User=User)
    else:
        return render_template('logInError.html')


@app.route('/admin/payments/<id>/input_payment', methods=['GET', 'POST'])
@login_required
def input_payment(id):
    if current_user.role == 'admin':
        form = AdminAddPaymentForm()
        image = Images.query.filter_by(image_id=id).first()
        student_id = image.user_id
        student = User.query.filter_by(id=student_id).first()
        room = Room.query.filter_by(room_num=student.room_id).first()
        room_price = room.price
        if form.validate_on_submit():
            if Payment.query.filter_by(user_id=student_id).order_by(Payment.payment_id.desc()).first():
                prev_amountremaining = Payment.query.filter_by(user_id=student_id).order_by(
                    Payment.payment_id.desc()).first()
                input = Payment(user_id=student_id, amount_paid=prev_amountremaining.amount_paid + form.price.data,
                                amount_remaining=prev_amountremaining.amount_remaining - form.price.data)
                db.session.add(input)
                db.session.delete(prev_amountremaining)
                image.processed = "True"
                db.session.commit()
                flash('Payment has been added', 'success')
                return redirect(url_for('payments', id=id))
            else:
                input = Payment(user_id=student_id, amount_paid=form.price.data,
                                amount_remaining=room_price - form.price.data)
                db.session.add(input)
                image.processed = "True"
                db.session.commit()
                flash('Payment has been added', 'success')
                return redirect(url_for('payments', id=id))

        return render_template('input_payments.html', form=form,
                               legend="Input Payment for " + student.firstname + " " + student.lastname)
    else:
        return render_template('logInError.html')


@app.route('/admin/changepassword', methods=['GET', 'POST'])
@login_required
def change_Adminpassword():
    if current_user.role == 'admin':

        form = ChangePasswordForm()
        user = User.query.filter_by(id=current_user.id).first()
        if request.method == 'POST':
            if form.validate_on_submit():
                if bcrypt.check_password_hash(user.password, form.current_password.data):
                    hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                    user.password = hashed_password
                    db.session.commit()
                    flash('Your password has been changed!', 'success')
                    return redirect(url_for('change_Adminpassword'))
                else:
                    flash('Current password might be wrong', 'danger')
                    return redirect(url_for('change_Adminpassword'))
        return render_template('change_Adminpassword.html', form=form, legend="Change Password")
    else:
        return render_template('logInError.html')


@app.route('/admin/edithosteldetails', methods=['GET', 'POST'])
@login_required
def edit_hostelDetails():
    if current_user.role == 'admin':
        form = EditHostelDetailsForm()
        hostel = Hostel.query.filter_by(hostel_id=current_user.hostel_id).first()
        if request.method == 'GET':

            hostel_details = hostel.desc
            form.description.data = hostel_details

        if request.method == 'POST':
            if form.validate_on_submit():
                hostel.desc = form.description.data
                db.session.commit()
                flash('Hostel description has been updated', 'success')
                return redirect(url_for('edit_hostelDetails'))
            else:
                flash('Failed validation','danger')
        return render_template('edit_hostelDetails.html', form=form, legend='Edit Hostel Details')
    else:
        return render_template('logInError.html')


@app.route('/admin/announcements', methods=['GET','POST'])
@login_required
def admin_announce():
    form = AnnouncementForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_announce = Announcement(subject=form.subject.data, message=form.message.data, user_id=current_user.id)
            db.session.add(new_announce)
            db.session.commit()
        # db.engine.execute(
        #     "insert into announcements subject, message, user_id values (" +
        #     form2.subject.data + "," + form2.message.data + "," + current_user.id + ")")
            flash('Announcement has been made', 'success')
            return redirect(url_for('admin_announce'))
    return render_template('admin_announce.html', form2=form)


@app.route("/student")
@login_required
def student():
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        if user.hostel_id == None and user.room_id == None:
            return render_template('firsttimehostelview.html', hostels=tourContent, user=user)
        elif user.hostel_id != None and user.room_id == None:
            hostel = Hostel.query.filter_by(hostel_id=user.hostel_id).first()
            rooms = db.engine.execute(
                "Select * from rooms where rooms.beds != (select count(*) from Users where users.room_id == rooms.room_num) and hostel_id == " + str(
                    hostel.hostel_id)).fetchall()
            return render_template('book_a_room.html', rooms=rooms, user=user)
        elif user.hostel_id != None and user.room_id != None:
            ann_userId = User.query.filter_by(role="admin", hostel_id=user.hostel_id).first()
            announcements = Announcement.query.filter_by(user_id=ann_userId.id)
            return render_template('student_announcement_page.html', user=user, announcement=announcements)

    else:
        return render_template('logInStudentError.html')


@app.route("/student/<id>/picked_hostel")
@login_required
def picked_hostel(id):
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        hostelInfo = None
        for hostel in tourContent:
            if (hostel['id'] == int(id)):
                hostelInfo = hostel
        return render_template('selected_hostel.html', hostelInfo=hostelInfo, user=user)
    else:
        return render_template('logInStudentError.html')


@app.route("/student/<id>/picked_hostel/selected", methods=['GET', 'POST'])
@login_required
def confirm_hostel(id):
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        user.hostel_id = int(id)
        db.session.commit()
        return redirect(url_for('student'))
    else:
        return render_template('logInStudentError.html')


@app.route("/student/<id>/picked_room")
@login_required
def picked_room(id):
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        room = Room.query.filter_by(room_num=id).first()
        table = TotalStudentsReport(room.occupants)
        return render_template('selected_room.html', table=table, room=room, user=user)
    else:
        return render_template('logInStudentError.html')


@app.route("/student/<id>/picked_room/selected", methods=['GET', 'POST'])
@login_required
def confirm_room(id):
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        user.room_id = id
        db.session.commit()
        return redirect(url_for('student'))
    else:
        return render_template('logInStudentError.html')


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/payments', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.save(picture_path)

    return picture_fn


@app.route("/student/make_payment", methods=['GET', 'POST'])
@login_required
def student_payment():
    if current_user.role == 'student':
        form = StudentPaymentForm()
        user = User.query.filter_by(id=current_user.id).first()
        amount_remaining = 1000
        if form.validate_on_submit():
            if form.receipt.data:
                picture_file = save_picture(form.receipt.data)
                image = Images(image_file=picture_file, user_id=current_user.id)
                image_name = image.image_file
                db.session.add(image)
                db.session.commit()
                flash('Receipt successfully sent, wait for confirmation from your Hostel Admin', 'success')
                return redirect(url_for('student_payment'))
            elif request.method == 'GET':
                form.receipt.data = None
        return render_template('student_payment.html', user=user, form=form, amount_remaining=amount_remaining)
    else:
        return render_template('logInStudentError.html')


@app.route("/student/view_room", methods=['GET', 'POST'])
@login_required
def student_viewroom():
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        room = Room.query.filter_by(room_num=current_user.room_id).first()
        table = TotalStudentsReport(room.occupants)
        return render_template('student_viewroom.html', table=table, room=room, user=user)
    else:
        return render_template('logInStudentError.html')


@app.route("/student/view_room/leave_room", methods=['GET', 'POST'])
@login_required
def student_leaveroom():
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        user.room_id = None
        db.session.commit()
        return redirect(url_for('student'))
    else:
        return render_template('logInStudentError.html')


@app.route("/student/account", methods=['GET', 'POST'])
@login_required
def updatestudentaccount():
    if current_user.role == 'student':
        form = UpdateAccountForm()
        user = User.query.filter_by(id=current_user.id).first()
        if form.validate_on_submit():
            current_user.firstname = form.firstname.data
            current_user.lastname = form.lastname.data
            current_user.number = form.number.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('updatestudentaccount'))
        elif request.method == 'GET':
            form.firstname.data = current_user.firstname
            form.lastname.data = current_user.lastname
            form.number.data = current_user.number
            form.email.data = current_user.email
        return render_template('update_studentAccount.html', title='Account', form=form, user=user)
    else:
        return render_template('logInStudentError.html')


@app.route("/student/account/leave_hostel")
@login_required
def student_leavehostel():
    if current_user.role == 'student':
        user = User.query.filter_by(id=current_user.id).first()
        user.hostel_id = None
        db.session.commit()
        return redirect(url_for('student'))
    else:
        return render_template('logInStudentError.html')

@app.route('/student/changepassword', methods=['GET', 'POST'])
@login_required
def change_Studentpassword():
    if current_user.role == 'student':

        form = ChangePasswordForm()
        user = User.query.filter_by(id=current_user.id).first()
        if request.method == 'POST':
            if form.validate_on_submit():
                if bcrypt.check_password_hash(user.password, form.current_password.data):
                    hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                    user.password = hashed_password
                    db.session.commit()
                    flash('Your password has been changed!', 'success')
                    return redirect(url_for('change_Studentpassword'))
                else:
                    flash('Current password might be wrong', 'danger')
                    return redirect(url_for('change_Studentpassword'))
        return render_template('change_Studentpassword.html', form=form, legend="Change Password")
    else:
        return render_template('logInError.html')