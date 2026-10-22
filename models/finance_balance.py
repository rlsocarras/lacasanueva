# -*- coding: utf-8 -*-
from odoo import models, api


class FinanceBalanceAnalysis(models.AbstractModel):
    _name = 'finance.balance.analysis'
    _description = 'Análisis de Balance Financiero'

    @api.model
    def get_balance_data(self, date_from, date_to):
        sales_domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', 'not in', ['draft', 'cancel', 'sent']),
        ]
        purchases_domain = [
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', 'not in', ['draft', 'cancel', 'sent']),
        ]

        sales_total = self._read_order_amounts('sale.report', sales_domain, amount_field='price_subtotal', date_field='date')
        purchases_total = self._read_order_amounts('purchase.report', purchases_domain, amount_field='untaxed_total', date_field='date_order')

        profit = sales_total - purchases_total

        labels, sales_series, purchases_series = self._monthly_series(
            sales_domain, purchases_domain, date_from, date_to
        )

        return {
            'sales': sales_total,
            'purchases': purchases_total,
            'profit': profit,
            'labels': labels,
            'sales_series': sales_series,
            'purchases_series': purchases_series,
        }

    def _read_amounts(self, domain, move_types):
        data = self.env['account.move'].read_group(
            domain + [('move_type', 'in', move_types)],
            ['amount_untaxed'],
            [],
        )
        return data[0]['amount_untaxed'] if data else 0.0

    def _read_order_amounts(self, model, domain, amount_field='price_subtotal', date_field='date'):
        data = self.env[model].read_group(
            domain,
            [amount_field],
            [],
        )
        return data[0][amount_field] if data else 0.0

    def _monthly_series(self, sales_domain, purchases_domain, date_from, date_to):
        months = self._list_months(date_from, date_to)

        sales_by_month = dict(self._order_amounts_by_month('sale.report', sales_domain, amount_field='price_subtotal', date_field='date'))
        purchases_by_month = dict(self._order_amounts_by_month('purchase.report', purchases_domain, amount_field='untaxed_total', date_field='date_order'))

        sales_series = [round(sales_by_month.get(m, 0.0), 2) for m in months]
        purchases_series = [round(purchases_by_month.get(m, 0.0), 2) for m in months]
        return months, sales_series, purchases_series

    def _amounts_by_month(self, domain_base, move_types):
        rows = self.env['account.move'].read_group(
            domain_base + [('move_type', 'in', move_types)],
            ['amount_untaxed'],
            ['invoice_date:month'],
        )
        result = []
        for row in rows:
            rango = (row.get('__range') or {}).get('invoice_date:month') or {}
            inicio = rango.get('from')
            if inicio:
                result.append((str(inicio)[:7], row['amount_untaxed'] or 0.0))
        return result

    def _order_amounts_by_month(self, model, domain, amount_field='price_subtotal', date_field='date'):
        rows = self.env[model].read_group(
            domain,
            [amount_field],
            ['%s:month' % date_field],
        )
        result = []
        for row in rows:
            rango = (row.get('__range') or {}).get('%s:month' % date_field) or {}
            inicio = rango.get('from')
            if inicio:
                result.append((str(inicio)[:7], row[amount_field] or 0.0))
        return result

    def _list_months(self, date_from, date_to):
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
