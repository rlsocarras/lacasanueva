# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    def _get_product_available_qty(self, product, **kwargs):
        if product and product.is_manual_stock_modified:
            return product.manual_stock
        return super()._get_product_available_qty(product, **kwargs)

    def _get_product_stock_availability(self, product, **kwargs):
        if product and product.is_manual_stock_modified:
            return self._get_manual_stock_availability_data(product)
        return super()._get_product_stock_availability(product, **kwargs)

    def _get_manual_stock_availability_data(self, product):
        manual_stock = product.manual_stock
        threshold = self.stock_threshold if hasattr(self, 'stock_threshold') else 0
        
        if manual_stock <= 0:
            availability = 'out_of_stock'
            message = _('Sin stock disponible.')
        elif threshold and manual_stock <= threshold:
            availability = 'threshold'
            message = _('Solo %s Unidades disponibles.') % int(manual_stock)
        else:
            availability = 'in_stock'
            message = _('%s Unidades disponibles.') % int(manual_stock)
        
        return {
            'product': product,
            'availability': availability,
            'message': message,
            'quantity': manual_stock,
            'threshold': threshold,
            'is_manual': True,
        }