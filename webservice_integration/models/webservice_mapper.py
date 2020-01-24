# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job
from odoo.tools import pycompat
from odoo.exceptions import ValidationError, UserError
import io
import random
import base64
import logging
_logger = logging.getLogger(__name__)


class WebserviceMapper(models.Model):
    _name = 'webservice.mapper'
    _description = 'Webservice Mapper'

    name = fields.Char(required=1)
    active = fields.Boolean()
    webservice_id = fields.Many2one(
        comodel_name='webservice.instance',
        string='Webservice',
    )
    ref_code = fields.Char(index=True, copy=False)
    sync_ids = fields.Char(string="Sync IDS",
                           help="select specific id or [ids] for sync")
    dep_field_ids = fields.One2many(comodel_name='webservice.mapper.fields',
                                    inverse_name='dependence_id')
    dep_mapper_id = fields.Many2one(
        comodel_name='webservice.mapper',
        related='dep_field_ids.webservice_mapper_id')
    source_model = fields.Char(
        help="Table name or model name if the source is odoo", required=1)
    odoo_model = fields.Many2one(
        comodel_name='ir.model',
        help="Table name or model name if the source is odoo",
        required=True)
    odoo_model_name = fields.Char(related='odoo_model.model')
    mapper_fields_ids = fields.One2many(
        comodel_name='webservice.mapper.fields',
        inverse_name='webservice_mapper_id',
        string='Mapper Fields',
        copy=True)
    search_field = fields.Char(help="""Fields used for search and use records
        in the current odoo database""")
    company_field = fields.Char(help="Column name for company_id",
                                compute="_compute_company_field",
                                store=True,
                                readonly=False)
    search_domain = fields.Char(help="""Domain used for search and use records
        in the source odoo database""")
    priority = fields.Integer(help="""Number between 0-99 to
                set the order of execute""")
    method_calls = fields.Text(
        help="""Separate with ; the list of the method to use
         after create the object""")
    update = fields.Boolean(
        help="""When is activated the record will be overwrite
         in case that it already exist""",
        default=True)
    create_active = fields.Boolean(
        help="When is activated the record will be created", default=True)
    hide_create_unique_field = fields.Boolean()

    result = fields.Text(string='')

    def get_ref_code(self):
        """Write a unique ref code """
        if not self.ref_code:
            num_2 = random.randint(10, 99)
            num = random.randint(100000, 999999)
            ref_code = '%s_%s_%s' % (self.odoo_model_name, num_2, num)
            self.write({'ref_code': ref_code})
        return self.ref_code

    def export_mappers(self):
        export_wiz = self.env['export.webservice.mapper'].create({})
        export_files = self.env['export.webservice.file']
        for rec in self:
            file_data, file_name = rec.get_export_data()
            export_wiz.file_ids += export_files.create({
                'file_name': file_name,
                'file_data': file_data,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export Mappers',
            'res_model': 'export.webservice.mapper',
            'res_id': export_wiz.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def get_export_data(self):
        fp = io.BytesIO()
        exporter = self.env['export.webservice.mapper']
        writter = pycompat.csv_writer(fp, quoting=1)
        writter.writerow(exporter._columns_mapper)
        writter.writerow(self.get_export_mapper_data())
        writter.writerow(exporter._columns_fields)
        for field in self.mapper_fields_ids:
            writter.writerow(field.get_export_field_data())
        return base64.encodestring(fp.getvalue()), self.name + '.csv'

    def format_get_dep_fields(self):
        vals = [
            x.get_ref_code()
            for x in self.dep_field_ids.mapped('webservice_mapper_id')
        ]
        return '/'.join(vals)

    def get_export_mapper_data(self):
        return [
            self.get_ref_code(),
            self.format_get_dep_fields(),
            self.name,
            self.active,
            self.odoo_model_name or "",
            self.source_model or "",
            self.search_field or "",
            self.search_domain or "",
            self.priority or "",
            self.method_calls or "",
            self.update,
            self.create_active,
            self.hide_create_unique_field,
        ]

    def get_company_domain(self):
        if self.company_field:
            return [(self.company_field, "=", self.webservice_id.company_id.id)
                    ]
        return []

    @api.depends('odoo_model')
    def _compute_company_field(self):
        for rec in self:
            if rec.odoo_model.field_id.filtered(
                    lambda o: o.name == 'company_id'):
                rec.company_field = "company_id"
            else:
                rec.company_field = ""

    @api.onchange('odoo_model_name')
    def _onchange_odoo_model_name(self):
        if self.odoo_model_name:
            self.source_model = self.odoo_model_name
        else:
            self.source_model = ''

    def create_unique_field(self):
        self.ensure_one()
        field_obj = self.env['ir.model.fields']
        field_obj = field_obj.search([
            ('name', '=', 'x_old_id'),
            ('model_id', '=', self.odoo_model.id),
        ])
        if not field_obj:
            field_obj = field_obj.sudo().create({
                'name': 'x_old_id',
                'field_description': 'Old ID',
                'model': self.odoo_model_name,
                'model_id': self.odoo_model.id,
                'ttype': 'integer',
                'store': True,
                'index': True,
                'state': 'manual'
            })
        map_field_obj = self.env['webservice.mapper.fields']
        if not map_field_obj.search([
            ('webservice_mapper_id', '=', self.id),
            ('odoo_field', '=', field_obj.id),
        ]):
            map_field_obj.create({
                'odoo_field': field_obj.id,
                'webservice_mapper_id': self.id,
                'source_field': 'id',
                'unique': True,
                'state_valid': 'valid'
            })
        self.hide_create_unique_field = True

    def _get_fields(self):
        self.ensure_one()
        models, db, uid, password = self.webservice_id.\
            _get_models_webservice()
        field_list = models.execute_kw(db, uid, password, self.source_model,
                                       'fields_get', [],
                                       {'attributes': ['type']})
        return field_list

    def _check_mapped_fields(self, field_list):
        all_valid = True
        unique_fields = self._get_unique_fields()
        for mapped_field in self.mapper_fields_ids:
            if mapped_field.source_field in field_list:
                mapped_field.state_valid = 'valid'
            elif (not mapped_field.source_field
                  and mapped_field.odoo_field.name in field_list):
                mapped_field.write({
                    'state_valid':
                    'valid',
                    'source_field':
                    mapped_field.odoo_field.name,
                })
            elif (mapped_field.odoo_field.name[-3:] == '_id'
                  and mapped_field.odoo_field.name[:-3] in field_list):
                mapped_field.write({
                    'state_valid':
                    'valid',
                    'source_field':
                    mapped_field.odoo_field.name[:-3],
                })
            else:
                mapped_field.state_valid = 'not_valid'
                all_valid = False
            if mapped_field.odoo_field.name in unique_fields:
                mapped_field.unique = True
        return all_valid

    def _get_unique_fields(self):
        model_obj = self.env[self.odoo_model_name]
        unique_fields = ['id', 'x_old_id']
        for cons in model_obj._sql_constraints:
            if 'uniq' in cons[0]:
                try:
                    unique_fields.append(cons[0].split('_')[0])
                except Exception:
                    pass
        return unique_fields

    def check_mapped_fields(self):
        self.ensure_one()
        field_list = self._get_fields()
        return self._check_mapped_fields(field_list.keys())

    def create_dependences(self):
        for rec in self:
            dep_list = rec.mapper_fields_ids.create_dependence()
            for dep in dep_list:
                dep.fill_required_fields()

    def fill_required_fields(self):
        for rec in self:
            if not rec.odoo_model:
                raise UserError(_('You must select a Odoo Model'))
            current_fields = rec.mapper_fields_ids.mapped('odoo_field').mapped(
                'name')
            required_fields = rec.odoo_model.field_id.filtered(
                lambda f: f.required and 'company_id' not in f.name)
            mapper_field_obj = self.env['webservice.mapper.fields']
            for field in required_fields:
                if current_fields and field.name in current_fields:
                    continue
                rec.mapper_fields_ids += mapper_field_obj.create(
                    {'odoo_field': field.id})
            rec.check_mapped_fields()

    def get_mapped_fields(self):
        """Return a dict with k=source field and v= odoo field"""
        res = {}
        for field in self.mapper_fields_ids:
            field.source_field = field.source_field or field.odoo_field.name
            res.update({field.source_field: field.odoo_field.name})
        return res

    def _get_search_domain(self):
        if self.search_domain:
            try:
                domain = eval(self.search_domain)
            except Exception:
                raise ValidationError(_("Error Validating Search Domain"))
            if type(domain) is not list:
                raise ValidationError(_("Error Validating Search Domain"))
            return domain

    def get_data_for_sync(self):
        for rec in self:
            if rec.active:
                models, db, uid, password = rec.webservice_id.\
                    _get_models_webservice()
                domain = []
                add_domain = rec._get_search_domain()
                if add_domain:
                    domain.append(add_domain)
                try:
                    res_list = models.execute_kw(db, uid, password,
                                                 rec.source_model,
                                                 'search_read', [domain],
                                                 {'fields': ['id']})
                except Exception:
                    raise UserError(
                        _("Error with domain used for search,"
                          " be sure you write the domain like:\n"
                          "['field','=','value']"))

                for res in res_list:
                    rec.with_delay().sync_data(res['id'])
        return {}

    @api.multi
    def action_sync_data(self):
        for rec in self:
            rec.sync_data()
        return {}

    @job
    def sync_data(self, res_id=False, odoo_id=False, create_method='before'):
        """Return a list with records sync"""
        self.ensure_one()
        record_list = []
        if res_id:
            res_ids = res_id
        else:
            try:
                res_ids = eval(self.sync_ids)
                if type(res_ids) is not int and type(res_ids) is not list:
                    res_ids = False
            except Exception:
                res_ids = False
        data_list, odoo_id = self.read_data(res_ids, odoo_id)
        for data in data_list:
            rec_id = self.write_data(data, odoo_id, create_method)
            if rec_id:
                record_list.append(rec_id)
        return record_list

    def read_data(self, res_id=False, odoo_rec=False):
        """This function read data from source database and search in
        the current databasa, it will return
        data_list dict from souce db data
        rec_id record from current db or false if is not found.
        """
        self.ensure_one()
        if not self.active:
            return None
        elif odoo_rec and not self.update:
            return False, odoo_rec
        # Init Variables
        domain, data, op = [], {}, ""
        # Get connexion and get odoo model
        models, db, uid, password = self.webservice_id.\
            _get_models_webservice()
        model_obj = self.env[self.odoo_model.model].sudo()
        # Reading in current database
        # If res_id is set search this record in current odoo  and source odoo
        if res_id:
            # Set Domain for Current Odoo DB
            domain += self.get_company_domain()
            op = 'in' if type(res_id) is list and len(res_id) > 1 else '='
            if self.search_field and not odoo_rec:
                domain = [(self.search_field, op, res_id)]
                odoo_rec = model_obj.search(domain)
                if odoo_rec and not self.update:
                    return data, odoo_rec
            # Set Domain for Source Odoo DB
            domain = [['id', op, res_id]]
        elif self.search_domain:
            domain = [eval(self.search_domain)]
        else:
            domain = []
        mapped_fields = self.get_mapped_fields()
        data_list = models.execute_kw(db, uid, password, self.source_model,
                                      'search_read', [domain],
                                      {'fields': list(mapped_fields.keys())})
        self.result = '--DATA READ--\n %s' % str(data_list)
        return data_list, odoo_rec

    @api.multi
    def write_data(self, data_read, odoo_rec=False, create_method='before'):
        """This function write data for the model and return the record
            res_id = id in source, odoo_rec = rec in current odoo
            record_list and data are use for reset the values
            in recursive call
        """
        if not data_read:
            return False
        # Init Variables
        domain = []
        model_obj = self.env[self.odoo_model.model].sudo()
        data_write = {}
        # Get all Mapped Fields with relation with other models
        dependences_ids = self.mapper_fields_ids.filtered(
            lambda x: x.odoo_relation)
        for dependence in dependences_ids:
            field_name = dependence.source_field
            is_o2m = dependence.odoo_field.ttype in ["one2many", "many2many"]
            if not data_read.get(field_name, False):
                continue
            # Search record values in the current database
            res_values = data_read[field_name]
            if dependence.dependence_id:
                if is_o2m:
                    depen_recs = dependence.dependence_id.sync_data(
                        res_id=res_values,
                        create_method=dependence.create_method)
                    if not depen_recs:
                        continue
                    depen_vals = []
                    create_recs = [x for x in depen_recs if type(x) is dict]
                    update_recs = [
                        x for x in depen_recs if x not in create_recs
                    ]
                    if update_recs:
                        depen_vals.append((6, 0, [x.id for x in update_recs]))
                    for depen_rec in create_recs:
                        depen_vals.append((0, 0, depen_rec))
                    if dependence.unique:
                        domain.append((dependence.odoo_field.name, 'in',
                                       [x.id for x in update_recs]))
                else:
                    value = dependence.dependence_id.sync_data(
                        res_id=res_values[0])
                    if not value or not value[0]:
                        continue
                    depen_vals = value[0].id
                    if dependence.unique:
                        domain.append(
                            (dependence.odoo_field.name, '=', depen_vals))
            else:
                depen_ids = dependence.search_record(res_values, is_o2m)
                if depen_ids:
                    depen_vals = ([(6, 0, [x.id for x in depen_ids])]
                                  if is_o2m else depen_ids.id)
                else:
                    depen_vals = depen_ids
            data_write.update({dependence.odoo_field.name: depen_vals})
            data_read.pop(field_name)
        data_write_after = {}
        # After read values search by unique values in current DB
        OR_domain = []
        if not odoo_rec:
            for field_id in self.mapper_fields_ids:
                if field_id.source_field not in data_read.keys():
                    continue
                value = data_read[field_id.source_field]
                if (not value and field_id.odoo_field.ttype not in
                   ['boolean', 'integer', 'float']):
                    continue
                if field_id.unique:
                    if field_id.search_operator == '|':
                        OR_domain += field_id.get_field_domain(value)
                    else:
                        domain += field_id.get_field_domain(value)
                if field_id.create_method == "after":
                    data_write_after.update({
                        field_id.odoo_field.name:
                        field_id.transform_data(value)
                    })
                else:
                    data_write.update({
                        field_id.odoo_field.name:
                        field_id.transform_data(value)
                    })
        # Fill with company
        if self.company_field:
            data_write.update(
                {self.company_field: self.webservice_id.company_id.id})
            domain += bool(domain) and self.get_company_domain() or []
        domain = ['|' for x in range(len(OR_domain) - 1)] + OR_domain + domain
        found = False
        # Delete None values
        print(data_write)
        data_write = {k: v for k, v in data_write.items() if v is not None}
        # Get Default Values
        data_write = {**model_obj.default_get(data_write), **data_write}
        self.result += "\n----DATA WRITE----\n%s" % str(data_write)
        # Logica actualizacion
        if not odoo_rec and domain:
            odoo_rec = model_obj.search(domain)
        if odoo_rec:
            if self.update:
                odoo_rec.sudo().write(data_write)
        else:
            if not self.create_active:
                return
            if create_method == 'together':
                return data_write
            odoo_rec = model_obj.create(data_write)
        if self.method_calls:
            if not found or (found and self.update):
                for method in self.method_calls.split(';'):
                    try:
                        getattr(odoo_rec, method)()
                    except Exception as err:
                        _logger.info('Error with calling method %s' % err)
        if data_write_after:
            odoo_rec.sudo().write(data_write_after)
        return odoo_rec[0]
