# Import necessary modules
from flask import Flask, render_template, request, flash, redirect, url_for
from email.message import EmailMessage
import smtplib
import os

# Create a Flask app instance
app = Flask(__name__)

# Session dictionary to store user session data
session = {}

# Set a secret key for the Flask app
app.secret_key = 'bigdataprogramming_python'

# Dummy user details for demonstration
userdetails = [
    {'name': 'Sheethal', 'number': '+91 9606745070', 'skills': 'Python', 'email': 'sheetalr0705@gmail.com'},
    {'name': 'Madhura', 'number': '+91 1234567890', 'skills': 'Python', 'email': 'aravendekarmadhura@gmail.com'},
    {'name': 'Adhirath', 'number': '+91 0987654321', 'skills': 'Java', 'email': 'adhirath.balan@gmail.com'},
    {'name': 'Gurudarshan', 'number': '+91 1357924680', 'skills': 'C', 'email': 'guru@gmail.com'},
    {'name': 'Chetan', 'number': '+91 2468013579', 'skills': 'C++', 'email': 'chetan@gmail.com'},
]

# Default username and password for demonstration
hrusername = 'hradmin'
hrpassword = 'hr1'

# Default username and password for demonstration
trusername = 'tradmin'
trpassword = 'tr1'


# Path to the image file
image_path = '/Users/Gurudarshan/Downloads/Participation Certificate.jpg'


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
    query = request.form.get('searched_results')
    print("I am in search after click")
    print("Query:", query)

    # Filter user details based on the search query
    filtered_userdetails = [user for user in userdetails if query.lower() in user['skills'].lower()]
    length = len(filtered_userdetails)
    if length>=1:
        show=True
    else:
        show=False
    return render_template('search.html', userdetails=filtered_userdetails, show=show, first=False)


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
    return render_template('tech.html', show=True, userdetails=userdetails)

# Route for the human resource page
@app.route('/humanresourcepage')
def humanresourcepage():
    return render_template('search.html', userdetails=userdetails, show=False)


#mail for HR to send an coding invite
@app.route('/sendmail', methods=['POST'])
def mail():
    googleformlink = "https://forms.gle/rDHYgVzLM3pXCaXq7"
    mail_id = request.form['mailid']
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
    msg['To'] = mail_id

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('bigdataprogramming5@gmail.com', 'axnc sazu rqzp mwuc')
        server.send_message(msg)
        server.quit()
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
    msg['Subject'] = 'Congratulations! You have Been Selected for the Online Coding Interview'
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
