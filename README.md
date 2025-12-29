# EFDOO

* Quiero que si entras al modo manual este el tiempo en 00:00, ahora mismo esta por default en 01:00
* Implementa que si se intenta iniciar el robot en 00:00 se impide y se notifica al usuario que antes debe ingresar tiempo en el temporizador
* Ahora mismo cuando el temporizador llega a 00:00, visualmente se queda en 00:01, esto es un error y hay que corregirlo.
* Cuando el temporizador llega a 0, quiero que salte el mismo mensaje que cuando termina una receta en el modo guiado pero obviamente con distinto texto, me refiero a que salte en cualquier página.
* Al cancelar, se resetean todos los gauges a 0, incluido el de tiempo, se pone en 00:00
* Si el robot se apaga mediante el switch (independientemente del estado en el que se encuentre el robot, ya sea pausado, en espera, cocinando, etc), se debe resetar todo (todos los gaugues a 0), incluido el selector de modo, que por defecto debe de estar en modo guiado.