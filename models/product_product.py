# -*- coding: utf-8 -*-
from datetime import timedelta

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

    last_import_date = fields.Datetime(
        string='Última importación',
        compute='_compute_last_import_date',
        store=True,
        readonly=True,
    )

    modified_last_3_days = fields.Boolean(
        string='Modificado últimos 3 días',
        compute='_compute_modified_last_3_days',
        store=False,
    )

    is_variant_view = fields.Boolean(
        string='Es Vista de Variante',
        compute='_compute_is_variant_view',
        store=False,
    )

    manual_variant_label = fields.Char(
        string='Variante',
        compute='_compute_manual_variant_label',
        store=False,
    )

    # Campo para verificar si el usuario actual es asociado
    is_asociado = fields.Boolean(
        string='Es Asociado',
        compute='_compute_is_asociado',
        store=False,
        compute_sudo=False,
    )
    # CRÍTICO: Este campo DEBE existir en product.product
    stock_display_mode = fields.Selection(
        selection=[
            ('real', 'Stock Real'),
            ('manual', 'Stock Manual'),
        ],
        string='Mostrar en Sitio Web',
        related='product_tmpl_id.stock_display_mode',
        readonly=True,
        store=True,
    )
    
    # ✅ Verifica el GRUPO
    can_manage_manual_stock = fields.Boolean(
        string='Puede Gestionar Stock Manual',
        compute='_compute_can_manage_manual_stock',
        store=False,
        compute_sudo=False,
    )
    
    @api.depends_context('uid')
    def _compute_can_manage_manual_stock(self):
        has_group = self.env.user.has_group('lacasanueva.group_gestionar_stock_manual')
        for product in self:
            product.can_manage_manual_stock = has_group
            
    def _check_user_permission(self):
        """Verificar que el usuario tenga el grupo para modificar stock"""
        if not self.env.user.has_group('lacasanueva.group_gestionar_stock_manual'):
            raise UserError(_(
                'Solo los usuarios con el permiso "Gestionar stock manual" '
                'pueden modificar el stock manual.'
            ))
        return True        

    @api.depends_context('uid')
    def _compute_is_asociado(self):
        """Verificar si el usuario actual es asociado o admin"""
        is_asociado = (
            self.env.user.has_group('lacasanueva.group_gestionar_stock_manual')
        )
        for product in self:
            product.is_asociado = is_asociado

    def _compute_is_variant_view(self):
        for product in self:
            product.is_variant_view = True

    @api.depends('manual_stock')
    def _compute_last_import_date(self):
        for product in self:
            line = self.env['manual.stock.import.log.line'].search(
                [('product_id', '=', product.id), ('applied', '=', True)],
                order='id desc', limit=1)
            product.last_import_date = line.log_id.import_date if line else False

    @api.depends('product_template_attribute_value_ids')
    def _compute_manual_variant_label(self):
        for product in self:
            product.manual_variant_label = product.name if product.product_template_attribute_value_ids else 'Sin variante'

    @api.depends('last_manual_stock_update')
    def _compute_modified_last_3_days(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.last_manual_stock_update:
                rec.modified_last_3_days = (
                    rec.last_manual_stock_update.date() >= (today - timedelta(days=2))
                )
            else:
                rec.modified_last_3_days = False

    @api.model
    def _check_user_permission(self):
        if not self.env.user.has_group('lacasanueva.group_gestionar_stock_manual') and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden modificar el stock manualmente.'))
        return True

    def action_open_website(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'new',
        }

    website_link = fields.Char(
        string='Sitio Web',
        related='product_tmpl_id.website_url',
        store=False,
        readonly=True,
    )

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
                # ⭐ CAMBIO AUTOMÁTICO A MODO MANUAL
                record.product_tmpl_id.write({
                    'stock_display_mode': 'manual',
                 })
        
        return result