from machine import Pin, PWM
from time import sleep_ms

# =============================
# PINOS DA PONTE H (L298N)
# =============================
# Motor A (Direito)
A_1A = Pin(23, Pin.OUT)   # IN1
A_1B = Pin(22, Pin.OUT)   # IN2
ENA  = PWM(Pin(5))        # ENA (PWM) - remover jumper ENA
ENA.freq(20000)           # 20 kHz (silencioso)

# Motor B (Esquerdo)
B_1A = Pin(19, Pin.OUT)   # IN4
B_1B = Pin(21, Pin.OUT)   # IN3
ENB  = PWM(Pin(18))       # ENB (PWM) - remover jumper ENB
ENB.freq(20000)

# =============================
# SENSORES (TCRT)
# =============================
sensor_esquerdo = Pin(4, Pin.IN)
sensor_direito  = Pin(27, Pin.IN)

# =============================
# CONFIGURAÇÕES DE VELOCIDADE
# =============================
BLACK_LEVEL = 1      # se seu sensor dá 0 no preto, troque para 0

# 1. Velocidades para ir RETO (Aqui você compensa o motor fraco)
VEL_RETO_DIR = 920   # Roda direita
VEL_RETO_ESQ = 960  # Roda esquerda

# 2. Velocidades para a Roda de FORA na curva (A que empurra)
# Usando a mesma força da reta para manter o equilíbrio na conversão
VEL_CURVA_DIR = 1020
VEL_CURVA_ESQ = 1020

# 3. Velocidades para a Roda de DENTRO na curva (A que serve de eixo)
# ZERO (0) garante que ela pare totalmente, resolvendo a diferença dos motores
VEL_RED_DIR = 0    
VEL_RED_ESQ = 0    

# 4. Freio
VEL_FREIO = 1023     # força de frenagem (0–1023)

# =============================
# FUNÇÕES DE MOVIMENTO
# =============================
def motores_frente():
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(VEL_RETO_DIR)
    ENB.duty(VEL_RETO_ESQ)

def virar_esquerda():
    # Para virar à ESQUERDA, o motor DIREITO empurra e o ESQUERDO para
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(VEL_CURVA_DIR)  # Direito Rápido
    ENB.duty(VEL_RED_ESQ)    # Esquerdo Parado

def virar_direita():
    # Para virar à DIREITA, o motor ESQUERDO empurra e o DIREITO para
    A_1A.value(1); A_1B.value(0)
    B_1A.value(1); B_1B.value(0)
    ENA.duty(VEL_RED_DIR)    # Direito Parado
    ENB.duty(VEL_CURVA_ESQ)  # Esquerdo Rápido

def parar_motores():
    # ---- FREIO CURTO (brusco) ----
    A_1A.value(1); A_1B.value(1)  # ambos HIGH → curto motor direito
    B_1A.value(1); B_1B.value(1)  # ambos HIGH → curto motor esquerdo
    ENA.duty(VEL_FREIO)           # aplica duty máximo para reforçar o freio
    ENB.duty(VEL_FREIO)
    sleep_ms(240)                  # tempo de freada (ajuste conforme inércia)
    ENA.duty(0); ENB.duty(0)      # depois desliga totalmente

# =============================
# LOOP PRINCIPAL
# =============================
while True:
    esq = sensor_esquerdo.value()
    dir = sensor_direito.value()

    # --------------------------
    # Lógica de seguir o BRANCO
    # --------------------------
    if esq == 0 and dir == 0:
        motores_frente()                   # ambos veem branco → reto
    
    elif esq == 1 and dir == 0:
        virar_esquerda()                   # esquerdo vê preto → desvia p/ esquerda
        
    elif esq == 0 and dir == 1:
        virar_direita()                    # direito vê preto → desvia p/ direita
        
    else:
        parar_motores()                    # ambos pretos → freio curto

    sleep_ms(5)
