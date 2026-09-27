# Preparar el repositorio sin datos privados

## Qué se comparte

Código fuente, dependencias, documentación y `iniciar.bat`, que resuelve la carpeta del proyecto de forma relativa. El lanzador personal `AbrirKiosco.bat` se conserva localmente y queda excluido por contener configuración del entorno.

El `.gitignore` excluye entornos virtuales, SQLite y sus archivos auxiliares, secretos de Streamlit, archivos `.env`, copias JSON con nombres habituales, exportaciones, registros y carpetas de trabajo locales. Para copias con cualquier otro nombre, usá `backups/` o `private/`, o guardalas fuera del proyecto. No todos los archivos JSON son privados, por lo que no se excluye globalmente esa extensión.

Los ejemplos declarados en `seed_demo_data()` usan correos del dominio `.test`; antes de publicar, confirmar que los nombres, teléfonos y el nombre comercial visible sean apropiados para compartir. Si se agregan capturas, generarlas con datos ficticios y sin rutas, usuarios del equipo ni datos de clientes o proveedores reales.

## Primer commit

El repositorio local se puede inicializar con `git init -b main` si todavía no existe `.git`. La preparación del repositorio no publica nada en internet.

Revisar primero:

```bash
git status --short --untracked-files=all
git check-ignore -v inventario.db AbrirKiosco.bat .venv/
```

Agregar explícitamente los archivos compartibles:

```bash
git add .gitignore README.md requirements.txt app.py database.py theme.py iniciar.bat pages/inventario.py pages/venta_libre.py pages/historial_ventas.py pages/proveedores.py pages/ganancias.py docs/DESARROLLO.md docs/PUBLICACION.md
git diff --cached --stat
git diff --cached
git diff --cached --check
git ls-files
```

Verificar que esa lista no incluya bases de datos, copias, credenciales ni el lanzador personal. Después, crear el commit con el mensaje propuesto en [DESARROLLO.md](DESARROLLO.md). Si Git solicita identidad, configurar el nombre y correo que se quieran publicar; se puede usar un correo de privacidad proporcionado por el alojamiento. No copiar automáticamente la identidad privada del equipo a la documentación.

La identidad del commit puede revisarse con `git var GIT_AUTHOR_IDENT` y `git var GIT_COMMITTER_IDENT`; esos comandos muestran información personal, por lo que su salida no debe adjuntarse al repositorio.

## Antes de subirlo

Crear el repositorio remoto en la cuenta elegida y seguir sus instrucciones para asociar la URL y subir la rama `main`. Revisar también los commits previos a cualquier envío: `.gitignore` solo evita incorporar archivos sin seguimiento; no elimina secretos de archivos ya versionados ni de commits anteriores.

Si por error se agregó un archivo privado al área de preparación antes del primer commit, `git rm --cached -- nombre-del-archivo` lo retira del índice y conserva la copia local. Si ya fue confirmado, quitarlo del último estado no lo borra del historial: hay que sanear el historial antes de compartirlo y revocar credenciales expuestas si corresponde.

Elegir una licencia explícitamente antes de ofrecer permisos de reutilización; esta preparación no asigna una en nombre del autor. Conservar los avisos de cualquier material de terceros que se incorpore.

## Copias y comprobaciones

Git conserva el código, no los datos operativos excluidos. Mantener copias de seguridad del negocio fuera del repositorio. Para comprobar instalación o funcionalidades sin alterar el inventario real, usar una copia del código en otra carpeta, sin trasladar `inventario.db`, e instalar las dependencias allí.
