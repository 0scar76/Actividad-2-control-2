import socket
from socketUDP import SocketUDP
from slidingWindowCC import SlidingWindowCC as swcc
from CongestionControl import CongestionControl
import random

MAX_PACKET_SIZE = 16
MSS = 8 # no puede superar 16, porque recv lee de a 5 + 16 bytes
BYTES_NUM = 1
LIMIT = 30

WINDOW_SIZE = 8

class SocketTCP:
    def __init__(self, timeout=1, debug=False, max_timeouts=WINDOW_SIZE):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sckt.settimeout(timeout)
        self.sckt_gbn = SocketUDP() # unicamente usado en go back n (es la idea pa no implementar todo de nuevo para el nuevo socket, simplemente cambiarlo hacia tener que cambiar todo el codigo)
        self.sckt_gbn.settimeout(timeout)
        self.sckt_gbn.set_timer_list_length(max_timeouts)
        self.debug = debug

        self.last_send = None
        self.remote_address = None
        self.remote_address_gbn = ""
        self.message_remaining = b''
        self.len_msg = 0
        self.len_sended = 0
        self.message_seq = 0
        self.ip = None
        self.port = None
        self.congestion_control_on = False

    def set_congestion_control(self, value):
        self.congestion_control_on = value

    def parse_segment(self, message):
        SYN = 0
        ACK = 0
        FIN = 0

        flags = message[0]

        if (flags == 4) or (flags == 6):
            SYN = 1
        if (flags == 2) or (flags == 3) or (flags == 6):
            ACK = 1
        if (flags == 1) or (flags == 3):
            FIN = 1

        seq = int.from_bytes(message[1:5])
        data = message[5:len(message)]

        parsed_message = {
            "SYN": SYN,
            "ACK": ACK,
            "FIN": FIN,
            "seq": seq,
            "data": data
        }

        return parsed_message

    def create_segment(self, parsed_message):
        flags = 0
        
        if parsed_message["SYN"]:
            if parsed_message["ACK"]:
                flags = 6
            else:
                flags = 4
        elif parsed_message["ACK"]:
            if parsed_message["FIN"]:
                flags = 3
            else:
                flags = 2
        elif parsed_message["FIN"]:
            flags = 1
        
        flags = flags.to_bytes(1)
        seq = parsed_message["seq"].to_bytes(4)
        data = parsed_message["data"]
        final_message = flags + seq + data
        
        return final_message

    def connect(self, address):
        self.message_seq = random.randint(0, 100)

        first_shake = {
            "SYN": 1,
            "ACK": 0,
            "FIN": 0,
            "seq": self.message_seq,
            "data": b""
        }

        parsed_second = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": self.message_seq,
            "data": b""
        }

        limit = 0
        while parsed_second["SYN"] != 1 or parsed_second["ACK"] != 1 or parsed_second["seq"] != (self.message_seq + 1):
            self.sckt.sendto(self.create_segment(first_shake), address)
            if self.debug:
                print("envie:", first_shake)
            try:
                second_shake, server_address = self.sckt.recvfrom(5)
                parsed_second = self.parse_segment(second_shake)
                if self.debug:
                    print("recibi:", parsed_second)
                limit = 0
            except TimeoutError:
                if self.debug:
                    print("no pude recibir")
                limit += 1
                if limit == LIMIT:
                    if self.debug:
                        print("se supero el umbral de espera de mensajes, para no esperar eternamente voy a dejar de intentar")
                    return
            except:
                if self.debug:
                    print("ya se habia cerrado la conexion")
                return


        self.message_seq += 2

        third_shake = {
            "SYN": 0,
            "ACK": 1,
            "FIN": 0,
            "seq": self.message_seq,
            "data": b""
        }

        parsed_second_try = parsed_second

        while parsed_second == parsed_second_try:
            self.sckt.sendto(self.create_segment(third_shake), server_address)
            if self.debug:
                print("envie:", third_shake)
            try:
                second_shake_try, server_address = self.sckt.recvfrom(5)
                parsed_second_try = self.parse_segment(second_shake_try)
                if self.debug:
                    print("recibi:", parsed_second_try)
                limit = 0
            except TimeoutError:
                if self.debug:
                    print("no recibi nada")
                break
            except:
                if self.debug:
                    print("ya se habia cerrado la conexion")
                return

        self.last_send = third_shake
        self.remote_address = server_address

        print(f"Se conecto a {address}")

    def bind(self, address):
        self.sckt.bind(address)
        self.ip, self.port = address

    def accept(self):
        parsed_first = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": -1,
            "data": b""
        }

        while (parsed_first["SYN"] != 1 or parsed_first["ACK"] != 0):
            try:
                first_shake, server_address = self.sckt.recvfrom(5)
                parsed_first = self.parse_segment(first_shake)
                if self.debug:
                    print("recibi:", parsed_first)
            except TimeoutError:
                if self.debug:
                    print("no pude recibir")

        new_port = random.randint(8001, 9000)
        new_sckt = SocketTCP(debug=self.debug)
        new_sckt.bind((self.ip, new_port))
        self.message_seq = parsed_first["seq"] + 1

        second_shake = {
            "SYN": 1,
            "ACK": 1,
            "FIN": 0,
            "seq": self.message_seq,
            "data": b""
        }

        parsed_third = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": -1,
            "data": b""
        }
        second_server = ""

        limit = 0
        while (parsed_third["SYN"] != 0 or
                 parsed_third["ACK"] != 1 or
                 parsed_third["seq"] != self.message_seq + 1 or
                 second_server != server_address):
            new_sckt.sckt.sendto(self.create_segment(second_shake), server_address)
            if self.debug:
                print("envie:", second_shake)
            try:
                third_shake, second_server = new_sckt.sckt.recvfrom(5)
                parsed_third = self.parse_segment(third_shake)
                if self.debug:
                    print("recibi:", parsed_third)
                limit = 0
            except TimeoutError:
                if self.debug:
                    print("no pude recibir")
                limit += 1
                if limit == LIMIT:
                    if self.debug:
                        print("se supero el umbral de espera de mensajes, para no esperar eternamente voy a cerrar nomas")
                    self.close()
                    return
            except:
                if self.debug:
                    print("ya se habia cerrado la conexion")
                return

        new_sckt.remote_address = server_address

        sv_ip, sv_prt = server_address

        new_sckt.message_seq = parsed_third["seq"]
        print("se establecio conexion")
        return new_sckt, (self.ip, new_port)

    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            return self.send_using_go_back_n(message)

    def recv_using_stop_and_wait(self, buff_size):
        while self.len_msg == 0:
            parsed_first = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": -1,
                "data": b''
            }
            sender = ""
        
            limit = 0
            while sender != self.remote_address or parsed_first["seq"] != self.message_seq:
                try:
                    first_message, sender = self.sckt.recvfrom(5 + 16)
                    parsed_first = self.parse_segment(first_message)
                    if self.debug:
                        print("recibi:", parsed_first)
                    limit = 0
                    if parsed_first["FIN"] == 1:
                        if self.debug:
                            print("se recibio mensaje de cierre")
                            print("se acabo recv")
                        self.recv_close()
                        return b''
                    if parsed_first["ACK"] == 1:
                        continue
                    if parsed_first["seq"] > 0 and parsed_first["seq"] < self.message_seq and sender == self.remote_address:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")
                    limit += 1
                    if limit == LIMIT:
                        if self.debug:
                            print("se supero el umbral de espera de mensajes, para no recibir eternamente voy a cerrar nomas")
                            print("se acabo recv")
                        self.close()
                        return b''
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return b''
        
            self.len_msg = int.from_bytes(parsed_first["data"]) # si sali del while recibi el mensaje correcto
            self.message_seq += len(parsed_first["data"])
        
            first_response = {
                "SYN": 0,
                "ACK": 1,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b''
            }
        
            self.sckt.sendto(self.create_segment(first_response), self.remote_address)
            if self.debug:
                print("envie:", first_response)
        
            self.last_send = first_response
        
        message = b''
        while (len(message) != min(self.len_msg, buff_size)):
            if self.message_remaining != b'':
                if len(self.message_remaining) >= min(self.len_msg, buff_size):
                    message += self.message_remaining[0:min(self.len_msg, buff_size)]
                    self.message_remaining = self.message_remaining[min(self.len_msg, buff_size):]
                else:
                    message += self.message_remaining
                    self.message_remaining = b''
                continue
        
            parsed_act = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": self.message_seq - 1,
                "data": b''
            }
            sender = ""
        
            limit = 0
            while sender != self.remote_address or parsed_act["seq"] != self.message_seq:
                try:
                    act_message, sender = self.sckt.recvfrom(5 + 16)
                    parsed_act = self.parse_segment(act_message)
                    if self.debug:
                        print("recibi:", parsed_act)
                    limit = 0
                    if parsed_act["FIN"] == 1:
                        if self.debug:
                            print("se recibio mensaje de cierre")
                            print("se acabo recv")
                        self.recv_close()
                        return b''
                    if parsed_act["seq"] < self.message_seq:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")
                    limit += 1
                    if limit == LIMIT:
                        if self.debug:
                            print("se supero el umbral de espera de mensajes, para no recibir eternamente voy a cerrar nomas")
                            print("se acabo recv")
                        self.close()
                        return b''
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return b''
        
            if len(parsed_act["data"] + message) > min(self.len_msg, buff_size):
                self.message_remaining = parsed_act["data"][min(self.len_msg, buff_size) - len(message):]
                message += parsed_act["data"][0:min(self.len_msg, buff_size) - len(message)]
            else:
                message += parsed_act["data"]
            self.message_seq += len(parsed_act["data"])
        
            acknowledge = {
                "SYN": 0,
                "ACK": 1,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b''
            }
        
            self.sckt.sendto(self.create_segment(acknowledge), self.remote_address)
            if self.debug:
                print("envie:", acknowledge)
            self.last_send = acknowledge
        
            if (len(message) == min(self.len_msg, buff_size)) or (self.len_sended + len(message) == self.len_msg):
                self.len_sended += len(message)
                if self.len_sended == self.len_msg:
                    self.len_msg = 0
                    self.len_sended = 0
                    break
        
        if self.debug:
            print("se acabo recv")
        return message

    def send_using_stop_and_wait(self, message):
        msg_len = len(message)
        
        first_message = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": self.message_seq,
            "data": msg_len.to_bytes(BYTES_NUM)
        }
        
        parsed_response = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": self.message_seq,
            "data": b''
        }
        sender = ""
        
        limit = 0
        while sender != self.remote_address or parsed_response["seq"] != self.message_seq + len(first_message["data"]):
            try:
                self.sckt.sendto(self.create_segment(first_message), self.remote_address)
            except:
                if self.debug:
                    print("ya se habia cerrado la conexion")
                return
            if self.debug:
                print("envie:", first_message)
            try:
                first_response, sender = self.sckt.recvfrom(5 + 16)
                parsed_response = self.parse_segment(first_response)
                if self.debug:
                    print("recibi:", parsed_response)
                limit = 0
                if parsed_response["FIN"] == 1:
                    if self.debug:
                        print("se recibio mensaje de cierre")
                        print("se acabo send")
                    self.recv_close()
                    return
                if parsed_response["SYN"] == 1 and parsed_response["ACK"] == 1:
                    self.sckt.sendto(self.create_segment(self.last_send), self.remote_address)
                    if self.debug:
                        print("envie:", self.last_send)
            except TimeoutError:
                if self.debug:
                    print("no recibi nada")
                limit += 1
                if limit == LIMIT:
                    if self.debug:
                        print("se supero el umbral de mensajes enviados, para no enviar eternamente voy a cerrar nomas")
                        print("se acabo send")
                    self.close()
                    return
            except:
                if self.debug:
                    print("ya se habia cerrado la conexion")
                return
        
        
        new_seq = parsed_response["seq"]
        self.message_seq = new_seq
        
        start = 0
        chunk = message[0:MAX_PACKET_SIZE]
        
        while (start < msg_len):
            parsed_message = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": self.message_seq,
                "data": chunk.encode("utf-8") if type(chunk) == str else chunk
            }
        
            parsed_response = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b""
            }
            sender = ""
        
            limit = 0
            while sender != self.remote_address or parsed_response["seq"] != self.message_seq + len(chunk):
                try:
                    self.sckt.sendto(self.create_segment(parsed_message), self.remote_address)
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return
                if self.debug:
                    print("envie:", parsed_message)
                try:
                    act_response, sender = self.sckt.recvfrom(5 + 16)
                    parsed_response = self.parse_segment(act_response)
                    if self.debug:
                        print("recibi:", parsed_response)
                    limit = 0
                    if parsed_response["FIN"] == 1:
                        if self.debug:
                            print("se recibio mensaje de cierre")
                            print("se acabo send")
                        self.recv_close()
                        return
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")
                    limit += 1
                    if limit == LIMIT:
                        if self.debug:
                            print("se supero el umbral de mensajes enviados, para no enviar eternamente voy a cerrar nomas")
                            print("se acabo send")
                        self.close()
                        return 
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return
        
            start += MAX_PACKET_SIZE
            chunk = message[start:(start + MAX_PACKET_SIZE)]
        
            new_seq = parsed_response["seq"]
            self.message_seq = new_seq
        
        if self.debug:
            print("se acabo send")
        return

    def recv_using_go_back_n(self, buff_size):
        while self.len_msg == 0:
            parsed_first = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": -1,
                "data": b''
            }
            sender = ""
        
            limit = 0
            while sender != self.remote_address_gbn or parsed_first["seq"] != self.message_seq:
                try:
                    first_message, sender = self.sckt.recvfrom(5 + 16)
                    parsed_first = self.parse_segment(first_message)
                    if self.remote_address_gbn == "":
                        sender_gbn_ip, sender_gbn_port = sender
                        sender_ip, sender_port = self.remote_address
                        if sender_ip == sender_gbn_ip: # si son la misma ip confio que es el puerto que usa el socketUDP
                            self.remote_address_gbn = (sender_gbn_ip, sender_gbn_port)
                    if self.debug:
                        print("recibi:", parsed_first)
                    limit = 0
                    if parsed_first["FIN"] == 1:
                        if self.debug:
                            print("se recibio mensaje de cierre")
                            print("se acabo recv")
                        self.recv_close()
                        return b''
                    if parsed_first["ACK"] == 1:
                        continue
                    if parsed_first["seq"] > 0 and parsed_first["seq"] < self.message_seq and sender == self.remote_address_gbn:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address_gbn)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")
                    limit += 1
                    if limit == LIMIT:
                        if self.debug:
                            print("se supero el umbral de espera de mensajes, para no recibir eternamente voy a cerrar nomas")
                            print("se acabo recv")
                        self.close()
                        return b''
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return b''
        
            self.len_msg = int.from_bytes(parsed_first["data"]) # si sali del while recibi el mensaje correcto
        
            first_response = {
                "SYN": 0,
                "ACK": 1,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b''
            }
            self.message_seq += len(parsed_first["data"])
        
            self.sckt.sendto(self.create_segment(first_response), self.remote_address_gbn)
            if self.debug:
                print("envie:", first_response)
        
            self.last_send = first_response
        
        message = b''
        while (len(message) != min(self.len_msg, buff_size)):
            if self.message_remaining != b'':
                if len(self.message_remaining) >= min(self.len_msg, buff_size):
                    message += self.message_remaining[0:min(self.len_msg, buff_size)]
                    self.message_remaining = self.message_remaining[min(self.len_msg, buff_size):]
                else:
                    message += self.message_remaining
                    self.message_remaining = b''
                continue
        
            parsed_act = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": self.message_seq - 1,
                "data": b''
            }
            sender = ""
        
            limit = 0
            while sender != self.remote_address_gbn or parsed_act["seq"] != self.message_seq:
                try:
                    act_message, sender = self.sckt.recvfrom(5 + 16)
                    parsed_act = self.parse_segment(act_message)
                    if self.debug:
                        print("recibi:", parsed_act)
                    limit = 0
                    if parsed_act["FIN"] == 1:
                        if self.debug:
                            print("se recibio mensaje de cierre")
                            print("se acabo recv")
                        self.recv_close()
                        return b''
                    if parsed_act["seq"] < self.message_seq:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address_gbn)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")
                    limit += 1
                    if limit == LIMIT:
                        if self.debug:
                            print("se supero el umbral de espera de mensajes, para no recibir eternamente voy a cerrar nomas")
                            print("se acabo recv")
                        self.close()
                        return b''
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return b''
        
            if len(parsed_act["data"] + message) > min(self.len_msg, buff_size):
                self.message_remaining = parsed_act["data"][min(self.len_msg, buff_size) - len(message):]
                message += parsed_act["data"][0:min(self.len_msg, buff_size) - len(message)]
            else:
                message += parsed_act["data"]
        
            acknowledge = {
                "SYN": 0,
                "ACK": 1,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b''
            }
            self.message_seq += len(parsed_act["data"])
        
            self.sckt.sendto(self.create_segment(acknowledge), self.remote_address_gbn)
            if self.debug:
                print("envie:", acknowledge)
            self.last_send = acknowledge
        
            if (len(message) == min(self.len_msg, buff_size)) or (self.len_sended + len(message) == self.len_msg):
                self.len_sended += len(message)
                if self.len_sended == self.len_msg:
                    self.len_msg = 0
                    self.len_sended = 0
                    break
        
        if self.debug:
            print("se acabo recv")
        return message

    def send_using_go_back_n(self, message):
        msg_len = len(message)
        data_list = [msg_len.to_bytes(BYTES_NUM)]

        # el mensaje se divide en trozos de tamaño MSS
        for i in range(0, msg_len, MSS):
            data_list.append(message[i:i + MSS])

        congestion_controller = CongestionControl(MSS)
        if self.congestion_control_on:
            window_size = int(congestion_controller.get_MSS_in_cwnd())
        else:
            window_size = WINDOW_SIZE
        data_window = swcc(window_size, data_list, self.message_seq)
        end_seq = self.message_seq
        for data in data_list:
            end_seq += len(data)
        self.sckt_gbn.set_timer_list_length(len(data_list))

        base = 0
        next_to_send = 0
        timeouts = 0

        while data_window.get_data(0) is not None:
            while next_to_send < len(data_list) and next_to_send - base < window_size:
                wnd_index = next_to_send - base
                segment = {
                    "SYN": 0,
                    "ACK": 0,
                    "FIN": 0,
                    "seq": data_window.get_sequence_number(wnd_index),
                    "data": data_window.get_data(wnd_index)
                }
                self.sckt_gbn.sendto(self.create_segment(segment), self.remote_address, timer_index=next_to_send)
                if self.debug:
                    print("envie:", segment)
                next_to_send += 1

            try:
                answer, sender = self.sckt_gbn.recvfrom(5 + 16)
                parsed_ans = self.parse_segment(answer)
                if self.debug:
                    print("recibi:", parsed_ans)
                if sender != self.remote_address or parsed_ans["ACK"] != 1:
                    continue

                ack_seq = parsed_ans["seq"]
                if ack_seq < data_window.get_sequence_number(0):
                    continue

                # si el ACK es mayor que el ultimo seq de la ventana, se mueve la ventana completa
                steps = 0
                while data_window.get_data(0) is not None:
                    for i in range(window_size):
                        if data_window.get_data(i) is not None and data_window.get_sequence_number(i) == ack_seq:
                            steps = i + 1
                            break
                    if steps > 0:
                        break

                    last_seq = data_window.get_sequence_number(window_size - 1)
                    if last_seq is None or ack_seq < last_seq:
                        break

                    for data_index in range(base, min(base + window_size, next_to_send)):
                        self.sckt_gbn.stop_timer(timer_index=data_index)
                    data_window.move_window(window_size)
                    base += window_size

                if steps > 0:
                    for data_index in range(base, min(base + steps, next_to_send)):
                        self.sckt_gbn.stop_timer(timer_index=data_index)
                    data_window.move_window(steps)
                    base += steps

                next_to_send = max(next_to_send, base)
                timeouts = 0

                if self.congestion_control_on:
                    congestion_controller.event_ack_received()
                    window_size = int(congestion_controller.get_MSS_in_cwnd())
                    data_window.update_window_size(window_size)
                    if self.debug:
                        print("cwnd:", congestion_controller.get_cwnd(), "window_size:", window_size)

                if data_window.get_data(0) is not None:
                    self.message_seq = data_window.get_sequence_number(0)

            except TimeoutError:
                if self.debug:
                    print("no pude recibir")

                # si se perdio el ultimo ACK del handshake, el server sigue mandando SYN-ACK al socket normal
                # se revisa rapido (0.01 s) para no alargar cada timeout
                normal_timeout = self.sckt.gettimeout()
                self.sckt.settimeout(0.01)
                try:
                    msg, snd = self.sckt.recvfrom(5)
                    parsed_msg = self.parse_segment(msg)
                    if self.debug:
                        print("recibi:", parsed_msg)
                    if snd == self.remote_address and parsed_msg["SYN"] == 1 and parsed_msg["ACK"] == 1:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    pass
                self.sckt.settimeout(normal_timeout)

                timeouts += 1
                if timeouts == LIMIT:
                    if self.debug:
                        print("se supero el umbral de espera de mensajes, para no enviar eternamente voy a cerrar nomas")
                        print("se acabo send")
                    self.close()
                    return
                for data_index in range(base, next_to_send):
                    self.sckt_gbn.stop_timer(timer_index=data_index)

                if self.congestion_control_on:
                    congestion_controller.event_timeout()
                    window_size = int(congestion_controller.get_MSS_in_cwnd())
                    data_window.update_window_size(window_size)
                    if self.debug:
                        print("cwnd:", congestion_controller.get_cwnd(), "window_size:", window_size)

                next_to_send = base

        self.message_seq = end_seq

    def close(self):
        try:
            attempts = 3
            parsed_response = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": -1,
                "data": b""
            }
            sender = ""

            while (attempts > 0 and (sender != self.remote_address or parsed_response["seq"] != self.message_seq)):
                last_response, sender = self.sckt.recvfrom(5 + 16)
                parsed_response = self.parse_segment(last_response)
                if self.debug:
                    print("recibi:", parsed_response)
                if parsed_response["SYN"] == 0 and parsed_response["ACK"] == 0 and parsed_response["FIN"] == 0:
                    # si el dato viene del socket de go back n, el ACK se devuelve a ese socket
                    if sender == self.remote_address_gbn:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address_gbn)
                    else:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address)
                    if self.debug:
                        print("envie:", self.last_send)
                    parsed_response = {
                        "SYN": 0,
                        "ACK": 0,
                        "FIN": 0,
                        "seq": -1,
                        "data": b""
                    }
                    sender = ""
                attempts -= 1

            self.message_seq += 1
            if parsed_response["FIN"] == 0:
                if self.debug:
                    print("yo hago el cierre")

                msg_close = {
                    "SYN": 0,
                    "ACK": 0,
                    "FIN": 1,
                    "seq": self.message_seq,
                    "data": b''
                }

                parsed_finack = {
                    "SYN": 0,
                    "ACK": 0,
                    "FIN": 0,
                    "seq": -1,
                    "data": b""
                }
                sender = ""

                attempts = 3
                while attempts > 0 and (sender != self.remote_address or parsed_finack["seq"] != self.message_seq + 1 or parsed_finack["ACK"] != 1 or parsed_finack["FIN"] != 1):
                    self.sckt.sendto(self.create_segment(msg_close), self.remote_address)
                    if self.debug:
                        print("envie:", msg_close)
                    attempts -= 1
                    try:
                        finack, sender = self.sckt.recvfrom(5 + 16)
                        parsed_finack = self.parse_segment(finack)
                        if self.debug:
                            print("recibi:", parsed_finack)
                        # el emisor de go back n sigue reenviando datos porque se perdio el ultimo ACK
                        if sender == self.remote_address_gbn and parsed_finack["SYN"] == 0 and parsed_finack["ACK"] == 0 and parsed_finack["FIN"] == 0:
                            self.sckt.sendto(self.create_segment(self.last_send), self.remote_address_gbn)
                            if self.debug:
                                print("envie:", self.last_send)
                    except TimeoutError:
                        if self.debug:
                            print("no recibi nada")

                if (attempts <= 0 and (sender != self.remote_address or parsed_finack["seq"] != self.message_seq + 1 or parsed_finack["ACK"] != 1 or parsed_finack["FIN"] != 1)):
                    if self.debug:
                        print("Se acabaron los intentos, asumo que el otro quiere cerrar conexion")

                    self.sckt.close()
                    self.sckt_gbn.close()
                    print("se cerro la conexion")
                    return

                self.message_seq = parsed_finack["seq"] + 1

                acknowledge = {
                    "SYN": 0,
                    "ACK": 1,
                    "FIN": 0,
                    "seq": self.message_seq,
                    "data": b''
                }

                for _ in range(3):
                    self.sckt.sendto(self.create_segment(acknowledge), self.remote_address)
                    if self.debug:
                        print("envie:", acknowledge)
                    try:
                        last, sender = self.sckt.recvfrom(5 + 16)
                        parsed_last = self.parse_segment(last)
                        if self.debug:
                            print("recibi:", parsed_last)
                    except TimeoutError:
                        if self.debug:
                            print("no recibi nada")


                self.sckt.close()
                self.sckt_gbn.close()
                print("se cerro la conexion")

            else: # yo no hago el cierre, quedo algo pendiente pero yo no quiero mas
                self.message_seq = parsed_response["seq"] + 1
                self.recv_close()
        except TimeoutError:
            if self.debug:
                print("yo hago el cierre")

            msg_close = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 1,
                "seq": self.message_seq,
                "data": b''
            }

            parsed_finack = {
                "SYN": 0,
                "ACK": 0,
                "FIN": 0,
                "seq": -1,
                "data": b""
            }
            sender = ""
            
            attempts = 3
            while attempts > 0 and (sender != self.remote_address or parsed_finack["seq"] != self.message_seq + 1 or parsed_finack["ACK"] != 1 or parsed_finack["FIN"] != 1):
                try:
                    self.sckt.sendto(self.create_segment(msg_close), self.remote_address)
                except:
                    if self.debug:
                        print("ya se habia cerrado la conexion")
                    return
                if self.debug:
                    print("envie:", msg_close)
                attempts -= 1
                try:
                    finack, sender = self.sckt.recvfrom(5 + 16)
                    parsed_finack = self.parse_segment(finack)
                    if self.debug:
                        print("recibi:", parsed_finack)
                    # el emisor de go back n sigue reenviando datos porque se perdio el ultimo ACK
                    if sender == self.remote_address_gbn and parsed_finack["SYN"] == 0 and parsed_finack["ACK"] == 0 and parsed_finack["FIN"] == 0:
                        self.sckt.sendto(self.create_segment(self.last_send), self.remote_address_gbn)
                        if self.debug:
                            print("envie:", self.last_send)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")

            if (attempts <= 0 and (sender != self.remote_address or parsed_finack["seq"] != self.message_seq + 1 or parsed_finack["ACK"] != 1 or parsed_finack["FIN"] != 1)):
                if self.debug:
                    print("Se acabaron los intentos, asumo que el otro quiere cerrar conexion")

                self.sckt.close()
                self.sckt_gbn.close()
                print("se cerro la conexion")
                return

            self.message_seq = parsed_finack["seq"] + 1

            acknowledge = {
                "SYN": 0,
                "ACK": 1,
                "FIN": 0,
                "seq": self.message_seq,
                "data": b''
            }

            for _ in range(3):
                self.sckt.sendto(self.create_segment(acknowledge), self.remote_address)
                if self.debug:
                    print("envie:", acknowledge)
                try:
                    last, sender = self.sckt.recvfrom(5 + 16)
                    parsed_last = self.parse_segment(last)
                    if self.debug:
                        print("recibi:", parsed_last)
                except TimeoutError:
                    if self.debug:
                        print("no recibi nada")

            self.sckt.close()
            self.sckt_gbn.close()
            print("se cerro la conexion")
        except:
            if self.debug:
                print("ya se habia cerrado la conexion")

        return

    def recv_close(self):
        if self.debug:
            print("yo recibo el cierre")

        msg_close = {
            "SYN": 0,
            "ACK": 1,
            "FIN": 1,
            "seq": self.message_seq,
            "data": b''
        }

        recv_fin = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 0,
            "seq": -1,
            "data": b""
        }
        sender = ""

        attempts = 3
        while attempts > 0 and (sender != self.remote_address or recv_fin["seq"] != self.message_seq + 1 or recv_fin["ACK"] != 1):
            self.sckt.sendto(self.create_segment(msg_close), self.remote_address)
            if self.debug:
                print("envie:", msg_close)
            attempts -= 1
            try:
                fin, sender = self.sckt.recvfrom(5 + 16)
                recv_fin = self.parse_segment(fin)
                if self.debug:
                    print("recibi:", recv_fin)
            except TimeoutError:
                if self.debug:
                    print("no recibi nada")

        if (attempts <= 0 and (sender != self.remote_address or recv_fin["seq"] != self.message_seq + 1 or recv_fin["ACK"] != 1)):
            if self.debug:
                print("Se acabaron los intentos, asumo que el otro quiere cerrar conexion")
        
            self.sckt.close()
            self.sckt_gbn.close()
            print("se cerro la conexion")
            return

        self.sckt.close()
        print("se cerro la conexion")

        return
