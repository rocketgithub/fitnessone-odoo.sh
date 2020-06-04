# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
SourceProduct = [
    ('all','All'),
    ('product_ids','Product ID(s)'),
]
SourceTemplate = [
    ('all', 'All'),
    ('product_tmpl_ids', 'Product ID(s)'),
]
class ImportProducts(models.TransientModel):

    _inherit = ['import.operation']
    _name = "import.products"
    product_ids = fields.Text(string='Product ID(s)')
    source = fields.Selection(SourceProduct, required=1, default='all')


class ImportTemplates(models.TransientModel):

    _inherit = ['import.operation']
    _name = "import.templates"
    product_tmpl_ids = fields.Text(string='Product Template ID(s)')
    source = fields.Selection(SourceTemplate, required=1, default='all')


class ExportProducts(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.products"

    @api.model
    def default_get(self,fields):
        res=super(ExportProducts,self).default_get(fields)
        if not res.get('product_ids') and self._context.get('active_model')=='product.product':
            res['product_ids']=self._context.get('active_ids')
        return res

    product_ids = fields.Many2many(
        'product.product',
        string='Product(s)',
    )
    sku_sequence_id = fields.Many2one(
        related='channel_id.sku_sequence_id',
        string = 'SKU  Sequence'
    )


class ExportTemplates(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.templates"

    @api.multi
    def export_odoo_products(self):
        if hasattr(self, 'export_%s_templates' % self.channel_id.channel):
            return getattr(self, 'export_%s_templates' % self.channel_id.channel)()

    @api.multi
    def update_odoo_products(self):
        if hasattr(self, 'update_%s_templates' % self.channel_id.channel):
            return getattr(self, 'update_%s_templates' % self.channel_id.channel)()

    @api.model
    def default_get(self,fields):
        res=super(ExportTemplates,self).default_get(fields)
        if not res.get('product_tmpl_ids') and self._context.get('active_model')=='product.template':
            res['product_tmpl_ids']=self._context.get('active_ids')
        return res

    product_tmpl_ids = fields.Many2many(
        'product.template',
        string='Product Template(s)',
    )
    sku_sequence_id = fields.Many2one(
        related='channel_id.sku_sequence_id',
        string = 'SKU  Sequence'
    )
