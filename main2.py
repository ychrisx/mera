from machine import Pin, PWM
import time
import bluetooth

# =============================
# ESTADO GLOBAL DO ROBÔ
# =============================
# Inicia sempre no modo manual
modo_atual = "BLUETOOTH" 

# =============================
# CONFIGURAÇÕES DE MOTORES
# =============================
ENA = PWM(Pin(5), freq=1000)   # Motor direito
ENB = PWM(Pin(18), freq=1000)  # Motor esquerdo

# Velocidades balanceadas para o robô andar reto
VEL_DIR_MAX = 770
VEL_ESQ_MAX = 1020

# Pinos de Direção (L298N)
A_1A = Pin(23, Pin.OUT)
A_1B = Pin(22, Pin.OUT)
B_1A = Pin(19, Pin.OUT)
B_1B = Pin(21, Pin.OUT)

# =============================
# CONFIGURAÇÕES DE SENSORES
# =============================
sensor_esquerdo = Pin(4, Pin.IN)
sensor_direito  = Pin(27, Pin.IN)

# =============================
# FUNÇÕES DE MOVIMENTO
# =============================
def aplicar_velocidade(v_dir, v_esq):
    ENA.duty(int(v_dir))
    ENB.duty(int(v_esq))

def mover(dir_A1A, dir_A1B, dir_B1A, dir_B1B, v_dir, v_esq):
    A_1A.value(dir_A1A)
    A_1B.value(dir_A1B)
    B_1A.value(dir_B1A)
    B_1B.value(dir_B1B)
    aplicar_velocidade(v_dir, v_esq)

# Movimentos Padrão (Bluetooth e Reto no Segue Linha)
def motores_frente():
    mover(1, 0, 1, 0, VEL_DIR_MAX, VEL_ESQ_MAX)

def motores_tras():
    mover(0, 1, 0, 1, VEL_DIR_MAX, VEL_ESQ_MAX)

def curva_direita(): 
    # Gira no próprio eixo (Bluetooth)
    mover(0, 1, 1, 0, VEL_DIR_MAX, VEL_ESQ_MAX)

def curva_esquerda(): 
    # Gira no próprio eixo (Bluetooth)
    mover(1, 0, 0, 1, VEL_DIR_MAX, VEL_ESQ_MAX)

def parar_motores():
    mover(0, 0, 0, 0, 0, 0)

# Movimentos Suaves (Correção do Segue Linha)
def ajustar_esquerda():
    # Sensor esquerdo viu a linha preta -> Robô precisa virar à esquerda.
    # Motor direito empurra (velocidade max), motor esquerdo para (0).
    mover(1, 0, 1, 0, VEL_DIR_MAX, 0)

def ajustar_direita():
    # Sensor direito viu a linha preta -> Robô precisa virar à direita.
    # Motor esquerdo empurra (velocidade max), motor direito para (0).
    mover(1, 0, 1, 0, 0, VEL_ESQ_MAX)


# =============================
# BLUETOOTH E INTERRUPÇÕES
# =============================
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
    global modo_atual # Permite modificar a variável global
    
    if event == 1:
        print("Bluetooth Conectado")
    elif event == 2:
        print("Bluetooth Desconectado")
        parar_motores()
        start_advertising()
    elif event == 3:
        conn_handle, value_handle = data
        value = ble.gatts_read(value_handle)

        # 1. Verifica se o botão SELECT foi pressionado (Troca de Modo)
        if value == b'\xff\x01\x01\x01\x02\x02\x00\x00':
            if modo_atual == "BLUETOOTH":
                modo_atual = "SEGUE_LINHA"
                print("--- MODO SEGUE LINHA ATIVADO ---")
            else:
                modo_atual = "BLUETOOTH"
                print("--- MODO BLUETOOTH ATIVADO ---")
                parar_motores() # Para o robô imediatamente ao trocar de modo
            return # Encerra a leitura aqui para não tentar ler movimento

        # 2. Se estiver no modo BLUETOOTH, aceita os comandos de direção
        if modo_atual == "BLUETOOTH":
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
print("Sistema Iniciado. Aguardando conexão Bluetooth...")

# =============================
# LOOP PRINCIPAL (SEGUE LINHA)
# =============================
while True:
    # O loop principal só controla os motores se estiver no modo Segue Linha
    if modo_atual == "SEGUE_LINHA":
        esq = sensor_esquerdo.value()
        dir = sensor_direito.value()

        # Lógica: Linha Preta (1) no Fundo Branco (0)
        if esq == 0 and dir == 0:
            # Ambos no branco -> A linha está no meio, vai reto
            motores_frente()
            
        elif esq == 1 and dir == 0:
            # Esquerdo viu preto -> Robô está saindo pela direita, corrige para a esquerda
            ajustar_esquerda()
            
        elif esq == 0 and dir == 1:
            # Direito viu preto -> Robô está saindo pela esquerda, corrige para a direita
            ajustar_direita()
            
        else:
            # Ambos viram preto -> Chegou num cruzamento ou marcação de parada
            parar_motores()

    # Pequeno atraso para estabilidade e evitar sobrecarga do processador
    time.sleep_ms(10)
