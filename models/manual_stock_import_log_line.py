# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ManualStockImportLogLine(models.Model):
    """Línea individual del histórico de importación de stock manual."""
    _name = 'manual.stock.import.log.line'
    _description = 'Línea de histórico de importación de stock manual'
    _order = 'log_id, line_number'

    log_id = fields.Many2one(
        'manual.stock.import.log', string='Histórico',
        required=True, ondelete='cascade', index=True)
    line_number = fields.Integer(string='Línea #')
    key_value = fields.Char(string='Referencia')
    product_id = fields.Many2one('product.product', string='Producto')
    current_stock = fields.Float(string='Stock actual')
    new_stock = fields.Float(string='Stock nuevo')
    difference = fields.Float(
        string='Diferencia',
        compute='_compute_difference', store=True)
    status = fields.Selection(
        [('valid', 'Válida'),
         ('not_found', 'No encontrada'),
         ('error', 'Error'),
         ('applied', 'Aplicada')],
        string='Estado', required=True)
    notes = fields.Char(string='Notas')
    applied = fields.Boolean(string='Aplicada', default=False)

    @api.depends('current_stock', 'new_stock')
    def _compute_difference(self):
        """Calcula la diferencia entre stock nuevo y actual."""
        for rec in self:
            rec.difference = (rec.new_stock or 0.0) - (rec.current_stock or 0.0)
