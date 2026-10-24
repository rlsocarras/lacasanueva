# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_asociado = fields.Boolean(
        string='Es Asociado',
        help='Marcar si el usuario es un asociado con permisos especiales para modificar stock manualmente',
        default=False,
        tracking=True,
    )

    gestionar_stock_manual = fields.Boolean(
        string='Gestionar stock manual',
        help='Permite gestionar el stock manual de los productos',
        default=False,
        tracking=True,
    )

    LACASANUEVA_GROUP = 'lacasanueva.group_gestionar_stock_manual'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_lacasanueva_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'is_asociado' in vals or 'gestionar_stock_manual' in vals:
            self._sync_lacasanueva_group()
        return res

    def _sync_lacasanueva_group(self):
        group = self.env.ref(self.LACASANUEVA_GROUP, raise_if_not_found=False)
        if not group:
            return
        for user in self:
            if user.gestionar_stock_manual and group not in user.groups_id:
                user.groups_id = [(4, group.id)]
            elif not user.gestionar_stock_manual and group in user.groups_id:
                user.groups_id = [(3, group.id)]

    @api.constrains('is_asociado')
    def _check_is_asociado(self):
        """Validación para asegurar que solo administradores pueden marcar asociados"""
        for user in self:
            if user.is_asociado and not self.env.user.has_group('base.group_system'):
                raise ValidationError('Solo los administradores pueden marcar usuarios como asociados')