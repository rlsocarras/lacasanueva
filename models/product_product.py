# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    manual_stock = fields.Float(
        string='Stock Manual',
        help='Stock modificado manualmente por usuarios asociados',
        digits='Product Unit of Measure',
        tracking=True,
        related='product_tmpl_id.manual_stock',
        store=True,
    )
    
    is_manual_stock_modified = fields.Boolean(
        string='Stock Modificado Manualmente',
        default=False,
        related='product_tmpl_id.is_manual_stock_modified',
        store=True,
    )
    
    last_manual_stock_update = fields.Datetime(
        string='Última Actualización Manual',
        readonly=True,
        related='product_tmpl_id.last_manual_stock_update',
        store=True,
    )
    
    last_manual_stock_user = fields.Many2one(
        'res.users',
        string='Actualizado Por',
        readonly=True,
        related='product_tmpl_id.last_manual_stock_user',
        store=True,
    )

    @api.model
    def _check_user_permission(self):
        """Verificar si el usuario tiene permisos para modificar stock"""
        if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden modificar el stock manualmente.'))
        return True

    def action_update_real_stock(self):
        """Actualizar el stock real del producto"""
        self.ensure_one()
        
        # Verificar permisos
        self._check_user_permission()
        
        try:
            # Obtener la cantidad actual en stock
            current_stock = self.qty_available
            manual_stock = self.manual_stock
            
            _logger.info(f"Actualizando stock de {self.name}: {current_stock} -> {manual_stock}")
            
            # Usar el wizard de cambio de stock
            stock_change_wizard = self.env['stock.change.product.qty'].create({
                'product_id': self.id,
                'product_tmpl_id': self.product_tmpl_id.id,
                'new_quantity': manual_stock,
            })
            
            stock_change_wizard.change_product_qty()
            
            _logger.info(f'Stock actualizado para producto {self.name}: {current_stock} -> {manual_stock}')
            
            # Marcar como modificado en el template
            self.product_tmpl_id.write({
                'is_manual_stock_modified': True,
                'last_manual_stock_update': fields.Datetime.now(),
                'last_manual_stock_user': self.env.user.id,
            })
            
            # Sincronizar con el sitio web
            self._update_website_stock_internal()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': f'Stock actualizado correctamente: {current_stock} -> {manual_stock}',
                    'type': 'success',
                    'sticky': True,
                }
            }
                
        except Exception as e:
            _logger.error(f'Error al actualizar stock: {str(e)}')
            raise UserError(_('Error al actualizar el stock: %s') % str(e))

    def action_sync_stock_to_website(self):
        """Método público para sincronizar stock con el sitio web"""
        self.ensure_one()
        
        try:
            # Verificar permisos
            self._check_user_permission()
            
            # Actualizar información de stock para el sitio web
            self._update_website_stock_internal()
            
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
            
        except Exception as e:
            _logger.error(f'Error al sincronizar con sitio web: {str(e)}')
            raise UserError(_('Error al sincronizar con sitio web: %s') % str(e))

    def _update_website_stock_internal(self):
        """Método interno para actualizar disponibilidad en el sitio web"""
        self.ensure_one()
        
        try:
            # Actualizar información de stock para el sitio web
            if self.manual_stock > 0:
                self.website_published = True
                self.is_published = True
            else:
                self.website_published = False
                self.is_published = False
            
            # Actualizar disponibilidad en el template
            if self.product_tmpl_id:
                self.product_tmpl_id.sudo().write({
                    'website_published': self.website_published,
                })
            
            return True
        except Exception as e:
            _logger.error(f'Error al sincronizar con sitio web: {str(e)}')
            return False

    @api.onchange('manual_stock')
    def _onchange_manual_stock(self):
        """Manejar cambios en el stock manual"""
        if self.manual_stock < 0:
            return {
                'warning': {
                    'title': 'Stock Negativo',
                    'message': 'El stock no puede ser negativo.',
                }
            }

    def write(self, vals):
        """Override para manejar actualizaciones de stock"""
        # Verificar si se está modificando el stock manual
        if 'manual_stock' in vals and vals['manual_stock'] is not None:
            self._check_user_permission()
            
        result = super(ProductProduct, self).write(vals)
        
        return result