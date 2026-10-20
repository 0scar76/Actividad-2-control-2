# Actividad 2 - Control 2 - CC4303 Redes

Link del repositorio en GitHub: [Repositorio](https://github.com/0scar76/Actividad-2-control-2.git)

**En esta actividad no se utilizo la inteligencia artificial.**

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

Las funciones agregadas en esta actividad (ademas de las pedidas por enunciado) corresponden a 2 funciones auxiliares de la funcion **send_with_go_back_n**.

## Respuestas a las preguntas de la parte 2.1

1. ¿Por que le puede servir usar como base para Go Back-N el codigo de Stop & Wait de la seccion anterior? ¿Que similitud tiene Go Back-N con Stop & Wait?
- Porque Stop & Wait es equivalente a usar Go Back-N con un tamaño de ventana igual a 1.
2. En la sección anterior solo se muestra la funcion **send** de Stop & Wait, ¿Qué ocurre con la función **recv**? ¿Esta función cambia con el uso de SocketUDP y SlidingWindowsCC?
- Para recv el unico cambio significativo es el manejo de los numeros de secuencia, en vez de enviar un ACK con el numero de secuencia aumentado en el tamaño del mensaje recibido, envia el mismo numero de secuencia que recibio en el mensaje. Fuera de esto, no hay cambio con el uso de SocketUDP y SlidingWindowsCC.

## Pruebas de enunciado