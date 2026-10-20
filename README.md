# Actividad 2 - Control 2 - CC4303 Redes

Link del repositorio en GitHub: [Repositorio](https://github.com/0scar76/Actividad-2-control-2.git)

**En esta actividad se utilizó Claude Opus 5.5 para la resolución de conflictos de merge, revisión del código escrito, consulta sobre firmas de funciones y las pruebas finales de la actividad.**

## Sobre la actividad

En esta actividad, se pidio implementar el metodo de envio Go Back-N y control de congestion en la clase socketTCP creada en la actividad anterior.

### Prerrequisitos

Para esta actividad no hay prerrequisitos, ya que todas las librerías ocupadas (socket y sys) vienen ya incluidas con Python por defecto y los archivos necesarios estan en el mismo repositorio.

## Cómo ejecutar las pruebas

Para las pruebas con pérdidas, se ejecutó el comando netem dado en el enunciado de la actividad.

El repositorio incluye 3 archivos .py, los cuales se ocuparon como tests:
* CongestionControl_test.py
* Server.py
* Cliente.py

Para ejecutar la prueba de control de congestion basta con ejecutar el archivo CongestionControl.py de la siguiente manera:
```
python3 CongestionControl.py
```
El mismo archivo imprime en pantalla que test pasan y que test se fallan.

Para ejecutar las pruebas de server y client, se deben ejecutar **ambos** archivos de la siguiente manera (argumento opcional -d o --debug sirve para activar el modo debug, que imprime mensajes enviados, recibidos y estados de los sockets):
```
python3 <nombre_del_archivo_.py> <IP_SERVER> <PORT_SERVER> [-d | --debug] < <nombre_del_archivo_a_enviar>
```
El repositorio incluye un archivo test.txt de largo 38 (el largo del archivo es más grande que el buffer que se utiliza en la prueba de archivo y, en este caso específico, el largo no es múltiplo de 16), pero puede incluso probarse dándole este README.md si se ajusta la variable **BYTES_NUM** dentro del archivo **socketTCP.py** a 2.

**IMPORTANTE:** Es necesario ejecutar ambos archivos .py con los mismos argumentos (a excepción del debug, que es opcional), ya que de otra forma el test **no funcionará**.

## Decisiones creativas

En esta actividad, la clase **socketTCP** controla 2 sockets UDP, uno creado con la clase socketUDP entregada por el equipo docente y otro implementado con la libreria socket de Python. Esto se hizo asi, ya que, como se reutilizo la clase **socketTCP** de la actividad 1 (que usa socket UDP de la libreria socket), para no reimplementar todo el codigo con la clase socketUDP (no funcionaba correctamente simplemente cambiar el tipo de socket a usar), esta se utilizo unicamente en el metodo de envio con Go Back-N.

Fuera de este detalle, el resto del codigo sigue las mismas decisiones de diseño de la implementacion en la actividad 1 y el enunciado de la actividad 2.

## Implementación

La clase **socketTCP(timeout=1, debug=False, max_timeouts=WINDOW_SIZE)** recibe los mismos argumentos que en la actividad 1 mas el argumento max_timeouts, que por defecto es igual al tamaño de la sliding window (el tamaño de la ventana se puede cambiar con la variable WINDOW_SIZE).

En esta actividad se añadieron ademas los siguientes recursos:
* **sckt_gbn:** El socket creado con la clase SocketUDP, que sera usado en Go Back-N.
* **remote_address_gbn:** La direccion del socket que se usa para el envio en Go Back-N.
* **congestion_control_on:** Indica si se usa control de congestion en Go Back-N (por defecto False). Se cambia con **set_congestion_control(value)**. Si esta apagado, la ventana queda fija en WINDOW_SIZE; si esta encendido, la ventana se ajusta con un objeto **CongestionControl**, llamando a **event_ack_received()** al recibir un ACK y a **event_timeout()** cuando ocurre un timeout.
* **MSS:** El tamaño de los trozos en que se divide el mensaje en Go Back-N (no puede superar 16, ya que recv lee de a 5 + 16 bytes).

## Respuestas a las preguntas

1. ¿Por que le puede servir usar como base para Go Back-N el codigo de Stop & Wait de la seccion anterior? ¿Que similitud tiene Go Back-N con Stop & Wait?
- Porque Stop & Wait es equivalente a usar Go Back-N con un tamaño de ventana igual a 1.
2. En la sección anterior solo se muestra la funcion **send** de Stop & Wait, ¿Qué ocurre con la función **recv**? ¿Esta función cambia con el uso de SocketUDP y SlidingWindowsCC?
- Para recv el unico cambio significativo es el manejo de los numeros de secuencia, en vez de enviar un ACK con el numero de secuencia aumentado en el tamaño del mensaje recibido, envia el mismo numero de secuencia que recibio en el mensaje. Fuera de esto, no hay cambio con el uso de SocketUDP y SlidingWindowsCC.
3. Según lo visto en el video y en los tests de la clase CongestionControl ¿que valor debería tener window_size en este punto?
- window_size debería ser 1. Un objeto CongestionControl recién creado parte en slow start con cwnd = MSS y ssthresh = None, que es lo que revisa `initialization_test`, por lo que `get_MSS_in_cwnd()` = cwnd // MSS = 1. Como la ventana se compone de segmentos de tamaño MSS, al comenzar el envío solo cabe 1 segmento en vuelo. Desde ahí crece en 1 MSS por cada ACK mientras esté en slow start.

## Pruebas de enunciado

Las pruebas se hicieron en localhost con un archivo de 100 bytes y otro de 1200 bytes (para el de 1200 bytes se uso **BYTES_NUM = 2**) y un timeout de 0.5 segundos. La perdida de 10% se simulo botando al azar el 10% de los mensajes que envian ambos lados, ya que no se pudo usar netem.

### 1. Integridad de los datos

Se envio el archivo de 1200 bytes con y sin perdida, y con y sin control de congestion. En todos los casos el archivo llego identico al original. Tambien llego completo en las 20 ejecuciones de la prueba 4.

### 2. Control de congestion sin perdida

No ocurrieron timeouts espontaneos. El control de congestion se mantuvo siempre en slow start con ssthresh = None (sin timeouts nunca se le asigna un valor, por lo que nunca pasa a congestion avoidance). cwnd crecio en 1 MSS (8 bytes) por cada ACK, desde 8 hasta 1216.

### 3. Control de congestion con perdida

Los cambios de estado son los esperados:
* Con cada timeout se vuelve a slow start, con cwnd = MSS = 8 y ssthresh = cwnd // 2.
* El ACK siguiente deja cwnd = 16 >= ssthresh, por lo que pasa a congestion avoidance.
* En congestion avoidance cwnd crece de a poco (por ejemplo 24 -> 26.67 -> 29.33).

Como ssthresh queda bajo (entre 4 y 16), el control pasa casi todo el tiempo en congestion avoidance con una ventana chica. En una ejecucion con el archivo de 1200 bytes hubo 26 cambios de estado y el cwnd maximo fue 66.

### 4. Go Back-N con y sin control de congestion

Con 10% de perdida y timeout de 0.5 segundos, cada caso se repitio 5 veces. Los mensajes cuentan todo lo enviado por ambos lados (handshake, datos, ACKs, cierre y mensajes perdidos).

| Archivo | Modo | Tiempo promedio | Mediana | Mensajes promedio |
|---|---|---|---|---|
| 100 bytes | sin control de congestion | 1.49 s | 2.10 s | 59.2 |
| 100 bytes | con control de congestion | 1.40 s | 1.59 s | 42.8 |
| 1200 bytes | sin control de congestion | 11.75 s | 10.28 s | 483.6 |
| 1200 bytes | con control de congestion | 10.52 s | 11.23 s | 389.6 |

Con el archivo de 1200 bytes, el control de congestion tomo en promedio 1.2 segundos menos (10%), pero su mediana fue 1 segundo mayor, asi que con 5 repeticiones la diferencia de tiempo no es clara: el tiempo depende sobre todo de cuantos timeouts ocurren. La diferencia clara esta en los mensajes: con control de congestion se enviaron cerca de un 20% menos, porque al achicar la ventana despues de una perdida se reenvian menos segmentos que despues se descartan.

### Problemas encontrados durante las pruebas

* **Perdida del ultimo ACK del handshake:** el cliente se daba por conectado pero el servidor seguia esperando el ACK y accept() terminaba devolviendo None. Se arreglo haciendo que send, al tener un timeout, revise si el servidor reenvio el SYN-ACK y le responda de nuevo.
* **Perdida del ultimo ACK de los datos:** el receptor ya habia salido de recv, por lo que nadie volvia a enviar el ACK y send esperaba hasta LIMIT timeouts (unos 15 segundos). Se arreglo haciendo que close() reenvie el ultimo ACK al socket de Go Back-N cuando le llegan datos de ese socket.
