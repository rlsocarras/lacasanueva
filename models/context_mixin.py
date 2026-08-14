# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplateContext(models.AbstractModel):
    _inherit = 'product.template'

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        """Sobrescribir para agregar contexto personalizado a las vistas"""
        context = dict(context or {})
        
        # Agregar flags al contexto basados en el usuario
        context['is_asociado'] = self.env.user.is_asociado or self.env.user.has_group('base.group_system')
        context['show_manual_stock'] = context['is_asociado']
        
        return super().get_view(view_id=view_id, view_type=view_type, context=context, 
                               toolbar=toolbar, submenu=submenu, **kwargs)