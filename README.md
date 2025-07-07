# 09/06 - Estudando o `stim_node.py`

- Primeiramente, usei o site [wiki.ros.org/pt_BR/ROS/Tutorials](http://wiki.ros.org/pt_BR/ROS/Tutorials) para entender melhor e achar as funções que usam o ROS dentro do código, e fui deixando os trechos comentados para não esquecer o que estou retirando do código;
- Aqui só li sobre os tópicos de iniciante;
- O tópico [CreatingMsgAndSrv](http://wiki.ros.org/pt_BR/ROS/Tutorials/CreatingMsgAndSrv) é importante para o entendimento do `Request` e `Response`;
- O Guilherme me ajudou a entender melhor onde usamos o ROS e disse o que deveria tirar;

## Relembrei das orientações sobre o que devo fazer no arquivo:
**28/05/25 - Anotações controle dos sensores**

- No git: `orthesis_pc/src/ema_fes_orthesis/ema_fes_orthesis/stim_node.py` (tirar o ROS e conectar no USB) e `step_test_node.py`
- Manual do Rasomed: ler
- Estudar melhor sobre o ROS
- Ficar de olho onde tiver `Request` e `Response`

### Funções que usarei no `stim_node.py`:
- `initialize_ccl`
- `update_ccl`
- `stop_ccl`
- Tirar o ROS e deixar botões para controle:
  - Comunicação;
  - Definição de parâmetros;
  - Controle;


## Próximos passos:
- Terminar o código `stim_node.py`;

---

# 11/06 - Estudando o `stim_node.py` - pt. 2

- Continuação do estudo e atualização do código `stim_node.py`
- Fiz alterações nos trechos que definem os objetos `initialize_ccl` e `stop_ccl`:

  - No `initialize_ccl`:
    - Retirei a chamada dos arquivos `Request` e `Response`, pois são tipos de arquivos do ROS;
    - Mudei `self.channel_stim` para receber `channels`;
    - Transformei o `response.success` em uma variável que recebe `success = self.write_read_command(command_bytes)`;
    - Pedi para retornar `success`;

  - No `stop_ccl`:
    - Também retirei a chamada dos arquivos `Request` e `Response`;
    - Transformei o `response.success` em uma variável que recebe `success = self.write_read_command(command_bytes)`;

- Fiz alteração na definição do `main`:
  - Apaguei tudo, pois era tudo do ROS;
  - Defini um objeto para chamar a classe `StimNode()`;
  - Defini qual canal quero usar;
  - Chamei o objeto `initialize_ccl` com a entrada de canal que defini no passo anterior;
  - Defini minha largura de pulso e de corrente;
  - Chamei o objeto que atualiza a largura de pulso e corrente;
  - Adicionei um delay para receber atualizações;
  - Chamei o objeto de parada `stop_ccl`;

- **Próximo dia vou testar o código no Rasomed.**


# 02/07 - 1° Teste no Hasomed

- Primeiraamente montei o Eletroestimulador Rasomed com a orientação do Guilherme e tentei rodar de primeira o código, mas não funcionou;
  - O primeiro erro que deu foi na hora de acessar a porta, no codigo original a porta era acessada por `PORT = "/dev/stim"`, mas como estou usando o Windows a forma de acessar é diferente, deve ser por `PORT = "COM5"`
  - Para saber qual é a porta serial, depois d conectar o Rasomed via usb no pc, digitei `mode` no terminal para me mostrar qual é a porta que está sendo usada;
  - O segundo erro que deu apos corrigir o anterior foi no termo `time.delay(5)` que eu escrevi dentro de `main()`, em Pyton deve ser `time.sleep(5)`
- Depois das correções feitas, o código rodou sem problemas no Rasomed e testei na perna do Guilherme;

# 07/07 - 2° Teste no Hasomed

- Testei o codigo pronto em mim mesma para entender melhor os parâmetros de `pulse_width` e `pulse_current`;
- Testei no braço, comecei usando `pulse_width` igual à 100 e `pulse_current` igual à 5: senti um leve formigamento.
- Depois fui alterando o valor de `pulse_current`, subindo de 2 em 2 ate chegar à 10, quando estava em 8 comecei a sentir o musculo se contraindo mas sem fazer o movimento da articulação e continuou igual no pulso de corrente igual à 10;
- Depois desci o pulso de corrente para 5 e fui alterando a largura de pulso de 100 ate chegar em 200: em 150 senti o músculo contrair, mas ainda sem movimento de articulação, a partir de 180 senti o músculo contrair e observei o movimento de articulação;
