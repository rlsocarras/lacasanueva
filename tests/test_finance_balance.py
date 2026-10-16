# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

# Los tests usan el año 2099 para aislarse de las facturas
# preexistentes en la base de datos (rango sin facturación real).
ANIO_PRUEBAS = 2099


class TestFinanceBalanceAnalysis(TransactionCase):
    """Pruebas de los datos que alimentan los gráficos del dashboard."""

    # Contador para números de documento únicos (formato UY: 2 letras + 7 dígitos)
    _doc_counter = 0

    def setUp(self):
        super().setUp()
        self.partner_venta = self.env['res.partner'].create({
            'name': 'Cliente de prueba La Casa Nueva',
        })
        self.partner_compra = self.env['res.partner'].create({
            'name': 'Proveedor de prueba La Casa Nueva',
        })
        self.account_ingreso = self._buscar_o_crear_cuenta('income', 'LCN.ING')
        self.account_gasto = self._buscar_o_crear_cuenta('expense', 'LCN.GAS')
        self.analysis = self.env['finance.balance.analysis']

    def _buscar_o_crear_cuenta(self, account_type, code):
        """Busca una cuenta del tipo indicado o la crea (BDs sin plan de cuentas)."""
        cuenta = self.env['account.account'].search(
            [('account_type', '=', account_type),
             ('company_ids', 'in', [self.env.company.id])],
            limit=1,
        )
        if not cuenta:
            cuenta = self.env['account.account'].create({
                'name': f'Cuenta de prueba ({account_type})',
                'code': code,
                'account_type': account_type,
            })
        return cuenta

    def _crear_factura(self, move_type, partner, fecha, importe, post=True):
        """Crea (y opcionalmente publica) una factura con una línea de importe dado."""
        # La localización UY exige número de documento para publicar facturas
        type(self)._doc_counter += 1
        numero_doc = 'PR%07d' % type(self)._doc_counter
        factura = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_date': fecha,
            'l10n_latam_document_number': numero_doc,
            'invoice_line_ids': [(0, 0, {
                'name': 'Línea de prueba',
                'account_id': (
                    self.account_ingreso.id if move_type == 'out_invoice'
                    else self.account_gasto.id
                ),
                'price_unit': importe,
                'quantity': 1,
            })],
        })
        if post:
            factura.action_post()
        return factura

    # ------------------------------------------------------------------
    # Totales (gráfico de barras)
    # ------------------------------------------------------------------

    def test_totales_ventas_compras_ganancia(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-10', 1000.0)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-20', 500.0)
        self._crear_factura('in_invoice', self.partner_compra, f'{ANIO_PRUEBAS}-08-15', 400.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-08-01', f'{ANIO_PRUEBAS}-08-31')

        self.assertAlmostEqual(resultado['sales'], 1500.0)
        self.assertAlmostEqual(resultado['purchases'], 400.0)
        self.assertAlmostEqual(resultado['profit'], 1100.0)

    def test_solo_se_cuentan_facturas_publicadas(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-10', 900.0, post=False)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-12', 300.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-08-01', f'{ANIO_PRUEBAS}-08-31')

        self.assertAlmostEqual(resultado['sales'], 300.0)
        self.assertEqual(resultado['sales_series'], [300.0])

    def test_rango_de_fechas_limita_los_resultados(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-07-31', 100.0)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-01', 200.0)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-31', 300.0)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-09-01', 400.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-08-01', f'{ANIO_PRUEBAS}-08-31')

        self.assertAlmostEqual(resultado['sales'], 500.0)
        self.assertEqual(resultado['labels'], [f'{ANIO_PRUEBAS}-08'])
        self.assertEqual(resultado['sales_series'], [500.0])

    # ------------------------------------------------------------------
    # Series mensuales (gráfico lineal)
    # ------------------------------------------------------------------

    def test_serie_mensual_con_varios_meses(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-07-05', 300.0)
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-08-12', 700.0)
        self._crear_factura('in_invoice', self.partner_compra, f'{ANIO_PRUEBAS}-08-25', 200.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-07-01', f'{ANIO_PRUEBAS}-09-30')

        self.assertEqual(resultado['labels'], [f'{ANIO_PRUEBAS}-07', f'{ANIO_PRUEBAS}-08', f'{ANIO_PRUEBAS}-09'])
        self.assertEqual(resultado['sales_series'], [300.0, 700.0, 0.0])
        self.assertEqual(resultado['purchases_series'], [0.0, 200.0, 0.0])

    def test_meses_sin_facturas_se_rellenan_con_cero(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-01-10', 100.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-01-01', f'{ANIO_PRUEBAS}-03-31')

        self.assertEqual(resultado['labels'], [f'{ANIO_PRUEBAS}-01', f'{ANIO_PRUEBAS}-02', f'{ANIO_PRUEBAS}-03'])
        self.assertEqual(resultado['sales_series'], [100.0, 0.0, 0.0])
        self.assertEqual(resultado['purchases_series'], [0.0, 0.0, 0.0])

    def test_serie_vacia_sin_facturas(self):
        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-08-01', f'{ANIO_PRUEBAS}-08-31')

        self.assertEqual(resultado['labels'], [f'{ANIO_PRUEBAS}-08'])
        self.assertEqual(resultado['sales_series'], [0.0])
        self.assertEqual(resultado['purchases_series'], [0.0])
        self.assertAlmostEqual(resultado['profit'], 0.0)

    def test_etiquetas_y_series_tienen_la_misma_longitud(self):
        self._crear_factura('out_invoice', self.partner_venta, f'{ANIO_PRUEBAS}-05-01', 50.0)
        self._crear_factura('in_invoice', self.partner_compra, f'{ANIO_PRUEBAS}-06-15', 25.0)

        resultado = self.analysis.get_balance_data(f'{ANIO_PRUEBAS}-05-01', f'{ANIO_PRUEBAS}-06-30')

        self.assertEqual(len(resultado['labels']), len(resultado['sales_series']))
        self.assertEqual(len(resultado['labels']), len(resultado['purchases_series']))
