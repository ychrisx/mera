from machine import Pin, PWM
import time
from time import sleep_ms
import bluetooth

# ==========================================
# CONFIGURAÇÕES DE HARDWARE (PONTE H L298N)
# ==========================================
# Motor Direito
A_1A = Pin(23, Pin.OUT)   # IN1
A_1B = Pin(22, Pin.OUT)   # IN2
ENA  = PWM(Pin(5))        # ENA
ENA.freq(20000)           # Frequência para modo silencioso

# Motor Esquerdo
B_1A = Pin(19, Pin.OUT)   # IN4
B_1B = Pin(21, Pin.OUT)   # IN3
ENB  = PWM(Pin(18))       # ENB
ENB.freq(20000)

# ==========================================
# SENSORES (TCRT)
# ==========================================
sensor_esquerdo = Pin(4, Pin.IN)
sensor_direito  = Pin(27, Pin.IN)

# ==========================================
# PARÂMETROS E VELOCIDADES
# ==========================================
BLACK_LEVEL = 1      
VEL_BASE = 850       
VEL_CURVA = 1023     
VEL_FREIO = 1023     

# Velocidades específicas do código Bluetooth
vel_direito_bt = 770
vel_esquerdo_bt = 1020

# ==========================================
# FUNÇÕES DE MOVIMENTO (SISTEMA INTEGRADO)
# ==========================================
def aplicar_velocidade(v_dir, v_esq):
    ENA.duty(v_dir)
    ENB.duty(v_esq)

def motores_frente_bt():
    aplicar_velocidade(vel_direito_bt, vel_esquerdo_bt)
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)

def motores_tras_bt():
    aplicar_velocidade(vel_direito_bt, vel_esquerdo_bt)
    A_1A.value(0); A_1B.value(1)
    B_1A.value(0); B_1B.value(1)

def curva_direita_bt():
    aplicar_velocidade(vel_direito_bt, vel_esquerdo_bt)
    A_1A.value(0); A_1B.value(1)
    B_1A.value(1); B_1B.value(0)

def curva_esquerda_bt():
    aplicar_velocidade(vel_direito_bt, vel_esquerdo_bt)
    A_1A.value(1); A_1B.value(0)
    B_1A.value(0); B_1B.value(1)

# Funções Originais do Segue Linha
def motores_frente_linha(v):
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(v)
    ENB.duty(v)

def virar_esquerda_linha(v):
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(int(v / 2))
    ENB.duty(v)

def virar_direita_linha(v):
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(v)
    ENB.duty(int(v / 2))

def parar_motores():
    # Mantendo a lógica de freio brusco do arquivo original
    A_1A.value(1); A_1B.value(1)
    B_1A.value(1); B_1B.value(1)
    ENA.duty(VEL_FREIO)
    ENB.duty(VEL_FREIO)
    sleep_ms(240)
    ENA.duty(0); ENB.duty(0)
    # Garante pinos em LOW após o freio
    A_1A.value(0); A_1B.value(0)
    B_1A.value(0); B_1B.value(0)

# ==========================================
# CONFIGURAÇÃO BLUETOOTH (BLE)
# ==========================================
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
            motores_frente_bt()
        elif value == b'\xff\x01\x01\x01\x02\x00\x02\x00':
            motores_tras_bt()
        elif value == b'\xff\x01\x01\x01\x02\x00\x04\x00':
            curva_esquerda_bt()
        elif value == b'\xff\x01\x01\x01\x02\x00\x08\x00':
            curva_direita_bt()
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

# ==========================================
# LOOP PRINCIPAL (MODO SEGUE LINHA)
# ==========================================
while True:
    esq = sensor_esquerdo.value()
    dir = sensor_direito.value()

    # Lógica de seguir o BRANCO (do primeiro código)
    if esq == 0 and dir == 0:
        motores_frente_linha(VEL_BASE)
    elif esq == 1 and dir == 0:
        virar_direita_linha(VEL_CURVA)
    elif esq == 0 and dir == 1:
        virar_esquerda_linha(VEL_CURVA)
    else:
        parar_motores()

    sleep_ms(5)
