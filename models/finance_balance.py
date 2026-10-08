# -*- coding: utf-8 -*-
from odoo import models, api


class FinanceBalanceAnalysis(models.AbstractModel):
    _name = 'finance.balance.analysis'
    _description = 'Análisis de Balance Financiero'

    @api.model
    def get_balance_data(self, date_from, date_to):
        """
        Calcula los totales de ventas, compras y ganancia/pérdida
        para el rango de fechas especificado, además de las series
        mensuales de ventas y compras para el gráfico lineal.
        """
        domain_base = [
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
        ]

        sales_total = self._read_amounts(domain_base, 'out_invoice')
        purchases_total = self._read_amounts(domain_base, 'in_invoice')

        profit = sales_total - purchases_total

        labels, sales_series, purchases_series = self._monthly_series(
            domain_base, date_from, date_to
        )

        return {
            'sales': sales_total,
            'purchases': purchases_total,
            'profit': profit,
            'labels': labels,
            'sales_series': sales_series,
            'purchases_series': purchases_series,
        }

    def _read_amounts(self, domain, move_type):
        """Suma del importe total de las facturas de un tipo."""
        data = self.env['account.move'].read_group(
            domain + [('move_type', '=', move_type)],
            ['amount_total'],
            [],
        )
        return data[0]['amount_total'] if data else 0.0

    def _monthly_series(self, domain_base, date_from, date_to):
        """Series mensuales de ventas y compras dentro del rango."""
        months = self._list_months(date_from, date_to)

        sales_by_month = dict(self._amounts_by_month(domain_base, 'out_invoice'))
        purchases_by_month = dict(self._amounts_by_month(domain_base, 'in_invoice'))

        sales_series = [round(sales_by_month.get(m, 0.0), 2) for m in months]
        purchases_series = [round(purchases_by_month.get(m, 0.0), 2) for m in months]
        return months, sales_series, purchases_series

    def _amounts_by_month(self, domain_base, move_type):
        """Parejas (mes 'YYYY-MM', importe) agrupadas por mes de factura."""
        rows = self.env['account.move'].read_group(
            domain_base + [('move_type', '=', move_type)],
            ['amount_total'],
            ['invoice_date:month'],
        )
        result = []
        for row in rows:
            # Odoo devuelve una etiqueta localizada en la clave del grupo
            # (ej: "octubre 2026"); la fecha real del inicio del mes
            # está disponible en __range, en formato 'YYYY-MM-DD'
            rango = (row.get('__range') or {}).get('invoice_date:month') or {}
            inicio = rango.get('from')
            if inicio:
                result.append((str(inicio)[:7], row['amount_total'] or 0.0))
        return result

    def _list_months(self, date_from, date_to):
        """Lista de meses ('YYYY-MM') que cubre el rango de fechas."""
        start_year, start_month, _ = (int(p) for p in str(date_from).split('-'))
        end_year, end_month, _ = (int(p) for p in str(date_to).split('-'))
        months = []
        year, month = start_year, start_month
        while (year, month) <= (end_year, end_month):
            months.append('%04d-%02d' % (year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1
        return months
