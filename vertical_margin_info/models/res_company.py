# Copyright 2018 Qubiq <info@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_margin_text = fields.Text(
        string=_('Text on left reports margin'),
        help='Write vertical information on the left reports margin. '
        'If the text is longer than a line in the report it will be cut.'
    )
