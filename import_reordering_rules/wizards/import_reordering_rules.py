# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportReorderingRules(models.TransientModel):
    _name = 'import.reordering.rules'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=',',
        help='Default delimiter ","',
    )

    '''
        Function to create the reordering rules.

        :param values: Dict with the values to import.
    '''
    def _create_new_reordering_rules(self, values):
        product_obj = self.env['product.product'].search([(
            'default_code', '=', values['product'])])
        del values['product']

        if product_obj:
            values.update({
                'product_id': product_obj.id,
            })

            reorder_rule_obj = self.env['stock.warehouse.orderpoint'].search([(
                'product_id', '=', product_obj.id)])
            if reorder_rule_obj:
                del values['product_id']
                reorder_rule_obj.write(values)
                _logger.info(
                    "Changing qtys for reordering rule: %s",
                    reorder_rule_obj.name
                )
            else:
                reorder_rule_obj = reorder_rule_obj.create(values)
                _logger.info(
                    "Creating reordering rule: %s", reorder_rule_obj.name)

    '''
        Function to read the csv file and convert it to a dict.

        :return Dict with the columns and its value.
    '''
    def action_import(self):
        """Load Inventory data from the CSV file."""
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data).decode('utf-8')
        file_input = StringIO(data)
        file_input.seek(0)

        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]

        # Get column names
        keys_init = reader_info[0]
        keys = []
        for k in keys_init:
            temp = k.replace(' ', '_')
            keys.append(temp)

        del reader_info[0]
        values = {}

        for i in range(len(reader_info)):
            # Don't read rows that start with ( , ' ' or are empty
            if not (reader_info[i][0] is '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                self._create_new_reordering_rules(values)

        return {'type': 'ir.actions.act_window_close'}
