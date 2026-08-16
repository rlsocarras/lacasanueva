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