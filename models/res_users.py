# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_asociado = fields.Boolean(
        string='Es Asociado',
        help='Marcar si el usuario es un asociado con permisos especiales para modificar stock manualmente',
        default=False,
        tracking=True,
    )

    @api.constrains('is_asociado')
    def _check_is_asociado(self):
        """Validación para asegurar que solo administradores pueden marcar asociados"""
        for user in self:
            if user.is_asociado and not self.env.user.has_group('base.group_system'):
                raise ValidationError('Solo los administradores pueden marcar usuarios como asociados')