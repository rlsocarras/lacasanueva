# AGENTS.md

## Module update workflow

After making changes to this Odoo module, restart Odoo and update the module:

```bash
sudo systemctl restart odoo18
./odoo-bin -c /etc/odoo18.conf -u lacasanueva --stop-after-init
```

# Instrucciones para Odoo 18

## Fuente de verdad
- **Prioriza siempre** el código base local de Odoo 18 (carpetas `addons/` y `odoo/addons/`).
- **Prohibido** buscar en la web código de Odoo si ya existe en el repositorio local.
- Para APIs o comportamientos, inspecciona primero los archivos locales.

## Rutas de referencia
- Módulos base: `./odoo/addons/`
- Módulos estándar: `./addons/`
- Módulos custom: `./custom-addons/`
