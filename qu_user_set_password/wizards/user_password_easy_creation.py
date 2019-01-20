# Copyright 2019 Marçal Isern - QubiQ 2010 <marsal.isern@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import  fields, models

class UserPasswordWiz(models.TransientModel):
    _name = 'user.password.wiz'

    name = fields.Char(
        string="New Password",
        required=True,
    )

    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users allowed',
        domain=[('share', '=', False)],
    )

    def action_accept(self):
        if not self.user_ids:
            self.user_ids = self.env['res.users'].search([])

        users = self.user_ids.filtered(
            lambda a: a.id != 1)
        users.write({'password': self.name})
