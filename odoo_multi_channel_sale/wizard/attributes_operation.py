# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
from odoo import api, fields, models, _
class ImportAttribute(models.TransientModel):

    _inherit = ['import.operation']
    _name = "import.attributes"

    attribute_ids = fields.Text(string='Attribute ID(s)')

class ExportAttribute(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.attributes"

    @api.model
    def default_get(self,fields):
        res=super(ExportAttribute,self).default_get(fields)
        if not res.get('attribute_ids') and self._context.get('active_model')=='product.attribute':
            res['attribute_ids']=self._context.get('active_ids')
        return res

    attribute_ids = fields.Many2many(
        'product.attribute',
        string='Attribute(s)',
    )

class ImportAttributeValue(models.TransientModel):

    _inherit = ['import.operation']
    _name = "import.attributes.value"

    attribute_value_ids = fields.Text(string='Attribute Value ID(s)')

class ExportAttributeValue(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.attributes.value"

    @api.model
    def default_get(self,fields):
        res=super(ExportAttributeValue,self).default_get(fields)
        if not res.get('attribute_value_ids') and self._context.get('active_model')=='product.attribute.value':
            res['attribute_value_ids']=self._context.get('active_ids')
        return res

    attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        string='Attribute(s)',
    )
