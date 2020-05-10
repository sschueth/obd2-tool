import serial
import time
from os import system
import pandas as pd
import csv
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
VIN = b'09 02\r'
DIAGNOSTICS = b'03\r'
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
    #print(data)
    data = str(car.readline())
    #print(data)

    time.sleep(0.2)
    car.write(ENGINE_SPEED)
    car.reset_input_buffer()
    time.sleep(0.1)
    data = str(car.readline())
    #print(data)
    data = str(car.readline())
    if 'SEARCHING' in data:
        data = str(car.readline())
    #print(data)
        

def main():
    print('----------------------------------------')
    print('----------ELM327 OBDII x PYTHON---------')
    print('----------------------------------------')
    print('')
    print('Connecting to OBDII...')
    time.sleep(1)
    try:
        car = serial.Serial('/COM8',38400,timeout=10)
        #car_listen =serial.Serial('/COM9',9600,timeout=10)
        connection = car.is_open
    except:
        connection = False
    
    if connection:        
        print('Connected.')
        car.reset_input_buffer()
        car.reset_output_buffer()
        time.sleep(1)    
        print('Initializing...')
        init(car)
        diag_dict = init_diagnostics()
        time.sleep(1)
        print('Initialized.')
        while True:
            cmd = input(">> ")
            if cmd == "help":
                help()

            if cmd == "get -vin":
                car_vin = vin(car)
                print("VIN: " + car_vin)
            if cmd == "get -engine_speed":
                eos = get_eng_speed(car)
                while eos < 3000:
                    eos = get_eng_speed(car)
                    print(str(eos)+" rpm")
                    
            if "get -sixty" in cmd:
                tf, ts, erpms, vs = sixty(car,verbose = 0)
                
                # Saving results
                if "-save" in cmd and tf != 0:
                    text_file = "sixty_time.txt"
                    with open(text_file,'w') as data_file:
                        for idx in range(0,len(ts)):
                            data_file.write(str(ts[idx]) + ', '+ str(erpms[idx]) + ', '+ str(vs[idx]))
                            data_file.write('\n')
                    print("Saved: " + text_file)
            
            if cmd == "get -quarter":
                tf, t, v = quarter(car,verbose = 1)
            if cmd == "get -top":
                v = top_speed(car,verbose = 1)
            if cmd == "get -diagnostics":
                check_diagnostics(car,diag_dict)
            if cmd == "exit":
                car.close()
                break
        
    else:
        print('Unable to connect.')

def get_speed(car,units = 'KPH'):
    car.write(VEHICLE_SPEED)
    time.sleep(0.01)
    car.reset_input_buffer()
    car.readline()
    data = str(car.readline())
    if 'SEARCHING' in data:
        data = str(car.readline())
    
    try:
        spd = data.split('41 0D')
        spd = spd[1].split('\\r\\n')
        spd = float(spd[0])
        if units == 'KPH':
            spd = spd*1.61
    except:
        spd = -99
    #print(">> " + str(spd))
    return spd
    
def get_eng_speed(car):
    car.write(ENGINE_SPEED)
    time.sleep(0.01)
    car.reset_input_buffer()
    car.readline()
    data = str(car.readline())

    if 'SEARCHING' in data:
        data = str(car.readline())
    #print(">> Data: "+data)

    try:
        eng_spd = data.split('41 0C')
        eng_spd = eng_spd[1].split('\\r\\n')
        eng_spd = eng_spd[0].split(' ')
        eng_spd = (float(int(eng_spd[1],16))*256 + float(int(eng_spd[2],16)))/4
        #eng_spd = eng_spd[0] + "," + eng_spd[1]
    except:
        eng_spd = -99
    return eng_spd

def sixty(car,verbose=0):
    # STATE IDs for 0-60 mph test
    # 0: Initial
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print("0 to 60 MPH Test")
    SIXTY_STATE = 0
    print("STATE: 0")
    while SIXTY_STATE == 0:
        speed = get_speed(car,units='MPH')
        eng_speed = get_eng_speed(car)
        #print(speed)
        if speed == 0.0:
            SIXTY_STATE = 1
            print("STATE: 1")
        elif speed == -99:
            SIXTY_STATE = 4
            print("STATE: 4")

    while(SIXTY_STATE == 1):
        speed = get_speed(car,units='MPH')
        eng_speed = get_eng_speed(car)
        #print(speed)
        if speed > 0.0:
            SIXTY_STATE = 2
            print("STATE: 2")
            t0 = time.time()
            t = [0]
            eos = [eng_speed]
            v = [speed]
    
    while(SIXTY_STATE == 2):
        speed = get_speed(car,units='MPH')
        eng_speed = get_eng_speed(car)
        tf = time.time() - t0
        t.append(tf)
        eos.append(eng_speed)
        v.append(speed)
        if verbose:
            print(speed)
        if speed >= 60.0:
            SIXTY_STATE = 3
            print("STATE: 3")
        if tf > 20.0:
            SIXTY_STATE = 4
            print("STATE: 4")
            print('Timed out.')
    if SIXTY_STATE == 3:
        if verbose:
            print(str(tf) + ' secs')
        return tf, t, eos, v
    else:
        print('Error.')
        return 0, 0, 0, 0

def vin(car):
    car.write(VIN)
    car.reset_input_buffer()
    car.readline()
    car.readline()
    vin_data = ""
    while car.in_waiting:
        vin_data += str(car.readline())
    vin_data = vin_data.replace(" ","")
    vin_data = vin_data.replace("b'","")
    vin_data = vin_data.replace("\\r\\n'","")
    vin_data = vin_data.replace("0:","")
    vin_data = vin_data.replace("1:","")
    vin_data = vin_data.replace("2:","")
    vin_data = vin_data.replace("49","")
    vin_data = vin_data[4:]
    bytes_obj = bytes.fromhex(vin_data)
    vin_ascii = bytes_obj.decode("ASCII")
    return vin_ascii

def quarter(car,verbose=0):
    # STATE IDs for 1/4 Mile Test
    # 0: Initialize
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print("1/4 Mile Test")
    QUARTER_STATE = 0
    print("STATE: 0")
    while(QUARTER_STATE == 0):
        time.sleep(0.5)
        speed = get_speed(car,units='MPH')
        if speed == 0.0:
            QUARTER_STATE = 1
            print('STATE: 1')
        elif speed == -99:
            QUARTER_STATE = 4
            print('STATE: 4')
    
    while(QUARTER_STATE == 1):
        speed = get_speed(car,units='MPH')
        if speed > 0.0:
            t0 = time.time()
            t = [0]
            v = [0]
            d = 0
            QUARTER_STATE = 2
            print('STATE: 2')
        elif speed == -99:
            QUARTER_STATE = 4
            print('STATE: 4')
    
    while(QUARTER_STATE == 2):
        speed = get_speed(car,units='MPH')
        t.append(time.time()-t0)
        v.append(speed)
        # Convert MPH to distance travelled
        d = d + v[-1]/3600*(t[-2]-t[-1])
        if d >= 0.25:
            QUARTER_STATE = 3
            print("STATE: 3")
        elif t[-1] >= 30:
            QUARTER_STATE = 4
            print('STATE: 4')
            print("Timed out.")

    if QUARTER_STATE == 3:
        if verbose:
            print(str(t[-1]) + ' secs')
        return t[-1], t, v
    else:
        print('Error.')
        return 0, 0, 0

def top_speed(car,verbose=0):
    # STATE IDs for Top Speed Test
    # 0: Initialize
    # 1: Ready
    # 2: Recording
    # 3: Finished
    # 4: Error
    print('Top Speed Test')
    TOP_STATE = 0
    print('STATE: 0')
    while TOP_STATE == 0:
        speed = get_speed(car,units='MPH')
        if speed > 0:
            TOP_STATE = 1
            print('STATE: 1')
        if speed == -99:
            TOP_STATE = 4
            print('STATE: 4')
    max_speed = speed
    stop_speed = 1
    while TOP_STATE == 1:
        speed = get_speed(car,units='MPH')
        if speed > max_speed:
            max_speed = speed
            if max_speed > stop_speed:
                stop_speed = (max_speed)*0.8
            if verbose:
                print(str(max_speed))
        
        if speed < stop_speed:
            TOP_STATE = 3
            print('STATE: 3')
            print(str(max_speed))
    if TOP_STATE == 3:
        return max_speed
    else:
        print('Error.')
        return 0
        
def help():
    print('Here are the current supported commands.')
    print('get -top')
    print('get -sixty')
    print('get -quarter')
    print('get -diagnostics')
    print('get -vin ')

def init_diagnostics():
    #diagnostics_df = pd.read_csv("obd2_diagnostic_database.csv")
    #print(diagnostics_df.head())
    reader = csv.DictReader(open('obd2_diagnostic_database.csv','r'))
    diag_dict = []
    for line in reader:
        diag_dict.append(line)
    return diag_dict

def check_diagnostics(car,diag_dict,verbose=0):
    # STATE IDs for Diagnostic Test 
    # 0: Initialize
    # 1: Retrieve diagnostic codes
    # 2: Map DTC to Descriptions
    # 3: Report and Finished
    # 4: Error
    print("Check Diagnostics Test")
    DIAG_STATE = 0
    if verbose:
        print("STATE: 0")
    while DIAG_STATE == 0:
        car.write(DIAGNOSTICS)
        car.reset_input_buffer()
        car.readline()
        DIAG_STATE = 1
        if verbose:
            print("STATE: 1")
    time.sleep(0.1)
    data = []
    while car.in_waiting > 0:
        temp_data = []
        temp_data = car.readline()
        temp_data = str(temp_data)
        if "43" in temp_data:
            temp_data = temp_data.replace("b'","")
            temp_data = temp_data.replace("\\r\\n'","")
            data.append(temp_data)

    #print(data)
    if len(data) > 0:
        DIAG_STATE = 2
        if verbose:
            print("STATE: 2")
    else:
        DIAG_STATE = 4  
        if verbose:
            print("STATE: 4")

    while DIAG_STATE == 2:
        for line in data:
            print(line)
        #print(">> here I would map to database.")
        DIAG_STATE = 3
        if verbose:
            print("STATE: 3")
    
    return

if __name__ == '__main__':
    #diag_dict = init_diagnostics()
    main()
