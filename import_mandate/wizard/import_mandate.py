# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportMandate(models.TransientModel):
    _name = 'import.mandate'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default=',',
                            help='Default delimiter ","')
    mandate_file = fields.Binary('Mandate file', required=True)

    '''
        Function to create the mandate.

        :param values: Dict with the values to import.
    '''
    def _create_new_mandate(self, values):
        mandate_obj = self.env['account.banking.mandate']
        partner_obj = self.env['res.partner'].search([(
            'unique_code', '=', values['partner'])])
        if partner_obj:
            mandate_obj.search([
                ('unique_mandate_reference', '=', values['mandate']),
                ('partner_id', '=', partner_obj.id)])
            if not mandate_obj:
                if values['signature_date'] > values['last_debit_date']:
                    values['last_debit_date'] = False

                mandate_values = {
                    'unique_mandate_reference': values['mandate'],
                    'format': 'sepa',
                    'type': 'recurrent',
                    'recurrent_sequence_type': 'recurring',
                    'scheme': 'CORE',
                    'partner_id': partner_obj.id,
                    'state': 'draft',
                    'scan': self.mandate_file,
                    'signature_date': values['signature_date'],
                    'last_debit_date': values['last_debit_date'],
                }

                if partner_obj.bank_ids:
                    mandate_values.update({
                        'partner_bank_id': partner_obj.bank_ids[0].id,
                    })

                mandate_obj = mandate_obj.create(mandate_values)
                mandate_obj.validate()

                _logger.info(
                    "Creating mandate for partner: %s",
                    partner_obj.sequence_number
                )
            else:
                _logger.info("Mandate %s already created", values['mandate'])
        else:
            _logger.info("Partner %s not found", values['partner'])

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
            # Don't read rows that start with ( or are empty
            if not (reader_info[i][0] is '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                self._create_new_mandate(values)

        return {'type': 'ir.actions.act_window_close'}
