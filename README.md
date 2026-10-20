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

anotar al final

## Implementación

anotar al final

## Respuestas a las preguntas (escribir mas bonito dsp)

1. Porque stop & wait es equivalente a usar go back n con ventana = 1.
2. Para receive el unico cambio significativo es el manejo de los numeros de secuencia, en vez de enviar un ACK con el numero de secuencia aumentado en el tamaño del mensaje recibido, solo aumenta seq en 1.