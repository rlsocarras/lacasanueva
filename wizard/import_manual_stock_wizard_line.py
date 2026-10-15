# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ImportManualStockWizardLine(models.TransientModel):
    _name = 'import.manual.stock.wizard.line'
    _description = 'Línea de previsualización de importación de stock manual'

    wizard_id = fields.Many2one(
        'import.manual.stock.wizard', string='Asistente',
        ondelete='cascade', index=True)
    line_number = fields.Integer(string='Línea #')
    key_value = fields.Char(string='Referencia')
    product_id = fields.Many2one('product.product', string='Producto')
    current_stock = fields.Float(string='Stock actual')
    new_stock = fields.Float(string='Stock nuevo')
    difference = fields.Float(
        string='Diferencia',
        compute='_compute_difference', store=False)
    status = fields.Selection(
        [('valid', 'Válida'),
         ('not_found', 'No encontrada'),
         ('error', 'Error')],
        string='Estado')
    notes = fields.Char(string='Notas')

    @api.depends('current_stock', 'new_stock')
    def _compute_difference(self):
        """Calcula la diferencia entre el stock nuevo y el actual."""
        for rec in self:
            rec.difference = (rec.new_stock or 0.0) - (rec.current_stock or 0.0)
