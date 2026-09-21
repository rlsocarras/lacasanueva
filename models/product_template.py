# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campo editable en template (solo si tiene 1 variante)
    manual_stock = fields.Float(
        string='Stock Manual',
        help='Stock manual. Editable cuando el producto tiene 1 variante o ninguna.',
        digits='Product Unit of Measure',
        compute='_compute_manual_stock',
        inverse='_inverse_manual_stock',
        store=True,
    )

    is_manual_stock_modified = fields.Boolean(
        string='Modificado Manualmente',
        default=False,
        tracking=True,
        store=True,
    )
    
    # Campos resumen (siempre readonly)
    manual_stock_summary = fields.Float(
        string='Stock Manual Total',
        help='Suma del stock manual de todas las variantes.',
        digits='Product Unit of Measure',
        compute='_compute_manual_stock_summary',
        store=True,
    )
    
    is_manual_stock_modified_summary = fields.Boolean(
        string='Modificado',
        compute='_compute_manual_stock_summary',
        store=True,
    )
    
    last_manual_stock_update_summary = fields.Datetime(
        string='Última Actualización',
        compute='_compute_manual_stock_summary',
        store=True,
    )
    
    last_manual_stock_user_summary = fields.Many2one(
        'res.users',
        string='Actualizado Por',
        compute='_compute_manual_stock_summary',
        store=True,
    )
    
    has_variants = fields.Boolean(
        string='Tiene Variantes',
        compute='_compute_has_variants',
    )

    is_variant_view = fields.Boolean(
        string='Es Vista de Variante',
        compute='_compute_is_variant_view',
        store=False,
    )

    # Campo para verificar si el usuario actual es asociado
    is_asociado = fields.Boolean(
        string='Es Asociado',
        compute='_compute_is_asociado',
        store=False,
        compute_sudo=False,
    )
    # ============================================
    # CAMPO: stock_display_mode (selector de stock)
    # ============================================
    stock_display_mode = fields.Selection(
        selection=[
            ('real', 'Stock Real'),
            ('manual', 'Stock Manual'),
        ],
        string='Mostrar en Sitio Web',
        default='real',
        required=True,
        help='Selecciona qué stock mostrar en el sitio web para este producto',
        tracking=True,
    )

    @api.depends_context('uid')
    def _compute_is_asociado(self):
        """Verificar si el usuario actual es asociado o admin"""
        is_asociado = (
            self.env.user.is_asociado 
        )
        for template in self:
            template.is_asociado = is_asociado

    def _compute_is_variant_view(self):
        for template in self:
            template.is_variant_view = False

    @api.depends('product_variant_ids.manual_stock')
    def _compute_manual_stock(self):
        """Stock manual del template (sincronizado con la variante única)"""
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.manual_stock = template.product_variant_ids.manual_stock
            else:
                template.manual_stock = 0.0

    def _inverse_manual_stock(self):
        """Escribir el stock manual en la variante única"""
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.write({
                    'manual_stock': template.manual_stock,
                })

    @api.depends('product_variant_ids.manual_stock',
                 'product_variant_ids.is_manual_stock_modified',
                 'product_variant_ids.last_manual_stock_update',
                 'product_variant_ids.last_manual_stock_user')
    def _compute_manual_stock_summary(self):
        """Resumen del stock manual de todas las variantes"""
        for template in self:
            variants = template.product_variant_ids
            
            template.manual_stock_summary = sum(variants.mapped('manual_stock'))
            
            template.is_manual_stock_modified_summary = any(
                variants.mapped('is_manual_stock_modified')
            )
            
            updates = [u for u in variants.mapped('last_manual_stock_update') if u]
            template.last_manual_stock_update_summary = max(updates) if updates else False
            
            users = [u for u in variants.mapped('last_manual_stock_user') if u]
            template.last_manual_stock_user_summary = users[-1] if users else False

    @api.depends('product_variant_count')
    def _compute_has_variants(self):
        for template in self:
            template.has_variants = template.product_variant_count > 1

    def action_sync_stock_to_website(self):
        """Sincronizar stock manual con el sitio web"""
        self.ensure_one()
        
        if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo los usuarios asociados pueden sincronizar stock.'))
        
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
        """Override para trazabilidad cuando se modifica manual_stock"""
        if 'manual_stock' in vals:
            if not self.env.user.is_asociado and not self.env.user.has_group('base.group_system'):
                raise UserError(_('Solo los usuarios asociados pueden modificar el stock manualmente.'))
        
        return super().write(vals)