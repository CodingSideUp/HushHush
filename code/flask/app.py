# Import necessary modules
import numpy as np
from flask import Flask, render_template, request, flash, redirect, url_for, session
import sys
sys.path.append('../')
from stackoverflow.supervised import StackOverflowPrediction
from stackoverflow.db.db_connection import connection
from stackoverflow.db.stackoverflow_db import cursorHandler, insert_into_table, use_stackOverflowDB
from GitHub.Supervise_model import return_models
from GitHub.Supervise_model import features as git_features
from sqlalchemy import create_engine
import pandas as pd
from email.message import EmailMessage
import smtplib
import os

# Create a Flask app instance
app = Flask(__name__)

# Session dictionary to store user session data
session = {}

# Set a secret key for the Flask app
app.secret_key = 'bigdataprogramming_python'

# DataFrames initialisation
stack_df = None
git_df = None

# DB credentials
DB_user = "root"
DB_password = "password"
DB_host = "localhost"

# Default username and password for demonstration
hrusername = 'hradmin'
hrpassword = 'hr1'

# Default username and password for demonstration
trusername = 'tradmin'
trpassword = 'tr1'


# Path to the image file
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, 'certificate/Participation Certificate.jpg')


# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_username = request.form['username']
        form_password = request.form['password']
        # Check if the entered username and password are correct for HR
        if form_username == hrusername and form_password == hrpassword:
            session['user'] = hrusername
            session['tech'] = False
            # Redirect to HR or TR page based on the user's role
            return redirect(url_for('index', tech=False))
        # Check if the entered username and password are correct for TR
        elif form_username == trusername and form_password == trpassword:
            session['user'] = trusername
            session['tech'] = True
            # Redirect to HR or TR page based on the user's role
            return redirect(url_for('index', tech=True))
        else:
            # Flash error message for invalid credentials
            flash('Invalid username or password', 'error')
    # Render the login template
    return render_template('login.html')


# Route for logging out
@app.route('/logout')
def logout():
    # Remove user session data upon logout
    if 'user' in session:
        session.pop('user')
    return redirect(url_for('login'))


# Route for searching user details based on skills
@app.route('/search', methods=['POST'])
def search():
    session['query'] = request.form.get('searched_results')

    # For StackOverflow
    model = StackOverflowPrediction()
    stack_df = model.get_data(skill=session['query'])

    if stack_df.empty:
        stackShow = False
    else:
        stack_df['pred'] = model.predict(stack_df[model.features])
        stack_df = stack_df[stack_df['pred'] == 1][['account_id', 'user_id', 'link', 'display_name']]
        if len(stack_df) >= 1:
            stackShow = True
        else:
            stackShow = False
    
    # For GitHub
    gitDB_name = "github_data"
    engine = create_engine(f'mysql+mysqlconnector://{DB_user}:{DB_password}@{DB_host}/{gitDB_name}')

    git_df = pd.read_sql_query(sql=f"SELECT * FROM github_data WHERE languages Like '%{session['query']}%' ", con = engine)
    
    git_df = git_df[git_df['Languages'].str.contains(r'\b{}\b'.format(session['query']), case=False)]

    if git_df.empty:
        gitShow = False
    else:
        scaler, rf_classifier, ada_classifier, xgb_classifier = return_models()
        git_df[git_features] = scaler.transform(git_df[git_features])

        pred_xgb = xgb_classifier.predict(git_df[git_features])
        pred_svc = rf_classifier.predict(git_df[git_features])
        pred_ada = ada_classifier.predict(git_df[git_features])

        final_pred = np.zeros(len(pred_xgb), dtype = int)
        unique_count = {}

        for i in range(len(pred_xgb)):
            for j in np.unique([pred_xgb, pred_svc, pred_ada]):
                unique_count[j] = 0

            unique_count[pred_xgb[i]] += 1
            unique_count[pred_svc[i]] += 1
            unique_count[pred_ada[i]] += 1

            final_pred[i] = max(unique_count, key = unique_count.get)

        git_df['pred'] = final_pred
        git_df = git_df[['Username', 'Repo_name', 'Repo_url', 'Languages']]

        if len(git_df) >= 1:
            gitShow = True
        else:
            gitShow = False

    return render_template('search.html', userdetails=[stack_df.values, git_df.values], stackShow = stackShow, gitShow = gitShow, first=False)


# Route for the homepage
@app.route('/')
def index():
    if 'user' in session:
        if session['tech']:
            return redirect(url_for('technicalrecruiter'))
        else:
            return redirect(url_for('humanresourcepage'))
    else:
        return redirect(url_for('login'))

# Route for the technical recruiter page
@app.route('/technicalrecruiter')
def technicalrecruiter():
    return render_template('tech.html')

# Route for the technical recruiters search
@app.route('/technicalrecruiter_search', methods=['POST'])
def technicalrecruiter_Search():
    skillset = request.form['searched_results']
    engine = create_engine(f'mysql+mysqlconnector://{DB_user}:{DB_password}@{DB_host}/selected_users')
    selectedStack_df = pd.read_sql_table(table_name="stackoverflow_" + skillset.lower(), con = engine)
    selectedGit_df = pd.read_sql_table(table_name="github_" + skillset.lower(), con = engine)
    
    if len(selectedStack_df) >= 1:
        stackShow = True
    else:
        stackShow = False

    if len(selectedGit_df) >= 1:
        gitShow = True
    else:
        gitShow = False
        
    return render_template('tech_search.html', users = [selectedStack_df.values, selectedGit_df.values], stackShow = stackShow, gitShow = gitShow)

# Route for the human resource page
@app.route('/humanresourcepage')
def humanresourcepage():
    return render_template('hr.html')


#mail for HR to send an coding invite
@app.route('/sendmail', methods=['POST'])
def mail():
    googleformlink = "https://forms.gle/rDHYgVzLM3pXCaXq7"
    form_value = request.form['mailid']
    userDetails = request.form['userDetails']
    form_value = form_value[1:-1].split(', ')
    userDetails = userDetails[1:].split(", ")
    # Code to send email
    msg = EmailMessage()
    msg.set_content(f'''Dear Candidate,

I hope this email finds you well. I am delighted to inform you that after careful consideration of all applicants, we have selected you to proceed to the next stage of our recruitment process: the online coding interview.

Your application stood out to us due to your impressive qualifications, experience, and the potential we see in you to thrive within our team. We believe that your skills align perfectly with the requirements of the position, and we are excited to learn more about you during the upcoming interview.

The online coding interview is scheduled for 13-03-2024 at 12PM CEST. Please make sure to mark this date and time on your calendar. You will receive a separate email shortly with detailed instructions on how to join the interview, including any technical requirements or platforms you may need to access.

During the interview, we'll delve deeper into your technical abilities, problem-solving skills, and your approach to coding challenges. We encourage you to prepare thoroughly and feel free to reach out if you have any questions or need further clarification on anything. Additionally, to find the link for the coding exam, please visit {googleformlink}.

Once again, congratulations on making it to this stage of the hiring process. We are eager to meet you virtually and explore the possibility of you joining our team.

Best regards,
HR Team
hr@doodle.com
www.doodle.com''')
    msg['Subject'] = 'Congratulations! You have Been Selected for the Online Coding Interview'
    msg['From'] = 'bigdataprogramming5@gmail.com'
    msg['To'] = form_value[0][1:-1]

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('bigdataprogramming5@gmail.com', 'axnc sazu rqzp mwuc')
        server.send_message(msg)
        server.quit()

        if form_value[1][1:-1] == "StackOverflow":
            with cursorHandler(connection) as cursor:
                table_name = form_value[1][1:-1] + "_" + session['query'].lower()
                cursor.execute("Use Selected_Users")
                cursor.execute("CREATE TABLE IF NOT EXISTS `" + table_name + "`(account_id INT, user_id INT, link VARCHAR(255), display_name VARCHAR(150))")
                insert_into_table(cursor, "Insert INTO `" + table_name + "` Values(%s, %s, %s, %s)", tuple(userDetails))

                use_stackOverflowDB(cursor)
                cursor.execute("Delete From UserData Where User_ID = %s AND Tag_Name = %s", (userDetails[1], session['query']))
                
        elif form_value[1][1:-1] == "GitHub":
            userDetails = userDetails[:3] + [', '.join(userDetails[3:])]
            with cursorHandler(connection) as cursor:
                table_name = form_value[1][1:-1] + "_" + session['query'].lower()
                cursor.execute("Use Selected_Users")
                cursor.execute("CREATE TABLE IF NOT EXISTS `" + table_name + "` (Username VARCHAR(255), Repo_name VARCHAR(255), Repo_url VARCHAR(255), Languages VARCHAR(255))")
                insert_into_table(cursor, "Insert INTO `" + table_name + "` Values(%s, %s, %s, %s)", tuple(userDetails))

                cursor.execute("Use github_data")
                cursor.execute("Delete From github_data Where username = %s AND Repo_url = %s", (userDetails[0], userDetails[2]))

        return 'Mail sent successfully!'
    except Exception as e:
        return str(e)


#mail for TR to send an face-to-face interview invite
@app.route('/successmail', methods=['POST'])
def mail1():
    mail_id = request.form['mailid']
    # Code to send email
    msg = EmailMessage()
    msg.set_content('''Dear Candidate,

I hope this email finds you well. I am writing to extend my heartfelt congratulations on successfully qualifying in the coding round of our selection process. Your performance was exceptional, and it is my pleasure to inform you that you have been selected to proceed to the next stage: the face-to-face interview.

Your proficiency in coding truly impressed our team, and we believe that you have the potential to make significant contributions to our organisation. The face-to-face interview will provide us with an opportunity to delve deeper into your qualifications, experience, and aspirations, as well as to gauge your compatibility with our team and company culture.

We are eager to learn more about you and your capabilities during this next phase of the selection process. Please be prepared to discuss your background, skills, and any relevant experiences that demonstrate your suitability for the role.

The face-to-face interview will be scheduled at your earliest convenience. Our HR team will reach out to you shortly to coordinate the logistics and provide you with further details about the interview process.

Once again, congratulations on your accomplishment, and best of luck as you progress to the next round. We look forward to meeting with you and exploring the possibility of you joining our team.
Should you have any questions or require any further information, please do not hesitate to reach out to us.

Warm regards,
Technical Recruiter
techrecruiter@doodle.com
www.doodle.com''')
    msg['Subject'] = 'Congratulations on Qualifying for the Face-to-Face Interview Round!'
    msg['From'] = 'bigdataprogramming5@gmail.com'
    msg['To'] = mail_id

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('bigdataprogramming5@gmail.com', 'axnc sazu rqzp mwuc')
        server.send_message(msg)
        server.quit()
        return 'Mail sent successfully!'
    except Exception as e:
        return str(e)


 #mail for TR to send a rejection mail 
@app.route('/rejectedmail', methods=['POST'])
def mail2():
    mail_id = request.form['mailid']
    # Code to send email
    msg = EmailMessage()
    msg.set_content('''Dear Candidate,

I hope this email finds you well. We sincerely appreciate the time and effort you invested in applying for the role at Doodle.

After careful consideration and evaluation of all applicants, we regret to inform you that you have not been selected to proceed to the next stage of the hiring process. This decision was a difficult one, as we received numerous qualified applications.

We want to express our gratitude for your interest in joining our team and participating in the coding round. Your skills and experience are certainly commendable. Although you were not selected this time, we encourage you to continue pursuing opportunities that align with your career goals.

We also want to extend an invitation to participate in future job openings at Doodle. Your application will remain in our database, and we will certainly consider you for suitable positions that match your qualifications.

Once again, thank you for your interest in joining our team. We wish you all the best in your future endeavours.

Warm regards,
Technical Recruiter
techrecruiter@doodle.com
www.doodle.com''')
    msg['Subject'] = 'Outcome of Your Recent Coding Assessment'
    msg['From'] = 'bigdataprogramming5@gmail.com'
    msg['To'] = mail_id

    # Add image attachment
    with open(image_path, 'rb') as f:
        img_data = f.read()
        msg.add_attachment(img_data, maintype='image', subtype='jpg', filename=os.path.basename(image_path))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('bigdataprogramming5@gmail.com', 'axnc sazu rqzp mwuc')
        server.send_message(msg)
        server.quit()
        return 'Mail sent successfully!'
    except Exception as e:
        return str(e)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
