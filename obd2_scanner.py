import serial
import time
from os import system
#import obd

RESET = b'AT Z\r'
LINE_SPACE = b'AT L1\r'
READ_VOLTAGE = b'AT RV\r'
SET_REGISTER = b'AT SP 0\r'
ENGINE_SPEED = b'01 0C 1\r'
VEHICLE_SPEED = b'01 0D 1\r'
ENGINE_LOAD = b'01 04\r'
TIMING_ADVANCE = b'01 0D 1\r'
THROTTLE_POS = b'01 11 1\r'
ENGINE_REF_TORQUE = b'01 63\r'
ENGINE_PCT_TORQUE = b'01 62\r'
ODOMETER = b'01 C0 1\r'
VIN = b'09 02 1\r'
#SERIAL_PORT = '/COM9'
#BAUD_RATE = 9600
#ser = serial.Serial(SERIAL_PORT,BAUD_RATE)

def init(car):
    time.sleep(0.1)
    car.write(RESET)
    car.reset_input_buffer()
    car.readline()
    car.readline()

    time.sleep(0.1)
    car.write(LINE_SPACE)
    car.reset_input_buffer()
    car.readline()
    car.readline()

    time.sleep(0.1)
    car.write(SET_REGISTER)
    car.reset_input_buffer()
    car.readline()
    car.readline()


    time.sleep(0.2)
    car.write(READ_VOLTAGE)
    car.reset_input_buffer()
    time.sleep(0.1)
    data = str(car.readline())
    print(data)
    data = str(car.readline())
    print(data)

    time.sleep(0.2)
    car.write(ENGINE_SPEED)
    car.reset_input_buffer()
    time.sleep(0.1)
    data = str(car.readline())
    print(data)
    data = str(car.readline())
    if 'SEARCHING' in data:
        data = str(car.readline())
    print(data)
        

def main():
    print('>> ')
    print('>> ELM327 OBDII x PYTHON')
    print('>> ')
    print('>> Connecting to OBDII...')
    time.sleep(1)
    try:
        car = serial.Serial('/COM8',38400,timeout=10)
        #car_listen =serial.Serial('/COM9',9600,timeout=10)
        connection = car.is_open
    except:
        connection = False
    
    if connection:        
        print('>> Connected.')
        car.reset_input_buffer()
        car.reset_output_buffer()
        time.sleep(1)    
        print('>> Initializing...')
        init(car)
        time.sleep(1)
        print('>> Initialized.')
        while True:
            cmd = input(">> ")
            if cmd == "get -sixty":
                tf, t, v = sixty(car,verbose = 1)
                #print(t)
                #print(v)
            if cmd == "get -quarter":
                tf, t, v = quarter(car,verbose = 1)
            if cmd == "get -top":
                v = top_speed(car,verbose = 1)
            if cmd == "exit":
                break
        #while True:
        #    time.sleep(0.25)
        #    car_speed = get_speed(car)
        #    if car_speed != -99:
        #        print(">> " + str(car_speed))
        
    else:
        print('>> Unable to connect.')

def get_speed(car,units = 'KPH'):
    time.sleep(0.2)
    car.write(VEHICLE_SPEED)
    car.reset_input_buffer()
    car.readline()
    data = str(car.readline())
    if 'SEARCHING' in data:
        data = str(car.readline())
    
    try:
        spd = data.split('41 0D')
        spd = spd[1].split('\\r\\n')
        spd = float(spd[0])
        if units == 'MPH':
            spd = spd/1.61
    except:
        spd = -99
    print(">> " + str(spd))
    return spd

def sixty(car,verbose=0):
    # STATE IDs for 0-60 mph test
    # 0: Initial
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print(">> 0 to 60 MPH Test")
    SIXTY_STATE = 0
    print(">> STATE: 0")
    while SIXTY_STATE == 0:
        speed = get_speed(car,units='MPH')
        #print(speed)
        if speed == 0.0:
            SIXTY_STATE = 1
            print(">> STATE: 1")
        elif speed == -99:
            SIXTY_STATE = 4
            print(">> STATE: 4")

    while(SIXTY_STATE == 1):
        speed = get_speed(car,units='MPH')
        print(speed)
        if speed > 0.0:
            SIXTY_STATE = 2
            print(">> STATE: 2")
            t0 = time.time()
            t = [0]
            v = [speed]
    
    while(SIXTY_STATE == 2):
        speed = get_speed(car)
        tf = time.time() - t0
        t.append(tf)
        v.append(speed)
        print(speed)
        if speed >= 20:
            SIXTY_STATE = 3
            print(">> STATE: 3")
        if tf > 20:
            SIXTY_STATE = 4
            print('>> Timed out.')
    if SIXTY_STATE == 3:
        if verbose:
            print('>> ' + str(tf) + ' secs')
        return tf, t, v
    else:
        print('>> Error.')
        return 0, 0, 0

def quarter(car,verbose=0):
    # STATE IDs for 1/4 Mile Test
    # 0: Initialize
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print(">> 1/4 Mile Test")
    QUARTER_STATE = 0
    print(">> STATE: 0")
    while(QUARTER_STATE == 0):
        time.sleep(0.5)
        speed = get_speed(car,units='MPH')
        if speed == 0.0:
            QUARTER_STATE = 1
            print('>> STATE: 1')
        elif speed == -99:
            QUARTER_STATE = 4
            print('>> STATE: 4')
    
    while(QUARTER_STATE == 1):
        speed = get_speed(car,units='MPH')
        if speed > 0.0:
            t0 = time.time()
            t = [0]
            v = [0]
            d = 0
            QUARTER_STATE = 2
            print('>> STATE: 2')
        elif speed == -99:
            QUARTER_STATE = 4
            print('>> STATE: 4')
    
    while(QUARTER_STATE == 2):
        speed = get_speed(car,units='MPH')
        t.append(time.time()-t0)
        v.append(speed)
        # Convert MPH to distance travelled
        d = d + v[-1]/3600*(t[-2]-t[-1])
        if d >= 0.25:
            QUARTER_STATE = 3
            print(">> STATE: 3")
        elif t[-1] >= 30:
            QUARTER_STATE = 4
            print('>> STATE: 4')
            print(">> Timed out.")

    if QUARTER_STATE == 3:
        if verbose:
            print('>> ' + str(t[-1]) + ' secs')
        return t[-1], t, v
    else:
        print('>> Error.')
        return 0, 0, 0

def top_speed(car,verbose=0):
    # STATE IDs for Top Speed Test
    # 0: Initialize
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print('>> Top Speed Test')
    TOP_STATE = 0
    print('>> STATE: 0')
    while TOP_STATE == 0:
        speed = get_speed(car,units='MPH')
        if speed > 0:
            TOP_STATE = 1
            print('>> STATE: 1')
        if speed == -99:
            TOP_STATE = 4
            print('>> STATE: 4')
    max_speed = speed
    stop_speed = 1
    while TOP_STATE == 1:
        speed = get_speed(car,units='MPH')
        if speed > max_speed:
            max_speed = speed
            if max_speed > stop_speed:
                stop_speed = (max_speed)*0.8
            if verbose:
                print('>> ' + str(max_speed))
        
        if speed < stop_speed:
            TOP_STATE = 3
            print('>> STATE: 3')
            print('>> ' + str(max_speed))
    if TOP_STATE == 3:
        return max_speed
    else:
        print('>> Error.')
        return 0
        
    
def help():
    print('>> Here are the current supported commands.')
    print('>> get -top')
    print('>> get -sixty')
    print('>> get -quarter')
    print('>> get -diagnostics')
    print('>> ')

if __name__ == '__main__':
    main()
