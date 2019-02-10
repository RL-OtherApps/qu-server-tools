# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
import datetime


class AcquirerRedsys(models.Model):
    _inherit = 'payment.acquirer'

    @api.multi
    def redsys_form_generate_values(self, values):
        tx_obj = self.env['payment.transaction'].search([
            ('reference', '=', values['reference'])
            ('state', 'not in', ('refunded', 'done'))
        ])
        if tx_obj:
            now = datetime.datetime.now().strftime("%H%M%S%d%m%Y")
            reference = tx_obj.sale_order_id.name + now
            tx_obj.write({'reference': reference})
            values.update({'reference': reference})

        res = super(AcquirerRedsys, self).redsys_form_generate_values(values)
        return res
