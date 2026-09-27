# Desarrollo, autoría e historial

## Cómo se construyó

Según el relato del autor, el sistema se desarrolló por etapas, con asistencia de IA en gran parte del código. El autor definió funcionalidades y decisiones de diseño, revisó y ajustó implementaciones y modificó manualmente partes del HTML y del frontend. Esta descripción reconoce ambas contribuciones sin asignar porcentajes que no se pueden comprobar.

La IA se utilizó como herramienta de asistencia. No se atribuye al autor la escritura manual de todo el código ni se presenta el sistema como una generación automática sin intervención humana. No se publican conversaciones completas: pueden contener información del negocio o del entorno.

## Punto de partida de Git

Al preparar esta documentación, la carpeta no tenía un repositorio `.git`. El código ya contenía las funciones descritas en el README. No hay evidencia aquí para fechar cada etapa ni reconstruir commits originales.

La opción recomendada es un commit inicial honesto con la versión existente y, desde ese momento, commits pequeños por cambio real. Un único commit inicial no implica que el software se haya creado de una sola vez.

Mensaje sugerido para el primer commit:

```text
chore: incorporar la versión existente del sistema de kiosco

Importar la aplicación desarrollada de forma incremental antes de usar Git.
Incluye inventario, ventas, proveedores, reportes e interfaz personalizada.
Agregar documentación, exclusiones de datos locales y lanzador portable.
El README describe la asistencia de IA y la participación del autor.
```

No conviene dividir artificialmente los archivos actuales en commits llamados «agregar ventas» o «crear inventario» para simular sesiones anteriores: esas funciones ya existían y esos cortes podrían dejar versiones que no arrancan. Tampoco cambiar fechas ni inventar autores o pruebas realizadas.

Si se conservan versiones anteriores auténticas y se desea recuperarlas, revisar primero sus datos privados y describirlas como importaciones de versiones conservadas; registrar únicamente fechas originales comprobables, sin presentarlas como commits que ya existían.

## Commits futuros por funcionalidad

Ejemplos de mensajes para usar **solamente cuando esos cambios se realicen**:

| Cambio real | Mensaje sugerido |
| --- | --- |
| Hacer opcional la carga de ejemplos | `fix: evitar la reposición automática de datos de ejemplo` |
| Agregar un filtro por fecha | `feat: filtrar el historial de ventas por período` |
| Modificar HTML/CSS para pantallas pequeñas | `style: mejorar el carrito en pantallas pequeñas` |
| Separar reglas de venta de SQL | `refactor: separar la lógica de ventas de la persistencia` |
| Incorporar una prueba de stock insuficiente | `test: verificar que una venta sin stock no altere los datos` |
| Actualizar instrucciones de instalación | `docs: actualizar la instalación en Windows` |

Cada commit debe explicar qué cambió y por qué, incluir los archivos que forman una unidad funcional y mantener la aplicación utilizable. Antes de confirmar, revisar `git diff --cached` y verificar el flujo afectado con datos ficticios. Registrar qué se comprobó y cualquier limitación real; no afirmar «probado» si solo se revisó el código.

## Cómo reflejar la asistencia de IA

- Mantener una explicación general en el README, sin etiquetas repetitivas en cada línea.
- En cambios relevantes, describir tareas concretas: qué propuso la IA, qué se corrigió manualmente, qué decisión tomó el autor y cómo se verificó el resultado.
- Usar primera persona solo para participación que el autor pueda sostener. No atribuir modificaciones a un archivo o sesión específica sin evidencia.
- Evitar porcentajes de autoría, cronologías inventadas y afirmaciones de revisión exhaustiva.
- No incluir conversaciones, capturas o prompts con datos reales como prueba de participación. Una descripción del cambio y su diff suelen ser suficientes.

Plantilla opcional para el cuerpo de un commit o una solicitud de cambios:

```text
Motivo: [problema observado]
Cambio: [comportamiento resultante]
Asistencia de IA: [tarea concreta, si corresponde]
Intervención del autor: [decisiones, revisión o edición manual realizada]
Verificación: [comprobación efectivamente realizada y resultado]
```
