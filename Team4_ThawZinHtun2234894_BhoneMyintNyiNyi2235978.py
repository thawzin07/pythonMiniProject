import RPi.GPIO as GPIO
import I2C_LCD_driver
from time import sleep
from mfrc522 import SimpleMFRC522

from picamera import PiCamera
import telepot

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

MATRIX = [[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9],
          ['*', 0, '#']]

ROW = [6, 20, 19, 13]  # row pins
COL = [12, 5, 16]  # column pins



GPIO.setup(26, GPIO.OUT)  # set GPIO 26 as output for servo
PWM = GPIO.PWM(26, 50)  # set 50Hz PWM output at GPIO 26
PWM.start(0)  # start PWM with 0% duty cycle

GPIO.setup(27,GPIO.OUT)#LED
GPIO.setup(19,GPIO.IN)#make pin 19 an input pin
GPIO.setup(23,GPIO.OUT) #set GPIO 23 as output, motor
GPIO.setup(17, GPIO.IN) #PIR
GPIO.setup(22,GPIO.IN) #for slider switch
GPIO.setup(24,GPIO.OUT) #set GPIO 24 as output
GPIO.setup(18,GPIO.OUT)

camera = PiCamera()
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.start_preview()
camera.brightness = 50
camera.hflip = True

def capture_image():
    sleep(1)
    camera.capture('/home/pi/Desktop/image.jpg')
    print('Image captured') 
# Telegram bot configurations
Bot_Token = '6632663355:AAGQDD_9MO0FnLDuasE8V9vKEeZm8IqWWN0'
CHAT_ID = '5259569395'
bot = telepot.Bot(Bot_Token)

reader = SimpleMFRC522()

LCD = I2C_LCD_driver.lcd()
LCD.backlight(1)



def move_servo(angle):
    duty = angle / 18 + 2
    GPIO.output(26, True)
    PWM.ChangeDutyCycle(duty)
    sleep(1)
    GPIO.output(26, False)
    PWM.ChangeDutyCycle(0)

def check_passcode(passcode):
    global count
    if passcode == "0123":
        LCD.backlight(1) #turn backlight on 
        LCD.lcd_display_string("Access granted.", 1) #write on line 1
        sleep(2) #wait 2 sec
        LCD.lcd_clear() #clear the display
        return True
    else:
        LCD.lcd_display_string("Access denied.", 1) #write on line 1
        sleep(2) #wait 2 sec
        LCD.lcd_clear() #clear the display
        print("I am here")
        count += 1
        return False

def check_rfid(id):
    global count
    id = str(id)
    with open("authlist.txt", "r+") as f:
        auth = f.read()
        if id in auth:
            number = auth.split('\n')
            pos = number.index(id)
            LCD.backlight(1) #turn backlight on 
            LCD.lcd_display_string("access granted") #write on line 1
            sleep(2) #wait 2 sec
            LCD.lcd_clear() #clear the display
            return True
        else:
            print("RFID: Card with UID", id, "not found in database; access denied")
            LCD.lcd_display_string("access denied") #write on line 1
            count += 1
            sleep(2) #wait 2 sec
            LCD.lcd_clear() #clear the display
            return False
        


# Set column pins as outputs, and write default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i], GPIO.OUT)
    GPIO.output(COL[i], 1)


for j in range(4):
    GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

def keypad_input():
    while True:
        for i in range(3):  # loop through all columns
            GPIO.output(COL[i], 0)  # pull one column pin low
            for j in range(4):  # check which row pin becomes low
                if GPIO.input(ROW[j]) == 0:  # if a key is pressed
                    while GPIO.input(ROW[j]) == 0:  # debounce
                        sleep(0.1)
                    return MATRIX[j][i]  # return the key pressed
            GPIO.output(COL[i], 1)

def reset_entered_passcode():
    passcode=""



def start_motor_light():
    sleep(5)
    PIR_state=GPIO.input(17)
    if PIR_state == 1:
        LCD.lcd_clear()
        LCD.lcd_display_string("No Motion ", 1)
        GPIO.output(24,0)
        print("no motion")
        sleep(5)
    elif PIR_state == 0:
        LCD.lcd_clear()
        LCD.lcd_display_string("Motion", 1)
        print("motion")
        GPIO.output(24,1)
        GPIO.output(23,1)
        sleep(7)
        GPIO.output(24,0)
        GPIO.output(23,0)

def capture_image():
    sleep(0.1)
    camera.capture('/home/pi/Desktop/image.jpg')
    print('Image captured')

    
global count
count = 0
# Scan keypad and authenticate
while True:
    passcode = ""
    
    

    choice = input("Enter 1 for keypad or 2 for RFID: ")

    if choice == '1':
        for _ in range(4):  # assume a 4-digit passcode
            key = str(keypad_input())
            passcode += key
            sleep(0.2)
            LCD.lcd_display_string(passcode, 2)
    
    if choice == '1':

        if check_passcode(passcode):
            if True:
                move_servo(180)
                sleep(2)
                move_servo(0)
                reset_entered_passcode()
                start_motor_light()
                    
            else:
                print("no match")
                text_message = "Someone tried to go in."
                bot.sendMessage(CHAT_ID, text_message)
                reset_entered_passcode()
            
    elif choice == '2':
        reset_entered_passcode()

        if check_rfid(reader.read_id()):
            if True:
                move_servo(180)
                sleep(2)
                move_servo(0)
                start_motor_light()
            else:
                text_message = "Someone tried to go in."
                bot.sendMessage(CHAT_ID,text_message)
                print("no match")
               
                
    else:
        print("Invalid choice")

    print(count)
    if count > 2 :
        print("danger")
        capture_image()
        count = 0
        bot.sendPhoto(CHAT_ID, photo=open('/home/pi/Desktop/image.jpg', 'rb'))
        for x in range(10):
            GPIO.output(18,1)
            sleep(0.3)
            GPIO.output(18,0)
            sleep(0.3)
        
        
    reset_entered_passcode()


    sleep(0.1)
