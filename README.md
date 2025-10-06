# Documentação Detalhada do Código StimNode

## Introdução

Este repositório tem como propósito principal servir como ambiente de **treinamento e aprendizado** para códigos utilizados no controle do estimulador **Hasomed**. O material aqui apresentado é baseado em códigos desenvolvidos por membros do **Projeto EMA**, porém adaptados para fins educacionais e de estudo.

### Contexto e Objetivos

Os códigos originais utilizam o framework **ROS (Robot Operating System)** para comunicação e controle dos dispositivos. No entanto, para facilitar o aprendizado e tornar o código mais acessível, um dos principais objetivos deste repositório é:

- Simplificar a implementação removendo dependências do ROS;
- Manter a funcionalidade equivalente ao código original;
- Facilitar o entendimento dos protocolos de comunicação;
- Criar material didático para novos membros do projeto;

### Estrutura de Aprendizado

Este código representa uma versão **mais básica e didática** dos sistemas utilizados em produção, focando nos aspectos fundamentais da comunicação serial e controle de estimulação elétrica, sem a complexidade adicional do ROS.

### Material Complementar

Para um acompanhamento detalhado do meu processo de aprendizado e desenvolvimento, consulte o **caderno de estudos** que documenta todo o percurso de compreensão deste código e dúvidas que tive:

**🔗 [Notas de Estudos - Diário de Aprendizado](https://github.com/Juliana-Bispo/Treinamento---HASOMED/tree/Notas-de-estudo)**

*Este diário contém anotações, dúvidas, descobertas e progressos realizados durante o estudo deste sistema de estimulação.*

---

# Documentação Detalhada do Código StimNode

## Importações e Dependências

```python
import time
import numpy as np
import sys
import serial
import struct
```

**Explicação das Importações:**
- `time`: Usado para delays e controle temporal
- `numpy`: Biblioteca para computação numérica (importada mas não utilizada no código)
- `sys`: Funcionalidades do sistema (importada mas não utilizada)
- `serial`: Comunicação serial com o dispositivo estimulador
- `struct`: Empacotamento e desempacotamento de dados binários

---

## Definição da Classe e Atributos

```python
class StimNode:   # Antes com o ROS era Class StimNode(Node):

    PORT = "COM5"
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
```

**Explicação dos Atributos de Classe:**
- `PORT`: Define a porta serial COM5 para comunicação com o estimulador
- `CHANNEL_LF`: Lista vazia para canais de baixa frequência (não utilizada)
- `FREQ`: Frequência de estimulação padrão de 50Hz
- `N_FACTOR`: Fator de pulo na sequência (0 = sem pulos)
- `GROUP_TIME`: Tempo de grupo (não utilizado no código atual)
- `STIM_MODE`: Modo de estimulação (0 = modo "single")

---

## Dicionário de Comandos

```python
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
                    # ... (repetido para 8 canais)
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
```

**Explicação do Dicionário de Comandos:**
- **`channelListModeInitialization`**: Comando para inicializar o modo de lista de canais
  - ID: 0, campos incluem identificador, checksum, canais de estimulação, etc.
- **`channelListModeUpdate`**: Comando para atualizar parâmetros de estimulação
  - ID: 1, contém modo, largura de pulso e corrente para até 8 canais
- **`channelListModeStop`**: Comando para parar a estimulação
  - ID: 2, contém apenas identificador e checksum
- **`singlePulseGeneration`**: Comando para gerar pulso único
  - ID: 3, especifica canal, largura de pulso e corrente

---

## Construtor da Classe

```python
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
```

**Explicação do Construtor:**
- Inicializa a conexão serial com configurações específicas:
  - **Porta**: COM5
  - **Baudrate**: 115200 bps
  - **Bits de dados**: 8
  - **Paridade**: Nenhuma
  - **Bits de parada**: 2
  - **Controle de fluxo**: RTS/CTS habilitado
- Imprime mensagem de confirmação da inicialização

---

## Métodos Utilitários para Manipulação de Bits

```python
def set_channel_byte(self,bit_list, channel_list):
    for channel in channel_list:
        bit_list |= (0b00000001 << channel-1)
    return bit_list

def clear_bit(self,cleared_bit_list, bit_list):
    for bit in bit_list:
        cleared_bit_list &= ~(1 << bit)
    return cleared_bit_list
```

**Explicação dos Métodos Utilitários:**
- **`set_channel_byte`**: Define bits específicos baseados em uma lista de canais
  - Usa operação OR bit-a-bit para ativar o bit correspondente a cada canal
  - Exemplo: canal 1 ativa bit 0, canal 2 ativa bit 1, etc.
- **`clear_bit`**: Limpa bits específicos de uma lista de bits
  - Usa operação AND com NOT bit-a-bit para desativar bits específicos

---

## Método de Criação de Comandos

```python
def create_command(self,cmd_name, field_values):
    command = self.command_dict[cmd_name]
    
    bit_count = 0
    command_bytes = []
    
    # starting byte has bit 7 set, all others have bit 7 clear
    command_byte = 0b10000000
    
    field_names = field_values.keys()
    
    for field_name in field_names:
        # if field is not present, just move on
        try:
            field_value = field_values[field_name]
            field_bit_size = command['field_bit_sizes'][field_name]
        except KeyError:
            continue
        
        # if field is a filler ('X'), just update bit_count and move on
        if field_name == 'X':
            bit_count += command['field_bit_sizes'][field_name]
        else:
            # Complex bit manipulation logic...
            # (código completo de empacotamento de bits)
    
    return bytearray(command_bytes)
```

**Explicação do Método `create_command`:**
- **Propósito**: Constrói comandos em formato binário baseado na estrutura do dicionário
- **Parâmetros**: Nome do comando e valores dos campos
- **Funcionamento**:
  - Inicia com byte de comando (bit 7 definido)
  - Empacota campos em bytes sequencialmente
  - Lida com campos que excedem limites de byte (divisão)
  - Campos 'X' são usados como preenchimento
  - Retorna array de bytes pronto para envio

---

## Método de Comunicação Serial

```python
def write_read_command(self,command_bytes):
    try:
        self.serial_port.write(command_bytes)
    except:
        print('failed to write to stimulator serial port')
        raise
    
    while(self.serial_port.in_waiting<1): pass
    
    try:                            
        ack = struct.unpack('B', self.serial_port.read(1))[0]
        print(f"ack -> {ack}")  
    except Exception as error:
        print(f"ack -> {error}") 
    
    error_code = ack & 1
    
    return {0: False, 1: True}[error_code]
```

**Explicação do Método `write_read_command`:**
- **Propósito**: Executa comunicação bidirecional com o estimulador
- **Processo**:
  1. Envia comando via serial
  2. Aguarda resposta (polling)
  3. Lê byte de acknowledgment (ACK)
  4. Extrai código de erro do bit menos significativo
  5. Retorna `True` se houve erro, `False` caso contrário
- **Tratamento de erro**: Captura exceções de escrita e leitura

---

## Método de Inicialização do CCL

```python
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
    print(f"response:{success}   |")
    
    return success
```

**Explicação do Método `initialize_ccl`:**
- **Propósito**: Inicializa o modo Channel Control List (CCL)
- **Parâmetros**: Lista de canais a serem ativados
- **Cálculos importantes**:
  - `ts1`: Período em milissegundos baseado na frequência
  - `main_time`: Tempo principal calculado conforme manual do estimulador
  - `check_sum`: Soma de verificação com módulo 8
- **Processo**: Monta comando, envia e retorna status de sucesso

---

## Método de Atualização do CCL

```python
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
```

**Explicação do Método `update_ccl`:**
- **Propósito**: Atualiza parâmetros de estimulação para canais ativos
- **Parâmetros**: Listas de largura de pulso e corrente para cada canal
- **Processo**:
  - Itera sobre canais ativos
  - Define modo, largura de pulso e corrente para cada canal
  - Calcula checksum acumulativo com módulo 32
  - Envia comando e retorna status

---

## Método de Parada do CCL

```python
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
```

**Explicação do Método `stop_ccl`:**
- **Propósito**: Para a estimulação em todos os canais
- **Processo**: Envia comando de parada simples com checksum zero
- **Retorno**: Status de sucesso da operação

---

## Função Principal e Exemplo de Uso

```python
def main(args=None):
    stim_object = StimNode()
    channels = [1]
    
    stim_object.initialize_ccl(channels)
    
    pulse_width = [180]     #no braço a partir de 60us
    pulse_current = [8]    #no braço entre 5mA e 10mA
    
    stim_object.update_ccl(pulse_width,pulse_current)
    
    time.sleep(5)
    
    stim_object.stop_ccl()

if __name__ == '__main__':
    main()
```

**Explicação da Função Principal:**
- **Demonstração prática** do uso da classe StimNode
- **Sequência de operações**:
  1. Cria instância do estimulador
  2. Inicializa canal 1
  3. Configura estimulação (para o músculo quadriceps 180μs de largura e 8mA de corrente, no braço seria)
  4. Atualiza parâmetros
  5. Mantém estimulação por 5 segundos
  6. Para a estimulação

