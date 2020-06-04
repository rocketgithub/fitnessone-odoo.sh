# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
Source = [
    ('all','All'),
    ('categories_ids','Product ID(s)'),
]

class ImportCategories(models.TransientModel):

    _inherit = ['import.operation']
    _name = "import.categories"

    category_ids = fields.Text(string='Categories ID(s)')
    parent_categ_id = fields.Many2one(
        'channel.category.mappings',
        'Parent Category',
    )

class ExportCategories(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.categories"

    @api.model
    def default_get(self,fields):
        res=super(ExportCategories,self).default_get(fields)
        if not res.get('category_ids') and self._context.get('active_model')=='product.category':
            res['category_ids']=self._context.get('active_ids')
        return res

    category_ids = fields.Many2many(
        'product.category',
        string='Category',
    )
