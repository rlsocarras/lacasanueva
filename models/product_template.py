# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manual_stock = fields.Float(
        string='Stock Manual',
        help='Stock modificado manualmente por usuarios asociados',
        digits='Product Unit of Measure',
        tracking=True,
    )
    
    is_manual_stock_modified = fields.Boolean(
        string='Stock Modificado Manualmente',
        default=False,
        help='Indica si el stock fue modificado manualmente',
    )
    
    last_manual_stock_update = fields.Datetime(
        string='Última Actualización Manual',
        readonly=True,
    )
    
    last_manual_stock_user = fields.Many2one(
        'res.users',
        string='Actualizado Por',
        readonly=True,
    )

    @api.onchange('manual_stock')
    def _onchange_manual_stock(self):
        """Validación cuando se modifica el stock manual"""
        if self.manual_stock < 0:
            return {
                'warning': {
                    'title': 'Stock Negativo',
                    'message': 'El stock no puede ser negativo.',
                }
            }

    def action_update_manual_stock(self):
        """Actualizar el stock manual para todas las variantes del producto"""
        self.ensure_one()
        
        # Verificar si el usuario es asociado o administrador
        if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden modificar el stock manualmente.'))
        
        # Actualizar stock en todas las variantes
        for variant in self.product_variant_ids:
            variant.write({
                'manual_stock': self.manual_stock,
                'is_manual_stock_modified': True,
                'last_manual_stock_update': fields.Datetime.now(),
                'last_manual_stock_user': self.env.user.id,
            })
            
            # Actualizar el stock real
            variant.action_update_real_stock()
        
        # Actualizar la plantilla
        self.write({
            'is_manual_stock_modified': True,
            'last_manual_stock_update': fields.Datetime.now(),
            'last_manual_stock_user': self.env.user.id,
        })
        
        # Sincronizar con sitio web
        self.action_sync_stock_to_website()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': f'Stock actualizado correctamente a {self.manual_stock}',
                'type': 'success',
                'sticky': True,
            }
        }

    def action_sync_stock_to_website(self):
        """Sincronizar stock con el sitio web"""
        self.ensure_one()
        
        # Verificar permisos
        if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden sincronizar stock.'))
        
        # Actualizar disponibilidad en el sitio web
        self.website_published = True
        self.is_published = True
        
        # Actualizar información de stock para el sitio web
        for variant in self.product_variant_ids:
            variant._update_website_stock_internal()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Stock sincronizado con el sitio web correctamente',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        """Override para sincronizar automáticamente con el sitio web"""
        result = super(ProductTemplate, self).write(vals)
        
        if 'manual_stock' in vals and vals['manual_stock']:
            for record in self:
                if record.is_manual_stock_modified:
                    record.action_sync_stock_to_website()
        
        return result