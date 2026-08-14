 #INSTRUCCIONES DE INSTALACIÓN

    Crear la estructura de carpetas:

bash

mkdir -p la_casa_nueva/models
mkdir -p la_casa_nueva/views
mkdir -p la_casa_nueva/security
mkdir -p la_casa_nueva/static/description

    Copiar todos los archivos en sus respectivas ubicaciones

    Actualizar el módulo en Odoo:

bash

# Reiniciar Odoo
sudo systemctl restart odoo18

# Actualizar lista de módulos
./odoo-bin -c /etc/odoo18.conf -u la_casa_nueva --stop-after-init

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