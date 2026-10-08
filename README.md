 #INSTRUCCIONES DE INSTALACIÓN

    Crear la estructura de carpetas:

bash

mkdir -p lacasanueva/models
mkdir -p lacasanueva/views
mkdir -p lacasanueva/security
mkdir -p lacasanueva/static/description

    Copiar todos los archivos en sus respectivas ubicaciones

    Actualizar el módulo en Odoo:

bash

# Reiniciar Odoo
sudo systemctl restart odoo18

# Actualizar lista de módulos
./odoo-bin -c /etc/odoo18.conf -u lacasanueva --stop-after-init

    Instalar el módulo:

    Ir a Apps → Actualizar lista de aplicaciones

    Buscar "La Casa Nueva"

    Instalar el módulo

    Configurar usuarios asociados:

    Ir a Ajustes → Usuarios

    Marcar el checkbox "Es Asociado" en los usuarios correspondientes

CARACTERÍSTICAS IMPLEMENTADAS:

✅ Modificación manual de stock desde la ficha del producto
✅ Sincronización automática con el sitio web
✅ Campo check "Es Asociado" en usuarios
✅ Restricción de permisos solo para asociados
✅ Uso de <list> en lugar de <tree> (Odoo 18)
✅ Sin uso de attrs (usando invisible con expresiones)
✅ Compatibilidad con Odoo 18
✅ Manejo de errores y validaciones
✅ Tracking de modificaciones
✅ Botones intuitivos en la interfaz
✅ Dashboard financiero "Balance de Compras y Ventas"
✅ Diseño visual al estilo de los tableros nativos de Odoo 18
✅ Panel lateral colapsable con el nombre del reporte
✅ Botón "Compartir" que copia el enlace del reporte
✅ Gráfico de barras con Chart.js (Ventas, Compras y Ganancia/Pérdida)
✅ Gráfico lineal con la evolución mensual de ventas y compras juntas
✅ Filtros de fecha: Año, Mes, Trimestre, Rango de fechas y Fecha específica
✅ Resumen numérico con totales y cambio de color según ganancia o pérdida

FUNCIONAMIENTO:

    Usuario Asociado accede a la ficha de un producto

    Ingresa el stock manual deseado

    Clic en "Actualizar Stock Manual"

    El sistema:

        Actualiza el stock real del producto

        Sincroniza con el sitio web

        Registra quién y cuándo hizo la modificación

    El stock modificado se refleja inmediatamente en el sitio web

    
#LISTA COMPLETA DE FUNCIONALIDADES Y SU UBICACIÓN

A. Campo "Es Asociado" en Usuarios
text

📍 Ubicación: Ajustes → Usuarios → Usuario específico → Pestaña "Derechos de acceso"
✅ Qué ver: Checkbox "Es Asociado" en la sección "La Casa Nueva"

B. Stock Manual en Plantilla de Producto
text

📍 Ubicación: Inventario → Productos → Productos → Seleccionar producto → Pestaña "Inventario"
✅ Qué ver: 
   - Campo "Stock Manual" (editable)
   - Campo "Modificado Manualmente" (solo lectura)
   - Campo "Última Actualización" (solo lectura)
   - Campo "Actualizado Por" (solo lectura)
   - Botón "Actualizar Stock Manual" (verde)
   - Botón "Sincronizar con Sitio Web" (gris)

C. Stock Manual en Variantes de Producto
text

📍 Ubicación: Inventario → Productos → Variantes de producto
✅ Qué ver:
   - Mismo grupo de campos que en la plantilla
   - Botón "Actualizar Stock Real"
   - Botón "Sincronizar con Sitio Web"

D. Dashboard Financiero "Balance de Compras y Ventas"
text

📍 Ubicación: Menú principal "Reportes La Casa Nueva" → "Balance de Compras y Ventas"
✅ Qué ver:
   - Panel de control superior al estilo de los tableros de Odoo 18 (título en miga de pan, filtros y botón "Compartir")
   - Filtros horizontales en el panel de control, al estilo de Odoo 18
   - Panel lateral colapsable "Reportes" con el nombre del reporte activo (preparado para futuros reportes con gráficos)
   - Panel de filtros de fecha (Año, Mes, Trimestre, Rango de fechas, Fecha específica)
   - Gráfico de barras con los totales (Ventas, Compras y Ganancia/Pérdida)
   - Gráfico lineal con la evolución mensual de ventas y compras en el mismo gráfico
   - Resumen numérico con tres tarjetas en colores suaves: Ventas (azul), Compras (rosado) y Ganancia/Pérdida (verde suave si hay ganancia, coral suave si hay pérdida)
   - Indicador de carga mientras se consultan los datos
   - Mensaje de error visible si la consulta falla
✅ Funcionamiento:
   - El menú abre una acción de cliente (ir.actions.client) con la etiqueta "lacasanueva.finance_balance"
   - El JavaScript (static/src/js/finance_balance.js) llama al modelo "finance.balance.analysis"
   - El modelo (models/finance_balance.py) calcula los totales de las facturas contables publicadas
     (out_invoice para ventas, in_invoice para compras) dentro del rango de fechas seleccionado
   - La ganancia/pérdida se calcula como: Ventas - Compras
   - El gráfico se dibuja con Chart.js (se carga desde /web/static/lib/Chart/Chart.js)
✅ Requisitos:
   - Módulo "account" (añadido como dependencia en el manifest)
   - Los assets del backend (JS y plantilla XML) se cargan automáticamente vía "web.assets_backend"
✅ Archivos involucrados:
   - models/finance_balance.py (modelo con el cálculo de datos)
   - views/finance_balance_views.xml (acción de cliente y menús)
   - static/src/js/finance_balance.js (lógica del dashboard)
   - static/src/xml/finance_balance.xml (plantilla del dashboard)

NOTA SOBRE CAMBIOS DE REPOSITORIO:
text

✅ El archivo .gitignore ahora ignora correctamente las carpetas __pycache__ (antes tenía el
   patrón "_pycache_" que no funcionaba) y la carpeta local "scrips"
✅ Los archivos .pyc fueron quitados del control de versiones (git rm --cached); siguen en disco
   pero ya no se versionan
✅ Los archivos nuevos del dashboard (models/finance_balance.py, views/finance_balance_views.xml,
   static/src/) aún no están confirmados en git; están listos para agregar y commitear

#PRUEBAS

## Pruebas automáticas (Python)

Ejecutar los tests del módulo:

bash

./odoo-bin -c odoo.conf -d <nombre_de_la_base> --test-enable --test-tags=lacasanueva -u lacasanueva --stop-after-init

Los tests (tests/test_finance_balance.py) verifican:
✅ Totales de ventas, compras y ganancia/pérdida
✅ Solo se cuentan facturas publicadas (state='posted')
✅ El rango de fechas limita los resultados (inclusive en los extremos)
✅ Serie mensual con varios meses (ventas y compras por mes)
✅ Meses sin facturas se rellenan con 0
✅ Sin facturas: etiquetas y series en 0
✅ Etiquetas y series siempre tienen la misma longitud

## Pruebas manuales (gráficos)

1. Ir a "Reportes La Casa Nueva" → "Balance de Compras y Ventas"
2. Verificar:
✅ El gráfico de barras muestra 3 barras: Ventas (azul), Compras (rosado) y
   Ganancia/Pérdida (verde suave si hay ganancia, coral suave si hay pérdida)
✅ El gráfico lineal muestra 2 líneas (Ventas azul, Compras magenta) con sombra
   degradada hacia abajo
✅ Las etiquetas del eje X muestran "ene 2026", "feb 2026", etc.
✅ Al cambiar el filtro (Año / Mes / Trimestre / Rango / Fecha específica) y pulsar
   "Consultar", ambos gráficos se actualizan
✅ Con un rango sin facturas publicadas, barras y líneas quedan en 0
✅ El panel lateral izquierdo se colapsa y expande con el botón <</>>
✅ El botón "Compartir" muestra una notificación
✅ Si la consulta falla, se muestra una alerta de error en rojo