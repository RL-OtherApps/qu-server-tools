# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, _, api
from odoo.exceptions import Warning, ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)
try:
    import traceback
    import xmlrpc.client
    import mysql.connector
    from mysql.connector import errorcode
except (ImportError, IOError) as err:
    _logger.debug(err)


class WeberviceSQLConnector(models.AbstractModel):
    _name = 'webservice.con.sqlserver'

    @api.model
    def connect(self, params={}):
        try:
            conn = mysql.connector.connect(
                user=params.get('user', ''),
                password=params.get('password', ''),
                port=params.get('port', ''),
                host=params.get('host', ''),
                database=params.get('db', ''), connect_timeout=1000000,
            )
            cursor = conn.cursor(dictionary=True)
            return conn, cursor

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise Warning(_("User or password are incorrect"))
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                raise Warning(
                    _("Database not found")
                )
            else:
                raise Warning(err)

    def disconnect(self, conn, cursor):
        try:
            cursor.close()
            conn.close()
            return True
        except:
            raise UserError(_('Connection Close Failed'))

    @api.model
    def check_connection(self, params={}):
        try:
            conn_obj = self.env['webservice.con.sqlserver']
            conn, cursor = conn_obj.connect(params)
            if conn_obj.disconnect(conn, cursor):
                return True
            raise UserError(_("Connection Failed!"))
        except:
            raise UserError(_("Connection Failed!"))


class WeberviceOdooConnector(models.AbstractModel):
    _name = 'webservice.con.odoo'

    @api.model
    def connect(self, params={}):
        try:
            common = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/common'.format(params['host'])
            )
            common.version()
            uid = common.authenticate(
                params['db'], params['user'], params['password'], {}
            )
            models = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/object'.format(params['host']))
            return models, params['db'], uid, params['password']
        except:
            raise Warning(_("Connection with Odoo Failed"))

    def check_connection(self, params={}):
        try:
            common = xmlrpc.client.ServerProxy(
                    '{}/xmlrpc/2/common'.format(params['host'])
                )
            common.version()
            uid = common.authenticate(
                params['db'], params['user'], params['password'], {}
            )
            if uid:
                return True
            raise Warning(_("Login/password not valid!"))
        except:
            raise UserError(_("Connection failed!"))
