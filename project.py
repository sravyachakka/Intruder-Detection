import streamlit as st
import mysql.connector
import cv2
from PIL import Image
import face_recognition
import time
import smtplib
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from twilio.rest import Client
import os

def check_login(username, password):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=4306,
            user="root",
            password="",
            database="project_db"
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        return result is not None, result

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False, None

def capture_image_with_delay():
    cap = cv2.VideoCapture(0)  

    time.sleep(3)
    ret, frame = cap.read()
    image_path = "captured_image.jpg"
    cv2.imwrite(image_path, frame)

    cap.release()

    return image_path

tolerance = 0.6
def compare_images(captured_image_path, database_image_path):

    captured_image = face_recognition.load_image_file(captured_image_path)
    
  
    captured_image_rgb = cv2.cvtColor(captured_image, cv2.COLOR_BGR2RGB)

    captured_face_locations = face_recognition.face_locations(captured_image_rgb)

    if len(captured_face_locations) == 0:
       
        return False

    captured_encodings = face_recognition.face_encodings(captured_image_rgb, captured_face_locations)
    database_image = face_recognition.load_image_file(database_image_path)
    database_encoding = face_recognition.face_encodings(database_image)[0]
    if captured_encodings:
        for captured_encoding in captured_encodings:
            face_distance = face_recognition.face_distance([database_encoding], captured_encoding)
            if face_distance <= tolerance:
                return True
    return False

def send_email(image_path, subject, body):
    sender_email = "sravyachakka1234@gmail.com" 
    sender_password = "jtfguevtkjvxqdie"  
    receiver_email = "praveenachinthalapudi1012@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(image_path, 'rb') as image_file:
        attachment = MIMEImage(image_file.read())
        attachment.add_header('Content-Disposition', 'attachment', filename="captured_image.jpg")
        msg.attach(attachment)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        st.success('Mail sent successfully!')

def send_sms_alert():
    account_sid = 'ACe7449f99771dce63bc30f95798e3498c'
    auth_token = 'e532d3a53923e2f4947facd1d0a26edb'
    twilio_phone_number = '+16592187247'
    recipient_number = '+919121949113'
    client = Client(account_sid, auth_token)
    message = "Intruder detected! Please check the mail for the intruder image."
    try:
        client.messages.create(
            to=recipient_number,
            from_=twilio_phone_number,
            body=message
        )
        st.success('SMS sent successfully!')
    except Exception as e:
        st.error(f'Error: {str(e)}')

def main():
    st.title("Login Form")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if 'image_authorized' not in st.session_state:
        st.session_state.image_authorized = False

    if st.button("Login"):
        if username and password:
            authorized, user_data = check_login(username, password)

            if authorized:
                st.success("Welcome!")
                captured_image_path = capture_image_with_delay()
                database_image_path = user_data[4]  
                if compare_images(captured_image_path, database_image_path):
                    st.success("Hurray!!!! You can use the application further now.....")
                    st.image(Image.open(captured_image_path), caption="Captured Image", use_column_width=True)
                    st.write("Now you can add a user")

                    st.session_state.image_authorized = True

                else:
                    st.image(Image.open(captured_image_path), caption="Captured Image", use_column_width=True)

                    st.error("Person using the application is found to be unauthorised!!!!")
                    send_email(captured_image_path, "Unauthorized Access Detected", "Unauthorized access detected. Attached is the image clicked.")
                    send_sms_alert()
                    
            else:
                st.error("Unauthorized. Please check your credentials.")

    if st.session_state.image_authorized:
        upload_dir = "temp"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        st.write("### Add New User")
        new_username = st.text_input("New Username:")
        new_password = st.text_input("New Password:", type="password")
        new_email = st.text_input("Email:")
        uploaded_file = st.file_uploader("Upload Image")

        if st.button("Submit"):
            if new_username and new_password and new_email and uploaded_file:
                image_path = os.path.join(upload_dir, f"{new_username}.jpg")
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                try:
                    conn = mysql.connector.connect(
                        host="localhost",
                        port=4306,
                        user="root",
                        password="",
                        database="project_db"
                    )
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password, email, image) VALUES (%s, %s, %s, %s)",
                                   (new_username, new_password, new_email, image_path))
                    conn.commit()

                    st.success("User added successfully!")

                except Exception as e:
                    st.error(f"An error occurred while adding the user: {e}")
                finally:
                    conn.close()
            else:
                st.error("Please fill in all fields.")

if __name__ == "__main__":
    main()