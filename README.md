# Protecto final de Sistemas Distribuidos

## Integrantes:
### Carmen Irene Cabrera Rodríguez C-412
### Enrique Martínez González C-412

## Solución presentada

Para la creación de este proyecto se hizo uso fundamentalmente del algoritmo Chord; este fue utilizado específicamente para, de manera distribuida, adquirir y almacenar las url solicitadas por los clientes. Todos los nodos dentro del anillo de chord son los encargados de almacenar htmls, recibir consultas y responder peticiones al mismo tiempo, de forma que los roles se aprecian a la hora de obtener una consulta. El nodo receptor de dicha consulta se convierte en el líder de la misma y se encarga de distribuir esta al nodo asociado a la url recibida. Una vez concluida la adquisición del html, el nodo inicial que recibió la petición se encarga de responderle esta al cliente. Los htmls de las urls recibidas son almacenados para no repetir consultas de peticiones futuras.

Primeramente, se utiliza para la comunicación entre los distintos nodos de chord la librería **Zmq** de python, haciendo uso del patrón **REQ/REP**. Cada nodo tiene dos sockets abiertos escuchando peticiones constantemente en puertos distintos, cada uno para consultas específicas. Cada peticón realizada entre dos nodos es respondida una vez haya culminado la acción solicitada, ya sea una petición de algún dato o pedir que se realice una acción en el nodo destino; además, se establece un tiempo máximo de espera de respuesta, asegurando que el patrón utilizado nunca quede detenido por falta de comunicación.

En el proyecto se plantea una implementación que intenta seguir la idea de la documentación de chord brindada en conferencias, utilizando la lista de sucesores por si el continuo a un nodo cae por algún motivo, el nodo sea capaz de sustituir a este por otro. Además los htmls ya scrapeados de un nodo son almacenados también en el siguiente, de forma que si cualquier nodo cae, esta información no se pierde.

Al adentrarse más en el código se puede observar que cada método de consulta cuenta con un método de respuesta. Estos métodos de respuesta son utilizados en el hilo que se crea al llamar a la función *run* de la clase *ChordNode*; este hilo no es más que un método encargado de abrir un socket por un puerto fijo determinado y revisar constantemente todos los paquetes recibidos por este puerto. Si la acción en el json recibido coincide con alguna de las funciones implementadas, pues se llama a esta y se envía la respuesta por este socket hacia el nodo emisor de la consulta. Apreciar que las consultas de url son analizadas por un puerto distinto al de las consultas internas del funcionamiento de chord ya que el obtener un html asociado a una url puede tomar más tiempo.

Cuando un cliente se conecta a algún nodo que pertenece al anillo de chord, este nodo le envía al cliente, una lista de otros nodos a los cuales el cliente puede hacer consultas de urls, que también pertenecen al anillo. El cliente introduce una url y una profundidad, entonces, utilizando un método semejante a un bfs en el lado del cliente, se le pregunta al nodo por el html de la url requerida. El método similar al bfs permite que no se repitan consultas al anillo de chord de urls ya visitadas, evitando la formación de ciclos en las peticiones. El nodo que recibe la petición se encarga de hashear la url, utilizando **SHA256**, para obtener el id asociado a la misma, con el cual es posible determinar el nodo que debe encargarse de obtener el html. Con este id, se hace la consulta a dicho nodo y cuando este haya obtenido el html de la url, se lo devuelve al nodo que en un principio obtuvo la consulta del cliente, el cual finalmente responde al cliente.

Por ejemplo, supongamos que el cliente `X` le manda una petición de la url `u` al nodo `A`. `A` se ocupa de encontrar el nodo encargado de procesar el id asociado a `u`, asuma que ese nodo sea `D`; entonces `A` le solicita a `D` el html de la url `u`. En cuanto `D` obtenga el resultado, lo almacena en su caché y le envía dicho html a `A` para que este responda finalmente la consulta a `X`.

En caso de que el cliente no obtenga respuesta en un tiempo fijado, intentará consultar la misma url a otros nodos hasta obtener el resultado deseado. Una vez que el html ha sido obtenido, se procede a extraer todos los links dentro del mismo, si la profundidad es mayor que 0, y visitarlos. Todos los htmls resultantes son guardados en el directorio raíz de la ejecución del cliente.

## Requerimientos 📋

El proyecto fue desarrollado utilizando `python 3.6`. Es necesaria la instalación de las siguientes herramientas:

- [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)
    ```
    $ pip install beautifulsoup4
    ```

- [Requests](https://docs.python-requests.org/en/master/)
    ```
    $ python -m pip install requests
    ```


## Ejecución

Para poder ejecutar este proyecto es necesario correr las siguientes líneas.

En caso de querer ejecutar un nodo que pertenezca al anillo de chord:
    
```
python3 main.py <ip del nodo de chord> <ip de algún nodo dentro del anillo de chord>
```

Si se trata del primer nodo del anillo, ambos *ip* deberán ser el mismo.

En caso de querer ejecutar un cliente para realizar consultas de urls:

```
python3 main_client.py <ip de algún nodo dentro del anillo de chord>
```

Luego de esto deberá introducir la url y la profundidad deseada.

En caso de que algún nodo dentro del anillo de chord falle se podrán apreciar errores en consultas que se realizan a este nodo por el resto. Mientras estos errores sean apreciados, el anillo se encuentra estabilizándose. Una vez este proceso culmine, el anillo debe quedar nuevamente estructurado de forma que con gran probabilidad sea capaz de mantener aún su forma cíclica. Destacar que en ningún momento el cliente dejará de recibir su petición pues siempre habrá algún nodo que sea el encargado de responderle no importa cuantas caídas o fallos hayan sucedido.

### Github

- **Repositorio del proyecto** - [SDFinalProject](https://github.com/codersUP/SDFinalProject)
- **Carmen Irene Cabrera Rodríguez** - [cicr99](https://github.com/cicr99)
-  **Enrique Martínez González** - [kikeXD](https://github.com/kikeXD)