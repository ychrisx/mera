from machine import Pin, PWM
import time
import bluetooth

# CONTROLE DE VELOCIDADE)
ENA = PWM(Pin(5), freq=1000)   # Motor direito
ENB = PWM(Pin(18), freq=1000)  # Motor esquerdo

# Velocidade 0 a 1023
vel_direito = 770
vel_esquerdo = 1020


# PINOS DE DIREÇÃO
A_1A = Pin(23, Pin.OUT)
A_1B = Pin(22, Pin.OUT)
B_1A = Pin(19, Pin.OUT)
B_1B = Pin(21, Pin.OUT)

# FUNÇÕES DE VELOCIDADE
def aplicar_velocidade(v_dir, v_esq):
    ENA.duty(v_dir)
    ENB.duty(v_esq)

# MOVIMENTO
def motores_frente():
    aplicar_velocidade(vel_direito, vel_esquerdo)
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)

def motores_tras():
    aplicar_velocidade(vel_direito, vel_esquerdo)
    A_1A.value(0); A_1B.value(1)
    B_1A.value(0); B_1B.value(1)

def curva_direita():
    aplicar_velocidade(vel_direito, vel_esquerdo)
    A_1A.value(0); A_1B.value(1)
    B_1A.value(1); B_1B.value(0)

def curva_esquerda():
    aplicar_velocidade(vel_direito, vel_esquerdo)
    A_1A.value(1); A_1B.value(0)
    B_1A.value(0); B_1B.value(1)

def parar_motores():
    ENA.duty(0)
    ENB.duty(0)
    A_1A.value(0); A_1B.value(0)
    B_1A.value(0); B_1B.value(0)

# BLUETOOTH
ble = bluetooth.BLE()
ble.active(True)

UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_UUID      = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX_UUID      = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

UART_SERVICE = (
    (UART_SERVICE_UUID, (
        (UART_TX_UUID, bluetooth.FLAG_NOTIFY),
        (UART_RX_UUID, bluetooth.FLAG_WRITE),
    )),
)

def bt_irq(event, data):
    if event == 1:
        print("Conectado")

    elif event == 2:
        print("Desconectado")
        start_advertising()

    elif event == 3:
        conn_handle, value_handle = data
        value = ble.gatts_read(value_handle)

        if value == b'\xff\x01\x01\x01\x02\x00\x01\x00':
            motores_frente()
        elif value == b'\xff\x01\x01\x01\x02\x00\x02\x00':
            motores_tras()
        elif value == b'\xff\x01\x01\x01\x02\x00\x04\x00':
            curva_esquerda()
        elif value == b'\xff\x01\x01\x01\x02\x00\x08\x00':
            curva_direita()
        else:
            parar_motores()

ble.irq(bt_irq)
ble.gatts_register_services(UART_SERVICE)

def start_advertising():
    name = "Clair Obscur: ESP 33"
    adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(name)+1, 0x09)) + name.encode()
    adv_data += bytearray(b'\x03\x03\x6E\x40')
    ble.gap_advertise(100, adv_data)

start_advertising()

while True:
    time.sleep(0.1)

