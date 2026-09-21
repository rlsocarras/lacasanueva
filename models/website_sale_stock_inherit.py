# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    def _get_product_available_qty(self, product, **kwargs):
        """
        Devuelve el stock manual SOLO si:
        - stock_display_mode == 'manual'
        - is_manual_stock_modified == True
        """
        if not product:
            return super()._get_product_available_qty(product, **kwargs)
        
        if (product.stock_display_mode == 'manual' and 
            product.is_manual_stock_modified):
            _logger.info(f"[LCN] Usando stock manual para {product.name}: {product.manual_stock}")
            return product.manual_stock
        
        return super()._get_product_available_qty(product, **kwargs)

    # ❌ ELIMINADO: _get_product_stock_availability
    # ❌ ELIMINADO: _get_manual_stock_availability_data