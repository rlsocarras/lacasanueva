# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ManualStockImportLog(models.Model):
    """Histórico persistente de cada importación de stock manual."""
    _name = 'manual.stock.import.log'
    _description = 'Historial de importación de stock manual'
    _order = 'import_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Referencia',
        store=True, readonly=True, default='/',
        help='Secuencia autogenerada (IMP/2026/0001).')
    import_date = fields.Datetime(
        string='Fecha de importación',
        default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        'res.users', string='Usuario',
        default=lambda self: self.env.user, required=True)
    file_name = fields.Char(string='Nombre del archivo')
    file_data = fields.Binary(string='Archivo')
    attachment_id = fields.Many2one(
        'ir.attachment', string='Adjunto original',
        help='Copia del archivo original guardado en el historial.')
    file_format = fields.Selection(
        [('csv', 'CSV'), ('xlsx', 'Excel')], string='Formato')
    key_field = fields.Selection(
        [('default_code', 'Referencia interna'),
         ('barcode', 'Código de barras'),
         ('name', 'Nombre'),
         ('id', 'ID técnico')],
        string='Campo clave')
    stock_field = fields.Char(string='Columna de stock', default='manual_stock')
    import_mode = fields.Selection(
        [('update', 'Solo actualizar'),
         ('update_or_create', 'Actualizar o crear')],
        string='Modo de importación')

    total_lines = fields.Integer(string='Total de líneas')
    valid_lines = fields.Integer(string='Líneas válidas')
    invalid_lines = fields.Integer(string='Líneas inválidas')
    updated_count = fields.Integer(string='Actualizadas')
    created_count = fields.Integer(string='Creadas')
    error_count = fields.Integer(string='Con error')

    state = fields.Selection(
        [('draft', 'Borrador'), ('done', 'Completado'), ('cancelled', 'Cancelado')],
        string='Estado', default='draft', required=True, tracking=True)
    notes = fields.Text(string='Observaciones')
    line_ids = fields.One2many(
        'manual.stock.import.log.line', 'log_id',
        string='Líneas', order="line_number")
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company)

    _rec_name = 'name'

    def action_download_original(self):
        """Descarga el archivo original asociado a la importación."""
        self.ensure_one()
        if not self.attachment_id:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name), ('res_id', '=', self.id),
                ('name', '=', self.file_name or ''),
            ], limit=1) or self.attachment_id
        else:
            attachment = self.attachment_id
        if not attachment:
            raise UserError(_('No se encontró el archivo original.'))
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
