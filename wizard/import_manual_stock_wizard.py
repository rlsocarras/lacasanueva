# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import openpyxl  # type: ignore
    _HAS_OPENPYXL = True
except ImportError:
    _HAS_OPENPYXL = False


# Mapeo de alias (minusculas, sin acentos) -> campo destino
_KEY_ALIASES = {
    'default_code': 'default_code', 'referencia': 'default_code',
    'reference': 'default_code', 'ref': 'default_code',
    'codigo': 'default_code', 'c': 'default_code',
    'barcode': 'barcode', 'codigo_barras': 'barcode', 'ean': 'barcode',
    'name': 'name', 'nombre': 'name', 'producto': 'name',
    'id': 'id',
}
_STOCK_ALIASES = {
    'manual_stock': 'manual_stock', 'stock_manual': 'manual_stock',
    'stock': 'manual_stock', 'cantidad': 'manual_stock',
    'quantity': 'manual_stock',
}

MAX_LINES = 500


class ImportManualStockWizard(models.TransientModel):
    _name = 'import.manual.stock.wizard'
    _description = 'Asistente de importación de stock manual'

    # --- Campos de configuración ---
    file_data = fields.Binary(
        string='Archivo',
        required=True,
        help='Archivo CSV o Excel (xls/xlsx) con el stock manual a importar.')
    file_name = fields.Char(string='Nombre del archivo')
    file_format = fields.Selection(
        [('csv', 'CSV'), ('xlsx', 'Excel')],
        string='Formato',
        help='Formato del archivo a importar.')
    delimiter = fields.Char(string='Delimitador CSV', default=',')
    has_header = fields.Boolean(string='Tiene encabezado', default=True)
    key_field = fields.Selection(
        [('default_code', 'Referencia interna'),
         ('barcode', 'Código de barras'),
         ('name', 'Nombre'),
         ('id', 'ID técnico')],
        string='Campo clave', default='default_code', required=True)
    stock_field = fields.Char(string='Columna de stock', default='manual_stock')
    import_mode = fields.Selection(
        [('update', 'Solo actualizar'),
         ('update_or_create', 'Actualizar o crear')],
        string='Modo de importación', default='update', required=True)

    # --- Estado del asistente ---
    state = fields.Selection(
        [('draft', 'Archivo'), ('preview', 'Previsualización'), ('done', 'Importado')],
        string='Estado', default='draft', required=True)

    # --- Líneas de previsualización ---
    line_ids = fields.One2many(
        'import.manual.stock.wizard.line', 'wizard_id',
        string='Líneas de previsualización',
        readonly=True)

    # --- Estadísticas ---
    total_lines = fields.Integer(string='Total de líneas', readonly=True)
    valid_lines = fields.Integer(string='Válidas', readonly=True)
    invalid_lines = fields.Integer(string='Inválidas', readonly=True)
    updated_count = fields.Integer(string='Actualizadas', readonly=True)
    created_count = fields.Integer(string='Creadas', readonly=True)
    error_count = fields.Integer(string='Errores', readonly=True)

    # -------------------------------------------------------
    # Helpers de detección de formato
    # -------------------------------------------------------
    def _detect_format(self):
        """Detecta el formato del archivo a partir de la extensión."""
        fmt = self.file_format
        if fmt:
            return fmt
        name = (self.file_name or '').lower()
        if name.endswith(('.xlsx', '.xlsm', '.xltx')):
            if not _HAS_OPENPYXL:
                raise UserError(_('El módulo `openpyxl` no está disponible para leer Excel.'))
            return 'xlsx'
        if name.endswith('.csv'):
            return 'csv'
        raise UserError(_('No se pudo determinar el formato del archivo. Selecciónelo manualmente.'))

    @api.onchange('file_name')
    def _onchange_file_name(self):
        """Autocompleta el formato a partir del nombre del archivo."""
        if self.file_name and not self.file_format:
            name = self.file_name.lower()
            if name.endswith(('.xlsx', '.xlsm', '.xltx')):
                self.file_format = 'xlsx'
            elif name.endswith('.csv'):
                self.file_format = 'csv'

    @staticmethod
    def _normalize(text):
        """Normaliza un texto para el matching de alias: minúsculas y sin acentos."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ''
        import unicodedata
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        return text.strip().lower()

    def _resolve_header(self, raw_header):
        """Dada la fila/lista de encabezados, devuelve el mapeo columna->campo para clave y stock."""
        mapping = {}
        for idx, cell in enumerate(raw_header):
            norm = self._normalize(cell)
            if norm in _STOCK_ALIASES and 'stock' not in mapping:
                mapping['stock'] = idx
            elif norm in self._key_aliases() and 'key' not in mapping:
                mapping['key'] = idx
        return mapping

    def _key_aliases(self):
        return {k: v for k, v in _KEY_ALIASES.items()}

    # -------------------------------------------------------
    # Parseo
    # -------------------------------------------------------
    def _parse_rows(self):
        """Devuelve una lista de dicts con los valores raw de cada fila usando los aliases."""
        if not self.file_data:
            raise UserError(_('Debe adjuntar un archivo.'))
        fmt = self._detect_format()
        try:
            data = base64.b64decode(self.file_data)
        except Exception as exc:
            raise UserError(_('El archivo adjunto está corrupto: %s') % str(exc))

        rows = []
        if fmt == 'csv':
            encoding = 'utf-8-sig'
            try:
                text = data.decode(encoding)
            except UnicodeDecodeError:
                text = data.decode('latin-1')
            reader = csv.reader(io.StringIO(text), delimiter=self.delimiter or ',')
            rows = list(reader)
        else:
            if not _HAS_OPENPYXL:
                raise UserError(_('El módulo `openpyxl` no está disponible para leer Excel.'))
            wb = openpyxl.load_workbook(filename=io.BytesIO(data), read_only=True, data_only=True)
            ws = wb.active
            rows = [[cell.value for cell in row] for row in ws.iter_rows()]

        if not rows:
            raise UserError(_('El archivo está vacío.'))
        return rows

    def _build_lines(self):
        """Parsea el archivo y construye las líneas de previsualización."""
        self.ensure_one()
        rows = self._parse_rows()
        offset = 0
        header = None
        if self.has_header:
            header = rows[0]
            offset = 1
        else:
            header = None

        line_vals = []
        for idx, row in enumerate(rows[offset:], start=offset + 1):
            line_number = idx - offset + 1  # numeración 1..N de datos
            if not any(cell not in (None, '') for cell in row):
                continue

            if header is not None:
                self._ensure_min_len(row, len(header))
                key_value = row[self._header_index(header, 'key')] if self._header_index(header, 'key') is not None else None
                stock_raw = row[self._header_index(header, 'stock')] if self._header_index(header, 'stock') is not None else None
            else:
                # Sin encabezado: primera columna clave, segunda stock
                self._ensure_min_len(row, 2)
                key_value = row[0]
                stock_raw = row[1]

            line_vals.append(self._make_line(line_number, key_value, stock_raw))

        if len(line_vals) > MAX_LINES:
            raise UserError(_(
                'El archivo contiene %d filas con datos, superando el máximo de %d.'
            ) % (len(line_vals), MAX_LINES))

        self.line_ids = [(5, 0, 0)] + [(0, 0, lv) for lv in line_vals]
        self._recompute_stats()
        return len(line_vals)

    @staticmethod
    def _ensure_min_len(row, n):
        if len(row) < n:
            row.extend([None] * (n - len(row)))

    def _header_index(self, header, role):
        idx = self._resolve_header(header)
        return idx.get(role)

    def _make_line(self, line_number, key_value, stock_raw):
        """Construye el dict de una línea de previsualización."""
        status = 'error'
        notes = ''
        product = None
        new_stock = None
        current_stock = 0.0

        if key_value is None or str(key_value).strip() == '':
            status = 'error'
            notes = 'Referencia vacía'
            return self._line_dict(line_number, '', None, current_stock, None, status, notes)

        key_value = str(key_value).strip()

        # Validar stock
        new_stock, notes = self._parse_stock(stock_raw)
        if new_stock is None:
            status = 'error'
            return self._line_dict(line_number, key_value, None, current_stock, None, status, notes)

        if new_stock < 0:
            status = 'error'
            notes = 'El stock no puede ser negativo'
            return self._line_dict(line_number, key_value, None, current_stock, None, status, notes)

        # Buscar producto según key_field
        product = self._find_product(key_value)
        if not product:
            status = 'not_found'
            return self._line_dict(line_number, key_value, None, 0.0, new_stock, status,
                                   'Producto no encontrado')
        current_stock = product.manual_stock
        status = 'valid'
        return self._line_dict(line_number, key_value, product, current_stock, new_stock, status, '')

    def _parse_stock(self, raw):
        """Parsea el valor de stock a float aceptando coma decimal y separadores de miles."""
        if raw is None or str(raw).strip() == '':
            return None, 'Valor de stock vacío'
        text = str(raw).strip()
        # Normalizar coma decimal: si tiene coma y punto, asumir "1.234,56" -> 1234.56
        if ',' in text and '.' in text:
            text = text.replace('.', '').replace(',', '.')
        elif ',' in text:
            text = text.replace(',', '.')
        try:
            value = float(text)
        except (ValueError, TypeError):
            return None, 'El stock "%s" no es un número válido' % raw
        return value, ''

    def _find_product(self, key_value):
        """Busca el producto según el campo clave configurado."""
        Product = self.env['product.product']
        if self.key_field == 'id':
            try:
                pid = int(float(key_value))
            except (ValueError, TypeError):
                return None
            return Product.browse(pid).exists()
        if self.key_field == 'default_code':
            # Buscar por referencia interna tanto en la variante
            # como en la plantilla (variantes que heredan el código del template).
            return Product.search(
                ['|', ('default_code', '=', key_value),
                 ('product_tmpl_id.default_code', '=', key_value)],
                limit=1)
        if self.key_field == 'barcode':
            return Product.search([('barcode', '=', key_value)], limit=1)
        if self.key_field == 'name':
            return Product.search([('name', '=', key_value)], limit=1)
        return None

    @staticmethod
    def _line_dict(line_number, key_value, product, current_stock, new_stock, status, notes):
        return {
            'line_number': line_number,
            'key_value': key_value,
            'product_id': product.id if product else None,
            'current_stock': current_stock or 0.0,
            'new_stock': new_stock if new_stock is not None else 0.0,
            'status': status,
            'notes': notes,
        }

    def _recompute_stats(self):
        self.ensure_one()
        lines = self.line_ids
        self.total_lines = len(lines)
        self.valid_lines = len(lines.filtered(lambda l: l.status == 'valid'))
        self.invalid_lines = len(lines.filtered(lambda l: l.status in ('not_found', 'error')))
        self.error_count = len(lines.filtered(lambda l: l.status == 'error'))
        self.updated_count = 0
        self.created_count = 0

    # -------------------------------------------------------
    # Acciones del wizard
    # -------------------------------------------------------
    def action_preview(self):
        """Parsea el archivo y muestra las líneas de previsualización."""
        self.ensure_one()
        self._check_permission()
        if not self.file_data:
            raise UserError(_('Debe adjuntar un archivo.'))
        count = self._build_lines()
        if self.total_lines == 0:
            raise UserError(_('El archivo no contiene filas con datos.'))
        self.state = 'preview'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Importar stock manual'),
            'res_model': self._name,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': self.id,
            'target': 'new',
        }

    def action_import(self):
        """Aplica los cambios marcados como válidos y crea el histórico."""
        self.ensure_one()
        self._check_permission()
        if self.state != 'preview':
            raise UserError(_('Primero debe previsualizar el archivo.'))
        if not self.line_ids.filtered(lambda l: l.status == 'valid'):
            raise UserError(_('No hay líneas válidas para importar.'))

        lines_to_apply = self.line_ids.filtered(lambda l: l.status == 'valid')

        log = self.env['manual.stock.import.log'].create(self._log_vals())
        log_line_vals = []
        updated = 0
        created = 0

        for line in lines_to_apply:
            current = line.product_id.manual_stock
            vals = {'manual_stock': line.new_stock}
            # Se marca la trazabilidad (is_manual_stock_modified/last_*) vía el modelo product.product
            line.product_id.write(vals)
            updated += 1
            log_line_vals.append({
                'log_id': log.id,
                'line_number': line.line_number,
                'key_value': line.key_value,
                'product_id': line.product_id.id,
                'current_stock': current,
                'new_stock': line.new_stock,
                'status': 'applied',
                'applied': True,
            })

        # Líneas no válidas pasan al histórico para auditoría
        for line in self.line_ids.filtered(lambda l: l.status != 'valid'):
            log_line_vals.append({
                'log_id': log.id,
                'line_number': line.line_number,
                'key_value': line.key_value,
                'product_id': line.product_id.id,
                'current_stock': line.current_stock,
                'new_stock': line.new_stock,
                'status': line.status,
                'applied': False,
                'notes': line.notes,
            })

        self.env['manual.stock.import.log.line'].create(log_line_vals)

        log.write({
            'updated_count': updated,
            'created_count': created,
            'error_count': len(self.line_ids) - len(lines_to_apply),
            'valid_lines': len(lines_to_apply),
            'invalid_lines': len(self.line_ids) - len(lines_to_apply),
            'total_lines': len(self.line_ids),
            'state': 'done',
        })
        self.updated_count = updated
        self.created_count = created
        self._recompute_stats()
        self.state = 'done'

        log.invalidate()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Detalle de importación'),
            'res_model': 'manual.stock.import.log',
            'view_mode': 'form',
            'views': [(log.id, 'form')],
            'res_id': log.id,
            'target': 'current',
        }

    def action_reset(self):
        """Reinicia el asistente para cargar un nuevo archivo."""
        self.ensure_one()
        self.line_ids = [(5, 0, 0)]
        self.file_data = False
        self.file_name = False
        self.file_format = False
        self.delimiter = ','
        self.has_header = True
        self.key_field = 'default_code'
        self.stock_field = 'manual_stock'
        self.import_mode = 'update'
        self.state = 'draft'
        self.total_lines = self.valid_lines = self.invalid_lines = 0
        self.updated_count = self.created_count = self.error_count = 0
        return {
            'type': 'ir.actions.act_window',
            'name': _('Importar stock manual'),
            'res_model': self._name,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': self.id,
            'target': 'new',
        }

    def action_download_template(self):
        """Genera y descarga un archivo CSV de ejemplo."""
        self.ensure_one()
        import io as _io
        out = _io.StringIO()
        w = csv.writer(out)
        w.writerow(['default_code', 'manual_stock'])
        w.writerow(['REF-001', '10'])
        w.writerow(['REF-002', '5'])
        w.writerow(['REF-003', '0'])
        content = out.getvalue().encode('utf-8')
        attach = self.env['ir.attachment'].create({
            'name': 'import_stock_manual_template.csv',
            'datas': base64.b64encode(content),
            'type': 'binary',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attach.id}?download=true',
            'target': 'new',
        }

    # -------------------------------------------------------
    # Seguridad y valores del histórico
    # -------------------------------------------------------
    @api.model
    def _check_permission(self):
        """Valida que el usuario tenga el permiso de gestionar stock manual."""
        if not self.env.user.has_group('lacasanueva.group_gestionar_stock_manual'):
            raise UserError(_('Solo los usuarios con permiso "Gestionar stock manual" pueden importar.'))

    def _log_vals(self):
        attach = self.env['ir.attachment'].create({
            'name': self.file_name or 'import_manual_stock.csv',
            'datas': self.file_data,
            'type': 'binary',
            'res_model': 'manual.stock.import.log',
            'res_id': self.id,
        }) if self.file_data else None
        seq = self.env.ref('lacasanueva.ir_sequence_manual_stock_import', raise_if_not_found=False)
        name = self.env['ir.sequence'].next_by_code('manual.stock.import') or '/'
        return {
            'name': name,
            'import_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'file_name': self.file_name,
            'file_data': self.file_data,
            'file_format': self.file_format,
            'key_field': self.key_field,
            'stock_field': self.stock_field,
            'import_mode': self.import_mode,
            'total_lines': self.total_lines,
            'valid_lines': self.valid_lines,
            'invalid_lines': self.invalid_lines,
            'updated_count': 0,
            'created_count': 0,
            'error_count': self.error_count,
            'state': 'draft',
            'company_id': self.env.company.id,
            'attachment_id': attach.id if attach else None,
        }
