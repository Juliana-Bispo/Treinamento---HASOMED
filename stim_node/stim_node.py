import time
import numpy as np
import sys
import serial
import struct

class StimNode:   # Antes com o ROS era Class StimNode(Node):

    PORT = "/dev/stim"
    # channels used as low frequency 
    CHANNEL_LF = []
    # stimulation frequency
    FREQ = 50
    # skip sequence of stimulation without changing the frequency
    # 0 = no skips
    N_FACTOR = 0
    #...
    GROUP_TIME = 0
    # stim mode 0 == "single"
    STIM_MODE = 0

    command_dict = {
        'channelListModeInitialization': {
            'id': 0,
            'field_bit_sizes': {'Ident':2, 'Check':3, 'N_Factor':3, 'Channel_Stim':8, 'Channel_Lf':8, 'X': 2, 'Group_Time':5, 'Main_Time':11}
        },
        'channelListModeUpdate': {
            'id': 1,
            'field_bit_sizes': {'Ident':2, 'Check':5,
                        'Mode1':2, 'X1':3, 'Pulse_Width1':9, 'Pulse_Current1':7,
                        'Mode2':2, 'X2':3, 'Pulse_Width2':9, 'Pulse_Current2':7,
                        'Mode3':2, 'X3':3, 'Pulse_Width3':9, 'Pulse_Current3':7,
                        'Mode4':2, 'X4':3, 'Pulse_Width4':9, 'Pulse_Current4':7,
                        'Mode5':2, 'X5':3, 'Pulse_Width5':9, 'Pulse_Current5':7,
                        'Mode6':2, 'X6':3, 'Pulse_Width6':9, 'Pulse_Current6':7,
                        'Mode7':2, 'X7':3, 'Pulse_Width7':9, 'Pulse_Current7':7,
                        'Mode8':2, 'X8':3, 'Pulse_Width8':9, 'Pulse_Current8':7}
        },
        'channelListModeStop': {
            'id': 2,
            'field_bit_sizes': {'Ident':2, 'Check':5}
        },
        'singlePulseGeneration': {
            'id': 3,
            'field_bit_sizes': {'Ident':2, 'Check':5, 'Channel_Number':3, 'X': 2, 'Pulse_Width':9,  'Pulse_Current':7}
        }
    }

    channel_stim = []

    def __init__(self):
         self.serial_port = serial.Serial(
            port=self.PORT, 
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            rtscts=True
        ) 
    print("[INFO] StimNode inicializado")

    
    #
        

    def set_channel_byte(self,bit_list, channel_list):
        for channel in channel_list:
            bit_list |= (0b00000001 << channel-1)

        return bit_list

    def clear_bit(self,cleared_bit_list, bit_list):
        for bit in bit_list:
            cleared_bit_list &= ~(1 << bit)

        return cleared_bit_list


    def create_command(self,cmd_name, field_values):
        command = self.command_dict[cmd_name]

        bit_count = 0
        command_bytes = []

        # starting byte has bit 7 set, all others have bit 7 clear
        command_byte = 0b10000000

        field_names = field_values.keys()

        for field_name in field_names:
            # if field is not present, just move on
            # (added because of variable packet size in update command)
            try:
                field_value = field_values[field_name]
                field_bit_size = command['field_bit_sizes'][field_name]
                
            except KeyError:
                continue

            # if field is a filler ('X'), just update bit_count and move on
            # Q Q TA ROLANDO AQUI!!!????
            if field_name == 'X':
                bit_count += command['field_bit_sizes'][field_name]
            
            else:
                # figure out where the field should be placed in byte
                shift = 7 - (bit_count + field_bit_size)

                # field fits in current command_byte or should be split
                if shift >= 0:
                    # insert field_value in the right place in command_byte
                    command_byte |= field_value << shift
                    bit_count += field_bit_size

                    # check if byte is full and we should start a new one
                    if bit_count == 7:
                        command_bytes.append(command_byte)
                        command_byte = 0b00000000
                        bit_count = 0
                else:
                    # field is split! get the size and shift of each part
                    current_field_bit_size = field_bit_size + shift
                    next_field_bit_size = -shift

                    shift_right = -shift
                    shift_left = 7 - next_field_bit_size

                    # insert field_value in the right place in current command_byte
                    command_byte |= field_value >> shift_right
                    

                    # append current command_byte to command_bytes
                    command_bytes.append(command_byte)
                    command_byte = 0b00000000
                    bit_count = 0

                    # clear bits in field_value that have already been used
                    field_value = self.clear_bit(field_value, 
                                    range(-shift,field_bit_size))

                    # insert remaining field_value in the right place in command_byte
                    command_byte |= field_value << shift_left
                    bit_count += next_field_bit_size
                    

                    # check if byte is full and we should start a new one
                    if bit_count == 7:
                        command_bytes.append(command_byte)
                        command_byte = 0b00000000
                        bit_count = 0       

        return bytearray(command_bytes)   

    def write_read_command(self,command_bytes):
        
        try:
            
            self.serial_port.write(command_bytes)
            
        except:
            print('failed to write to stimulator serial port')
            raise
        

        while(self.serial_port.in_waiting<1): pass


        try:                            
            ack = struct.unpack('B', self.serial_port.read(1))[0]
            self.get_logger().info(f"ack -> {ack}")  
        except Exception as error:
            self.get_logger().info(f"ack -> {error}") 

        #for _ in range(10):
        #    try:
        #        ack = struct.unpack('B', self.serial_port.read(1))[0]
        #        self.get_logger().info(f"ack -> {ack}")
        #    except Exception as error:
        #        self.get_logger().info(f"ack -> {error}")

        # DEIXEI ESSAS COISAS COMENTADAS AQUI POR ENQUANTO CASO PRECISE
        # print('ack', '{0:08b}'.format(ack))
        #ident = ack >> 6

        error_code = ack & 1
        # print(f"Error Code: {error_code}")
        # print('ident', reverse_command_dict[ident])
        # print('error_code', error_code)

        return {0: False, 1: True}[error_code] 


        # retorna de houve erro 
        #return True*error_code

########################### ADICIONAR FLUSH ##############################################################
    def initialize_ccl(self, channels):
        
        self.channel_stim = channels 

        # Command name
        cmd_name = 'channelListModeInitialization'
        # Command identifier
        ident = self.command_dict[cmd_name]['id']

        channel_stim_byte = self.set_channel_byte(0,self.channel_stim)
        channel_lf_byte = self.set_channel_byte(0,self.CHANNEL_LF)

        # get ts1 from frequency - equation from manual
        ts1 = round((1/float(self.FREQ))*1000)
        # equation from stim manual
        main_time = int(round((ts1 - 1.0) / 0.5))

        # check_sum size = 3 bits 
        check_sum = (self.N_FACTOR + channel_stim_byte + channel_lf_byte 
                    + self.GROUP_TIME + main_time) % 8


        field_values = {
            'Ident': ident,
            'Check': check_sum,
            'N_Factor': self.N_FACTOR,
            'Channel_Stim': channel_stim_byte,
            'Channel_Lf': channel_lf_byte,
            'X': 0 ,#filler
            'Group_Time': self.GROUP_TIME,
            'Main_Time': main_time
            
        }

        # create command in the specific format 
        command_bytes = self.create_command(cmd_name, field_values)
        # write command
        success = self.write_read_command(command_bytes)
        self.get_logger().info(f"response:{success}   |")
        
        return success


    def update_ccl(self,pulse_width, pulse_current):

        # Command name
        cmd_name = 'channelListModeUpdate'
        # Command identifier
        ident = self.command_dict[cmd_name]['id']


        check_sum = 0


        field_values = {
            'Ident': ident,
            'Check': check_sum
        }

        for idx in range(len(self.channel_stim)):
            channel_num = str(self.channel_stim[idx])
            
            field_values['Mode' + channel_num] = self.STIM_MODE
            field_values['X' + channel_num] = 0 # filler
            field_values['Pulse_Width' + channel_num] = pulse_width[idx]
            field_values['Pulse_Current' + channel_num] = pulse_current[idx]
            check_sum += self.STIM_MODE
            check_sum += pulse_width[idx]
            check_sum += pulse_current[idx]

        check_sum = check_sum % 32
        field_values['Check'] = check_sum


        command_bytes = self.create_command(cmd_name, field_values)

        return self.write_read_command(command_bytes)


    def stop_ccl(self):
        # Command name
        cmd_name = 'channelListModeStop'
        # Command identifier
        ident = self.command_dict[cmd_name]['id']

        check = 0

        field_values = {
            'Ident': ident,
            'Check': check
        }

        command_bytes = self.create_command(cmd_name,field_values)
        success = self.write_read_command(command_bytes)

        return success


    def ccl_callback(self,request):
        print(request)
        self.update_ccl(request.pulse_width, request.pulse_current)
        


def main(args=None):
    #rclpy.init(args=args)

    stim_object = StimNode()
    channels = [1]

    stim_object.initialize_ccl(channels)

    pulse_width = [100]
    pulse_current = [5]

    stim_object.update_ccl(pulse_width,pulse_current)

    time.delay(5)

    stim_object.stop_ccl()


if __name__ == '__main__':
    main()
