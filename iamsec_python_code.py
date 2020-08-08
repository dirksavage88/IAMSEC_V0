#!/usr/bin/python
import os, sys, time, requests, json
import board
import signal
import VL53L1X
import busio
import adafruit_bme680
import boto3
from adafruit_seesaw.seesaw import Seesaw
from busio import I2C
from board import SCL, SDA

#Amazon SNS Keys
AWS_ACCESS_KEY = ''
AWS_SECRET_ACCESS = ''
TOPIC_ARN = 'arn:aws:sns:us-east-1:284671194479:datadump'

#seesaw library objects for soil sensor
i2c_bus = busio.I2C(SCL, SDA)
ss = Seesaw(i2c_bus, addr=0x36)
#VL53L1X TOF library objects
tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open() # Initialise the i2c bus and configure the sensor
tof.start_ranging(3) # Start ranging, 1 = Short Range, 2 = Medium Range, 3 = Long Range
a = 0
b = 0
c = 0
#define amazon sns publish
def publish(snsClient, message):
    response = snsClient.publish(TopicArn = TOPIC_ARN, Message = message, Subject = '24/7 Housesitter')
    print("Published with id %s " % response)

def vl53l1x():
    #vl53l1x variables
    min_distance_alert = 1000
    units = "meters"
    space = " "
    p = 2
    current_distance_in_mm = tof.get_distance() # Grab the range in mm
    print("Distance: {}mm".format(current_distance_in_mm))
    current_distance_in_m = float(current_distance_in_mm/1000)
    if current_distance_in_mm < min_distance_alert:
        print("Presence detected! Alerting user")
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Presence detected!(value in meters)": '{0:.{1}f}'.format(current_distance_in_m, p)}

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload),headers=headers, timeout=5) 
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")
        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        #Send SNS through Amazon Web Services
        message = "Presence detected! There has been movement detected within %.2f meters " % current_distance_in_m
        publish(snsClient, message)
        
    time.sleep(1)
    
def soil():
    # read moisture from the sensor
    touch = ss.moisture_read()

    # read temperature from the temperature sensor
    temp = ss.get_temp()
    global c
    print("temp: " + str(temp) + "  moisture: " + str(touch))
    if temp > 32:
        print("High temperature detected:" + str(temp))
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"High Temperature": format(temp)}
        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        c = 1
    if touch > 600:
        print ("Excess moisture level:" + str(touch))
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Excess Moisture Level": round(touch * 10) / 10 }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        
    time.sleep(1)

def bme680():
    #gas sensor library objects
    i2c = I2C(board.SCL, board.SDA)
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
    #gas sensor variables
    bme680.sea_level_pressure = 1013.25
    n = 1
    global a
    global b
    print("Gas: %d ohm" % bme680.gas)
    print("Humidity: %0.1f %%" % bme680.humidity)
    print("Pressure: %0.3f hPa" % bme680.pressure)
    print("Altitude = %0.2f meters" % bme680.altitude)
    if bme680.humidity > 72:
        print("Elevated humidity: consider ventilation or air conditioning to avoid mold")
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Slightly Elevated Relative Humidity": '{0:.{1}f}'.format(bme680.humidity, n)  }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)

    elif bme680.humidity > 80:
        print("Extreme elevated humidity! Consider ventilation or air conditioning to avoid mold")
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Extreme Elevated Relative Humidity": '{0:.{1}f}'.format(bme680.humidity, n)  }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        a = 1
    if bme680.gas < 170000:
        print("Slightly elevated VOC gas detected")
        # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Slightly elevated VOC": format(bme680.gas, "d")  }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        b = 1
    elif bme680.gas < 45556:
        print("Elevated VOC gas detected!")
        # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Elevated VOC": format(bme680.gas, "d")  }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        b = 1
    elif bme680.gas < 20000:
        print("Extreme elevated VOC gas detected!")
         # Set the HTTP request header and payload content
        headers = {"Content-Type": "application/json"}
        payload = {"Extreme Elevated VOC": format(bme680.gas, "d")  }

        # Send the HTTP request to Harvest
        print ("Sending data to Harvest...:" + str(json.dumps(payload)))
        try:
            response = requests.post("http://unified.soracom.io", data=json.dumps(payload), headers=headers,timeout=5)
        except requests.exceptions.ConnectTimeout:
            print ("Error: Connection timeout. Is the modem connected?")

        # Display HTTP request response
        if response.status_code == 201:
            print ("Response 201: Success!")
        elif response.status_code == 400:
            print ("Error 400: Harvest did not accept the data. Is Harvest enabled?")
            sys.exit(1)
        b = 1
    time.sleep(1)

def exit_handler(signal, frame):
    global running
    running = False
    print("Closing resources")
    tof.stop_ranging() # Stop ranging
    print("User has closed execution")
    sys.exit(0)

if __name__ == "__main__":
    try:
        snsClient = boto3.client(
            'sns',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS,
            region_name='us-east-1'
        )
        running = True
        signal.signal(signal.SIGINT, exit_handler) #signal handler call to accept user input to exit
        urgent = "Indoor air quality poor: log into Soracom User Console to view Harvest data"
        vurgent = "Indoor air quality very poor: log into Soracom User Console to view Harvest data"
        #2/3 variables true: urgent SNS sent, 3/3: very urgent sent
        
        while running:
            vl53l1x()
            soil()
            bme680()
            #if globals == 2, send urgent sns, if ==3 sent very urgent sns
            if a + b + c == 2:
                publish(snsClient, urgent)
                a = 0
                b = 0
                c = 0
            elif a + b + c == 3:
                publish(snsClient, vurgent)
                a = 0
                b = 0
                c = 0
    except KeyboardInterrupt:
        pass



