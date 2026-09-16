# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    def _get_product_available_qty(self, product, **kwargs):
        """Sobrescribir para mostrar el stock manual en el sitio web"""
        # Si el producto tiene stock manual modificado, usarlo
        if product.is_manual_stock_modified:
            _logger.info(f"Usando stock manual para {product.name}: {product.manual_stock}")
            return product.manual_stock
        
        # Si no, usar el comportamiento normal de Odoo
        return super(Website, self)._get_product_available_qty(product, **kwargs)