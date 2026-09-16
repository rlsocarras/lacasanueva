# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Campos propios de la variante
    manual_stock = fields.Float(
        string='Stock Manual',
        help='Stock modificado manualmente. NO afecta al stock real.',
        digits='Product Unit of Measure',
        tracking=True,
    )
    
    is_manual_stock_modified = fields.Boolean(
        string='Modificado Manualmente',
        default=False,
        tracking=True,
    )
    
    last_manual_stock_update = fields.Datetime(
        string='Última Actualización',
        readonly=True,
        tracking=True,
    )
    
    last_manual_stock_user = fields.Many2one(
        'res.users',
        string='Actualizado Por',
        readonly=True,
        tracking=True,
    )

    is_variant_view = fields.Boolean(
        string='Es Vista de Variante',
        compute='_compute_is_variant_view',
        store=False,
    )

    def _compute_is_variant_view(self):
        for product in self:
            product.is_variant_view = True

    @api.model
    def _check_user_permission(self):
        if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden modificar el stock manualmente.'))
        return True

    def action_sync_stock_to_website(self):
        self.ensure_one()
        self._check_user_permission()
        self._update_website_stock_internal()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': f'Stock manual ({self.manual_stock}) sincronizado',
                'type': 'success',
                'sticky': False,
            }
        }

    def _update_website_stock_internal(self):
        self.ensure_one()
        try:
            if self.manual_stock > 0:
                self.website_published = True
                self.is_published = True
            else:
                self.website_published = False
                self.is_published = False
            return True
        except Exception as e:
            _logger.error(f'Error al sincronizar con sitio web: {str(e)}')
            return False

    @api.onchange('manual_stock')
    def _onchange_manual_stock(self):
        if self.manual_stock < 0:
            return {
                'warning': {
                    'title': 'Stock Negativo',
                    'message': 'El stock manual no puede ser negativo.',
                }
            }

    def write(self, vals):
        if 'manual_stock' in vals:
            self._check_user_permission()
            vals['is_manual_stock_modified'] = True
            vals['last_manual_stock_update'] = fields.Datetime.now()
            vals['last_manual_stock_user'] = self.env.user.id
        
        result = super(ProductProduct, self).write(vals)
        
        if 'manual_stock' in vals:
            for record in self:
                record._update_website_stock_internal()
        
        return result