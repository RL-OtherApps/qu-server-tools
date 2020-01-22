# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# Copyright 2019 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, Warning
from odoo.tools import ustr
import logging
_logger = logging.getLogger(__name__)
try:
    import traceback
    import xmlrpc.client
except (ImportError, IOError) as err:
    _logger.debug(err)


class Webservice(models.Model):
    _name = 'webservice.instance'
    _description = 'Webservice Instance'

    name = fields.Char(string='Name')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
    )

    webservice_active = fields.Boolean(string='Webservice active')
    ws_url = fields.Char(string='Webservice URL')
    ws_db = fields.Char(string='Webservice Database')
    ws_username = fields.Char(string='Webservice User')
    ws_password = fields.Char(string='Webservice Password')
    ws_type = fields.Selection(
        string='Connection Type',
        selection=[
            ('sql', 'SQL'),
            ('odoo', 'Odoo')
        ]
    )
    mapper_ids = fields.One2many(
        comodel_name='webservice.mapper',
        inverse_name='webservice_id',
        string='Mapper',
        copy=True,
    )

    def _get_connexion_obj(self):
        try:
            if self.ws_type == 'sql':
                return self.env['webservice.con.sqlserver']
            elif self.ws_type == 'odoo':
                return self.env['webservice.con.odoo']
        except Exception:
            return False

    def _get_access_data(self):
        return {
            'host': self.ws_url,
            'db': self.ws_db,
            'user': self.ws_username,
            'password': self.ws_password,
        }

    def _get_models_webservice(self):
        try:
            res = self._get_access_data()
            conn_obj = self._get_connexion_obj()
            if not conn_obj.check_connection(res):
                raise Warning(_("Connection was failed"))
            common = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/common'.format(res['host'])
            )
            common.version()
            uid = common.authenticate(
                res['db'], res['user'], res['password'], {}
            )
            models = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/object'.format(res['host']))
            return models, res['db'], uid, res['password']
        except UserError as err:
            _logger.debug(ustr(err))
            raise UserError(str(err))

    @api.multi
    def check_connection_webservice(self):
        try:
            self.ensure_one()
            conn_obj = self._get_connexion_obj()
            data = self._get_access_data()
            if conn_obj.check_connection(data):
                raise Warning(_("Connection was succesful"))
        except UserError as err:
            _logger.debug(ustr(err))
            raise UserError(str(err))
