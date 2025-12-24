# EFDOO

## Bugs

### Bug — Receta con un único paso manual no muestra la card de completado
```ruby
En una app NiceGUI que ejecuta recetas paso a paso en un RobotCocina, cada receta puede tener pasos manuales y automáticos.

Bug actual:
Si una receta tiene solo un paso manual, al confirmar ese paso:

- No aparece la card de “¡Receta Completada!”
- El sistema vuelve directamente al estado “en espera”, como si nunca hubiera terminado.

En recetas con más pasos o con pasos automáticos, esto no ocurre.

Objetivo:
Corregir la lógica del robot / UI para que:

- Una receta con un único paso manual se considere completada correctamente.
- Se muestre la card de completado exactamente igual que en el resto de recetas.

Analiza el flujo de estados (ESPERANDO_CONFIRMACION, avance de índice de paso, final de receta) y dame el código final completo que haya que modificar.
```

## Features a implementar

### Feature — Notificación global cuando termina una receta (en cualquier página)
```ruby
Quiero añadir una notificación temporal global cuando una receta termina.

Requisitos:

- Debe aparecer arriba de la pantalla (tipo toast / notify).
- Debe dispararse aunque el usuario esté en otra página distinta del dashboard.
- Debe mostrarse una sola vez por receta completada.
- El sistema ya usa ui.notify y callbacks de actualización del RobotCocina.

Objetivo:
Diseñar e implementar una solución limpia para:

- Detectar de forma centralizada que una receta ha finalizado.
- Lanzar la notificación independientemente de la vista actual.

Dame el código completo final necesario (estado global, callback, cambios en el robot o UI) listo para copiar y pegar.
```

### Feature — Mostrar temperatura, velocidad y cuenta atrás en el paso automático
```ruby
En la card de paso automático (la que muestra una barra de progreso relativa al paso), quiero ampliar la información.

Estado actual:

- Solo se muestra el porcentaje del paso y la barra.

Nuevo comportamiento deseado:

- Mostrar temperatura, velocidad y tiempo restante del paso.
- El tiempo debe verse como cuenta atrás (mm:ss).
- La cuenta atrás debe estar sincronizada con la barra de progreso.
- Los valores vienen de PasoReceta (temperatura, tiempo_segundos, velocidad), no del proceso.

Objetivo:
Modificar la UI y la lógica de actualización para que:

- La card muestre claramente esos parámetros.
- El tiempo restante se calcule correctamente incluso al pausar/reanudar.

Dame el código completo final de la card y de la función de actualización del paso automático.
```

### Feature — Persistir los datos del formulario “Crear Receta” al cambiar de página
```ruby
En la vista de crear receta, el usuario introduce nombre, descripción, ingredientes y pasos.

Problema actual:
Si el usuario cambia de página (por ejemplo, vuelve al dashboard para monitorizar una cocción) y luego regresa, todos los datos escritos se pierden.

Objetivo:
Implementar persistencia temporal para que:

- Los datos del formulario se mantengan aunque el usuario navegue entre páginas.
- No se guarden todavía en base de datos (solo estado en memoria).
- Al volver a la vista de crear receta, los campos se restauren automáticamente.

Usa un enfoque coherente con NiceGUI (estado global, sesión o estructura compartida).

Dame el código final completo de la solución.
```

### Feature — Hacer más grande el botón de encendido/apagado del robot
```ruby
En el dashboard hay un switch/botón de encendido y apagado del robot que actualmente es pequeño y poco visible.

Objetivo de UI/UX:

- Hacerlo significativamente más grande y claro.
- Que visualmente comunique mejor ON / OFF (tamaño, color, icono o layout).
- Mantener la lógica actual de encendido/apagado sin cambios funcionales.

La app usa NiceGUI con clases Tailwind.

Dame el código final completo del componente de encendido/apagado con el nuevo diseño aplicado.
```

## Última implementación - Modo Manual Completo

```ruby
Objetivo general
Implementar **modo manual real** con una card de controles (Temperatura, Tiempo, Velocidad) que permita cocinar de forma directa y segura, reutilizando los controles de inicio/pausa/cancelar existentes. El cambio debe integrarse con el RobotCocina ya refactorizado (parámetros por paso), persistir entre páginas y respetar la lógica de apagado actual.

Contexto (lo que ya existe / supuestos)
- El sistema usa NiceGUI para la UI.
- Hay un modelo `RobotCocina` que gestiona estados (APAGADO, ESPERA, COCINANDO, PAUSADO, ESPERANDO_CONFIRMACION, ERROR) y un hilo de ejecución.
- Tras el refactor, los parámetros de ejecución (tiempo, temp, vel) vivirán en `PasoReceta` para recetas; aquí desplegamos un modo separado para control manual independiente.
- Queremos **eliminar** la restricción: “En modo manual no se usan recetas”. Manual vs Guiado pasa a ser un modo de control, pero la card manual ofrece una forma de ejecutar *cocción directa* (standalone). Si se inicia una receta y ya hay una cocción manual activa, una política clara debe aplicarse (ver abajo).

Requisitos funcionales concretos (comportamiento esperado)
1. Card de controles manuales (ubicación: dashboard / panel de control)
   - Muestra y permite ajustar en todo momento:
     - Temperatura: slider / número (min 0, max 120)
     - Velocidad: slider / número (min 0, max 10)
     - Tiempo restante: control tipo “ruleta/selector” o slider inteligente con la granularidad descrita (ver 3)
   - Visualiza los valores actuales en texto (p. ej. `Temp: 95°C · Vel: 4 · Tiempo: 02:35`).
   - Reutiliza los botones principales de control (INICIAR/REANUDAR, PAUSAR, CANCELAR) de la card de control de cocción. Es decir: la card manual no duplica lógica de inicio/pausa/cancelar sino que las invoca sobre el robot.
   - Permite ajustar cualquier control **en caliente** mientras se cocina (los cambios se aplican inmediatamente).

2. Eliminación de la restricción “En modo manual no se usan recetas”
   - El usuario puede seleccionar una receta en Modo Manual. Comportamiento definido:
     - Si **hay una cocción manual activa** y el usuario inicia una receta → **la cocción manual se cancelará** y la receta se iniciará (notificar al usuario).
     - Si **hay una receta en curso** y el usuario inicia manual (INICIAR desde la card manual) → la receta en curso se cancelará y la cocción manual se iniciará.
     - Esta política evita conflictos ambiguos e impondrá una única ejecución activa a la vez. (Se notificará y se usará diálogo de confirmación si procede.)

3. Control del tiempo (experiencia tipo microondas / Thermomix)
   - La ruleta/selector del tiempo:
     - Incrementa en segundos hasta 60s con saltos razonables (p. ej. 5s, 10s, 15s...60s).
     - A partir de 1 minuto, incrementos en minutos (1,2,3,...,90).
     - Interacción: subir/bajar cambia **el tiempo restante** instantáneamente; no se requieren botones “+30s” ni similares, pero puede existir un pequeño conjunto de atajos si el UI lo necesita.
   - Tiempo máximo: 90 minutos (5400 s). El temporizador acepta mínimo operativo 1s para iniciar.
   - Si el temporizador llega a 0 → la cocción termina y el robot pasa a ESPERA. (Comportamiento igual que recetas automáticas.)

4. Pausar / Reanudar / Cancelar
   - Pausar: detiene decremento del temporizador; al reanudar continúa desde tiempo restante.
   - Cancelar: detiene la cocción y pone los controles manuales a 0 (temp 0, vel 0, tiempo 0) y robot a ESPERA.
   - Ajustar tiempo mientras está cocinando (por ejemplo de 2min a 5min) modifica inmediatamente el tiempo restante.

5. Persistencia entre páginas
   - La cocción manual (hilo/timer) persiste aunque el usuario navegue a otra página del UI. La UI debe re-sincronizarse mostrando el estado actual al volver.
   - Si la sesión del servidor se reinicia o el robot se apaga, se aplica la lógica existente: todo se apaga y UI se refresca.

6. Integración con robot existente y seguridad
   - Reutilizar y extender `RobotCocina`:
     - Añadir API/funciones: `iniciar_manual(temp, vel, tiempo)`, `ajustar_manual(temp?, vel?, tiempo?)`, `pausar_manual()`, `cancelar_manual()`, propiedades de estado `manual_activo`, `manual_tiempo_restante`, etc.
     - La ejecución manual usa el mismo mecanismo de hilo que las recetas (o un hilo claro y coordinado) para contar tiempo y actualizar progreso. Evitar condiciones de carrera con la ejecución de recetas.
   - En caso de apagado `RobotCocina.apagar()` debe detener cualquier cocción manual según la lógica actual y notificar UI.
   - Validaciones: temp 0–120, vel 0–10, tiempo 1s–5400s. Aplicar límites en UI y en el backend.

7. UX / accesibilidad y componentes sugeridos
   - Temperatura y Velocidad: sliders con input numérico sincronizado (para precisión).
   - Tiempo: componente mixto “wheel + numeric display” o slider con saltos; debe permitir precisión de segundos hasta 60s y luego minutos.
   - Mostrar progreso visual (barra o circular) y tiempo restante en formato mm:ss.
   - Hacer que los controles no sean ortopédicos: interacción natural y fluida, sin múltiples botones duplicados.

Políticas operativas y prioridad
- Solo una ejecución activa a la vez (manual o receta); iniciar una nueva cancela la anterior tras confirmación (si procede).
- Ajustes manuales aplican inmediatamente al estado actual del robot.
- Persistencia entre páginas mediante el estado del objeto `RobotCocina` en memoria; no es necesario persistir al disco.

Plan por fases (entregas claras y seguras)
Fase 1 — Diseño + API backend (entrega mínima viable)
- Diseñar la API de `RobotCocina` para soporte manual: firmas y semántica de funciones.
- Implementar métodos `iniciar_manual`, `ajustar_manual`, `pausar_manual`, `cancelar_manual` en `robot/modelos.py`. El hilo de ejecución ya existente debe poder manejar temporizadores decrecientes.
- Tests unitarios (pytest) para la lógica del temporizador (iniciar, decrementar, pausar, reanudar, cancelar).
Commit message sugerido: `robot: add manual cooking API and timer support`

Fase 2 — UI mínima funcional
- En `robot/vistas.py` añadir la card de controles manuales (NiceGUI).
- Conectar botones INICIAR/PAUSAR/CANCELAR existentes para invocar las nuevas APIs.
- Implementar sliders / inputs para temp, vel y el control de tiempo con la granularidad indicada.
- UI debe mostrar estado actual y persistir al navegar.
- Tests manuales: iniciar manual, ajustar en caliente, pausar, reanudar, cancelar, navegar de página y verificar persistencia.
Commit message sugerido: `ui: add manual control card and bind to robot manual API`

Fase 3 — Integración con recetas y políticas de prioridad
- Implementar la política de preempción: iniciar receta cancela manual y viceversa; añadir diálogos de confirmación si necesario.
- Asegurar que si una receta está en curso, la card manual está en modo “disponible” pero iniciar manual cancela receta.
- Tests de integración: iniciar receta en modo manual y viceversa.
Commit message sugerido: `integration: reconcile manual cooking and recipe execution with preemption policy`

Fase 4 — Pulir UX + robustez
- Ajustes finos del control de tiempo (saltos, rueda), animaciones, notificaciones.
- Manejo de edge-cases: redondeos temporales, sincronización UI-thread, reintentos si callback falla.
- Pruebas E2E (manuales + automatizadas si posible).
Commit message sugerido: `ui: polish manual controls, accessibility and edge cases`

Entregables por fase
- Fase 1: diff/patch de `robot/modelos.py` con nuevas funciones y tests unitarios.
- Fase 2: diff/patch de `robot/vistas.py` (card completa), snippets de componentes (sliders, wheel), y pasos de verificación en README.
- Fase 3: cambios en control de flujo (`robot/modelos.py` + `vistas.py`) y pruebas de integración.
- Fase 4: mejoras, documentación y tests E2E.

Archivos / funciones a modificar (lista explícita)
- `robot/modelos.py`
  - Añadir: `iniciar_manual(temp, vel, tiempo)`, `ajustar_manual(...)`, `pausar_manual()`, `cancelar_manual()`
  - Estado interno: `_manual_activo`, `_manual_tiempo_restante`, `_manual_temp`, `_manual_vel`, protección con `_lock`
  - Ajustar hilo de ejecución para soportar decremento de temporizador y comunicación con UI.
- `robot/vistas.py`
  - Añadir la nueva card de controles manuales al dashboard.
  - Conectar botones existentes INICIAR/PAUSAR/CANCELAR a llamadas que respeten si se está en modo manual o ejecutando receta.
  - Lógica frontend para ajustar parámetros en caliente y enviar `ajustar_manual` al backend.
- `robot/servicios.py` (si fuera necesario)
  - Exponer funciones para que la UI llame a la API del robot (si existe una capa de servicios).
- Tests:
  - `tests/test_robot_manual.py` con casos de temporizador y controles.

Criterios de aceptación (QA)
1. La card manual permite ajustar temp/vel/tiempo y muestra valores actuales.
2. Comportamiento del temporizador:
   - Iniciar hace decrementar el tiempo.
   - Pausar detiene la cuenta.
   - Reanudar continúa.
   - Cancelar pone todo a 0 y deja robot en ESPERA.
3. Ajustes en caliente afectan inmediatamente la ejecución en curso.
4. Persistencia entre páginas: navegar fuera y volver muestra estado correcto y temporizador sigue vivo.
5. Al iniciar receta mientras hay ejecución manual activa, la ejecución manual se cancela (y viceversa) con notificación.
6. Apagar el robot detiene todo y deja el estado como ahora (apagar/reseteo).
7. Validaciones: temp 0–120, vel 0–10, tiempo 1–5400s. UI y backend aplican las mismas restricciones.

Notas técnicas adicionales y consideraciones
- Evitar duplicar lógica de ejecución: reutilizar el modelo de ejecución por pasos para el temporizador (un paso virtual `PasoReceta` podría usarse internamente), aunque no se persista.
- Sincronización: usar `_lock` cuando se muta estado del robot; la UI debe leer estado de forma atómica.
- Eventos / callbacks: preferir notificaciones websocket / push (NiceGUI bindings) para actualizar la UI en tiempo real.
- No persistir la cocción manual en DB; persistir en memoria para mantener simplicidad (se persiste solo mientras el servidor esté vivo). Documentar esto.
- Documentar claramente el comportamiento en caso de reinicio del servidor o pérdida de energía.

Formato de entrega requerido
- Para cada fase: patch/diff o ficheros completos modificados listos para copiar/pegar.
- Tests unitarios (pytest) correspondientes.
- README con pasos de verificación y comandos para ejecutar pruebas.
- Commit message sugeridos incluidos en cada fase.

Instrucción final para Claude
- Trabaja por fases y entrega los artefactos indicados en cada fase.
- Incluye en cada entrega: el código completo modificado, tests, instrucciones de verificación y el commit message sugerido.
- No rompas compatibilidad existente de `RobotCocina` hasta que las pruebas de la fase anterior pasen.
- Si hay decisiones de diseño que deban tomarse (por ejemplo: “¿la cocción manual debe persistir tras reboot?”), propone la opción por defecto y documenta trade-offs.

---  
Fin del prompt.  
Pega todo esto y procede por fases como indiqué.  

```