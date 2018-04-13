# -*- coding: utf-8 -*-
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, api
from . import iban
import logging
_logger = logging.getLogger(__name__)


class ResPartnerBankConfirm(models.TransientModel):
    _name = 'res.partner.bank.confirm'

    """
    Proceso que gracias al archivo iban.py transforma los ccc en iban.
    Tiene en cuenta que todos los paises son ES.
    https://www.lawebdelprogramador.com/codigo/Python/3276-Calculo-del-IBAN.html
    """
    @api.multi
    def calculo_iban_proceso(self):
        _logger.info("")
        _logger.info("------>Inicio del proceso de conversion de CCC a Iban")
        _logger.info("")
        for company in self.env['res.company'].search([]):
            for bank in self.env['res.partner.bank'].search([
                ('company_id', '=', company.id),
                ('acc_type', '=', 'bank')
                    ]):
                _logger.info("Cuenta actual:")
                _logger.info(bank.acc_number)
                _logger.info("Iniciando proceso de conversion..")
                number = bank.acc_number
                if number[:2] in ('ES', 'es'):
                    number = number[2:]
                iban_number = iban.convertir(number)
                if ('Error') not in iban_number:
                    bank.acc_number = iban_number
                    _logger.info("Nueva cuenta:")
                    _logger.info(iban_number)
                else:
                    _logger.info(iban_number)
                _logger.info("")

        _logger.info("------>Finalizacion del proceso de conversion de CCC a Iban")
        _logger.info("")
