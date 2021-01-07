#!/usr/bin/python
import subprocess
from gpiozero import OutputDevice
import time
import RPi.GPIO as GPIO
from time import sleep
import serial
import sys
import sqlite3
import time
import string 
from serial import SerialException

ON_THRESH_HUM = (70.0)  # (% humidity, temperature in F) Fan kicks on at this humidity.
LOW_HUM = (40.0)  # (% humidity, temperature in F) Email notification below this humidity.
ON_THRESH_TEMP = (80.0)  # (% humidity, temperature in F) Fan kicks on at this temp.
SLEEP_INTERVAL = 270  # (seconds) How long the fan runs. 
GPIO_PIN = 3  # Which GPIO pin you're using to control the relay/fan.

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
            return reading
    
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
            
if __name__ == "__main__":
    #setup the GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(GPIO_PIN,GPIO.OUT)
    
    fan = OutputDevice(GPIO_PIN,False) #assign variable to pin to later get boolean on/off

#**************************get temp and humidity reading**************************************************
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

    temp_hum_split = temp_hum.split(',')
    humid = float(temp_hum_split[0])
    temperature = float(temp_hum_split[1])
    temp = (temperature * 9/5)+32

    print('humidity is: ',humid, 'temperature is:', temp)
    
#**********************LOG TEMP + HUMIDITY TO DB*************************
    conn = sqlite3.connect('/home/pi/Desktop/PythonScripts/Logger/green_data.db')
    c = conn.cursor()

    date=time.strftime("%Y-%m-%d ")     # current date
    t=time.strftime("%H:%M:%S")         # current time
    c.execute("INSERT INTO ezosensor(temperature,humidity,Date,Time) VALUES(?,?,?,?)", (temp,humid,date,t))
    conn.commit() # commit all changes to database

    
    
    
#***************IF STATEMENT TURNS ON FAN FOR TIME*********************
    time.sleep(5)
    
    if (humid > ON_THRESH_HUM or temp>ON_THRESH_TEMP):
        print('Fan turns on')
        fan.on()
        time.sleep(SLEEP_INTERVAL)
        print('Fan turns off')
        fan.off()


    elif (humid < LOW_HUM):
        humidity_message = '''
        Datetime= {}
        Environmental Temperature= {}
        Environmental Humidity= {}
        '''.format(date+"."+t, temp, humid)

        def send_mail(message, title):#, file):
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            gmailUser = yourGmail
            gmailPassword = yourPassword
            recipient = yourRecipients

            #attachment = open(file,"rb")
            msg = MIMEMultipart()
            msg['From'] = gmailUser
            msg['To'] = recipient
            msg['Subject'] = title
            msg.attach(MIMEText(message))
            
            #part = MIMEBase("application","octet-stream")
            #part.set_payload((attachment).read())
            #encoders.encode_base64(part)
            #part.add_header("Content-Disposition","attachment;filename= " + file)
            #msg.attach(part)

            mailServer = smtplib.SMTP('smtp.gmail.com', 587)
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(gmailUser, gmailPassword)
            mailServer.sendmail(gmailUser, recipient, msg.as_string())
            mailServer.close()
            #print ("Mail sent")

        send_mail(humidity_message, "Alert: Humidity is Low")#, image_file)


     

   



