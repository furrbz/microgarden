import sys
import Adafruit_DHT
import time
from pathlib import Path
import RPi.GPIO as GPIO
from time import sleep
from picamera import PiCamera
import subprocess
import time
from gpiozero import OutputDevice
import serial
import string 
from serial import SerialException
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
from datetime import date, datetime
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib



#******************************READ RPI CORE TEMPERATURE*************************************
def getCoreTemp():
    '''reads RPi core temp and returns it in a string'''
    output = subprocess.run(['vcgencmd','measure_temp'],capture_output=True)
    temp_str = output.stdout.decode()
    return(temp_str)

core_temp = getCoreTemp()
print('Core Temperature:', core_temp)

#**********************READ ENVIRONMENTAL TEMPERATURE AND HUMIDITY****************************
def read_line():
    """
    taken from the ftdi library and modified to 
    use the ezo line separator "\r"
    """
    lsl = len(b'\r')
    line_buffer = []
    while True:
        next_char = ser.read(1)
        if next_char == b'':
            break
        line_buffer.append(next_char)
        if (len(line_buffer) >= lsl and
                line_buffer[-lsl:] == [b'\r']):
            break
    return b''.join(line_buffer)
    
def read_lines():
    """
    also taken from ftdi lib to work with modified readline function
    """
    lines = []
    try:
        while True:
            line = read_line()
            if not line:
                break
                ser.flush_input()
            lines.append(line)
            reading = lines[:1]
            #temp_hum = lines[:1]
            return reading
        #return temp_hum
    
    except SerialException as e:
        print( "Error, ", e)
        return None 

def send_cmd(cmd):
    """
    Send command to the Atlas Sensor.
    Before sending, add Carriage Return at the end of the command.
    :param cmd:
    :return:
    """
    buf = cmd + "\r"        # add carriage return
    try:
        ser.write(buf.encode('utf-8'))
        return True
    except SerialException as e:
        print ("Error, ", e)
        return None

real_raw_input = vars(__builtins__).get('raw_input', "R") # used to find the correct function for python2/3
usbport = '/dev/ttyS0'
try:
    ser = serial.Serial(usbport, 9600, timeout=0)
except serial.SerialException as e:
    print( "Error, ", e)
    sys.exit(0)
#run the reading
input_val = real_raw_input

send_cmd(input_val)
time.sleep(1.3)
lines = read_lines()
for i in range(len(lines)):
    #print(lines[i].decode('utf-8'))
    temp_hum = lines[i].decode('utf-8')

#temphum_format = temp_hum[0:]
temp_hum_split = temp_hum.split(',')
humid = float(temp_hum_split[0])
temperature = float(temp_hum_split[1])
temp = round(((temperature * 9/5)+32),2)


print('humidity is: ',humid, 'temperature is:', temp)



#********************ASSIGN DATETIME VARIABLES************************************
dtstr = time.strftime("%y%m%d")
tmstr = time.strftime("%H%M")

#********************TAKE A PICTURE***********************************************
image_file = '/home/pi/Desktop/Garden_Images/img_'+dtstr+'_'+tmstr+'.jpg'

def take_photo(file_path):
    camera = PiCamera()
    #camera.rotation = 180
    camera.start_preview()
    sleep(5)
    #print(image_file)
    camera.capture(file_path)
    camera.stop_preview()
    camera.close()

#take_photo(image_file)
    
#************************SEND HTML EMAIL WITH EMBEDDED GRAPH*******************

#**************QUERY THE DB*********************************
conn = sqlite3.connect("/home/pi/Desktop/PythonScripts/Logger/green_data.db") # db - database
cursor = conn.cursor()

ezo_sql = """SELECT * FROM ezosensor;"""
df = pd.read_sql(ezo_sql,conn)

df['DateTime'] = df['Date']+df['Time']


#find 12 hours ago
_12_hours_ago = datetime.now()-timedelta(hours=12)
twelve_ago = str(_12_hours_ago)
date_12_ago = twelve_ago[0:10]
time_12_ago = twelve_ago[11:19]
df_12_ago = df.loc[(df['Date']>=date_12_ago) & (df['Time']>=time_12_ago)]


#*****************GRAPH THE DATA AND SAVE IMAGE***********************************
x = df_12_ago['DateTime'].to_numpy()
y1= df_12_ago['Temperature'].to_numpy()
y2=df_12_ago['Humidity'].to_numpy()
fig = plt.figure(figsize=(10,5))
plt.plot(x, y1, label = "Temperature")
plt.plot(x, y2, label = "Humidity")
plt.legend()

fig.savefig('/home/pi/Desktop/PythonScripts/Production/temp_hum.jpg', bbox_inches='tight', dpi=150)
#plt.show()


#******************EMBED IN HTML AND EMAIL IMAGE***********************************
#Embed image in HTML Text

sample_file = r"/home/pi/Desktop/PythonScripts/Production/temp_hum.jpg"

# Send an HTML email with an embedded image and a plain text message for
# email clients that don't want to display the HTML.
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

gmailUser = yourGmail
gmailPassword = yourPassword
recipient = yourRecipients


# Create the root message and fill in the from, to, and subject headers
msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = 'Alert:RPi4 has Rebooted'
msgRoot['From'] = gmailUser
msgRoot['To'] = recipient
msgRoot.preamble = 'This is a multi-part message in MIME format.'

# Encapsulate the plain and HTML versions of the message body in an
# 'alternative' part, so message agents can decide which they want to display.
msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)

msgText = MIMEText('This is the alternative plain text message.')
msgAlternative.attach(msgText)

# We reference the image in the IMG SRC attribute by the ID we give it below
msgText = MIMEText('''Current Temperature = {}<br>Current Humidity = {}<br>Current Core {}<br>Last 12 Hours:<br>
                        <img src="cid:image1"><br>
                        End of Message'''.format(temp, humid, core_temp), 'html')
msgAlternative.attach(msgText)

fp = open(sample_file, 'rb')
msgImage = MIMEImage(fp.read())
fp.close()

# Define the image's ID as referenced above
msgImage.add_header('Content-ID', '<image1>')
msgRoot.attach(msgImage)

# Send the email (this example assumes SMTP authentication is required)

mailServer = smtplib.SMTP('smtp.gmail.com', 587)
mailServer.ehlo()
mailServer.starttls()
mailServer.ehlo()
mailServer.login(gmailUser, gmailPassword)
mailServer.sendmail(gmailUser, recipient, msgRoot.as_string())
mailServer.close()

print ("Mail sent")


