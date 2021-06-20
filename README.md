# Protecto final de Sistemas Distribuidos

## Integrantes:
### Carmen Irene Cabrera Rodríguez C-412
### Enrique Martínez González C-412

#

Para la creación de este proyecto se hizo uso fundamentalmente de el algoritmo Chord, este fue utilizado específicamente para, de manera distribuida, adquirir y almacenar las url solicitadas por los clientes.

Primeramente, se utiliza para la comunicación entre los distintos nodos de chord la librería **Zmq** de python, haciendo uso del patrón **REQ/REP**. Específicamente cada nodo tiene dos sockets abiertos escuchando peticiones constantementes en puertos distintos. Cada peticón reaizada entre dos nodos es respondida una vez haya culminado la acción solicitada, enviando en caso de ser requerida la respuesta a la petición, dentro del mensaje de respuesta, además se establece un tiempo máximo de espera de respuesta, de esta manera se asegura que el patrón utilizado nunca quede detenido por falta de respuesta.

En el proyecto se plantea una implementación que intenta seguir a la documentación de chord brindada en conferencias, utilizando la lista de sucesores por si el continuo a un nodo cae por algún motivo, el nodo sea capaz de sustituir a este por otro. Además los htmls ya scrapeados de un nodo son almacenados también en el siguiente, de forma que si cualquier nodo cae, esta información no se pierda.

Adentrándonos más en el código podemos ver que cada método de consulta cuenta con un método de respuesta, estos métodos de respuesta son utilizados en el hilo que se crea al llamar a la función *run* de la clase *ChordNode*, este hilo no es más que un método encargado de abrir un socket por un puerto fijo determinado y revisar constantemente todos los paquetes recibidos por este puerto, si la acción en el json recibido coincide con alguna de las funciones implementadas, pues se llama a esta y se envía la respuesta por este socket hacia el nodo emisor de la consulta. Apreciar que las consultas de url son analizadas por un puerto distinto al de las consultas internas del funcionamiento de chord ya que el obtener un html asociado a una url puede tomar más tiempo.

Cuando un cliente se conecta a algún nodo que pertenece al anillo de chord, este nodo le envía al cliente, una lista de otros nodos a los cual el cliente puede hacer consultas de urls, que también pertenecen al anillo. El cliente introduce una url y una profundidad, entonces utilizando un método semejante a un bfs en el lado del cliente, en donde no se repiten consultas al anillo de chord de urls ya visitadas, se le pregunta al nodo por el html de la url necesitada, este nodo se encarga de hashear utilizando **SHA256** para obtener el id asociado a la url para entonces saber cual es el nodo encargado de obtener el html de dicha url, con este id, manda a hacer la consulta a dicho nodo y cuando este haya obtenido el html de la url, se lo devuelve al nodo que en un principio obtuvo la consulta del cliente y este se lo manda finalmente el resultado de la query. En caso de que el cliente no obtenga respuesta en un tiempo fijado, pues intenta consultar la misma url a otros nodos hasta obtener el resultado deseado. Una vez el html ha sido obtenido, se procede a extraer todos los links dentro del html si la profundidad es mayor que 1. Todos los htmls obtenidos son guardados en el directorio raiz de la ejecución del cliente.

Para poder ejecutar este proyecto es necesario correr las siguientes líneas.

En caso de querer ejecutar un nodo que pertenezca al anillo de chord:

    python3 main.py <ip del nodo de chord> <ip de algún nodo dentro del anillo de chord>

En caso de querer ejecutar un cliente para realizar consultas de urls:

    python3 main_client.py <ip de algún nodo dentro del anillo de chord>

Luego de esto deberá introducir la url y la profundidad deseada.