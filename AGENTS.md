# AGENTS.md

## Module update workflow

After making changes to this Odoo module, restart Odoo and update the module:

```bash
sudo systemctl restart odoo18
./odoo-bin -c /etc/odoo18.conf -u lacasanueva --stop-after-init
```
