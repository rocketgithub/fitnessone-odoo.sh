# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
# Developed By: Jahangir Naik
##########################################################################
from odoo import fields, models, api


class ChannelTemplateMappings(models.Model):
    _name = "channel.template.mappings"
    _inherit = ['channel.mappings']

    store_product_id = fields.Char(
        string='Store Product ID',
        required=True)
    odoo_template_id = fields.Char(
        string='Odoo Template ID',
        required=True)
    template_name = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
    )
    default_code = fields.Char(
        string="Default code/SKU")
    barcode = fields.Char(
        string="Barcode/EAN/UPC or ISBN")
    _sql_constraints = [
        # ('channel_store_store_product_id_uniq',
        #     'unique(channel_id, store_product_id)',
        #     'Store Product ID must be unique for channel product mapping!'),
        # ('channel_odoo_odoo_template_id_uniq',
        #     'unique(channel_id, odoo_template_id)',
        #     'Odoo Template ID must be unique for channel template mapping!'),
    ]
    @api.multi
    def unlink(self):
        for record in self:
            if record.store_product_id:
                match = record.channel_id.match_product_feeds(record.store_product_id)
                if match: match.unlink()
        res = super(ChannelTemplateMappings, self).unlink()
        return  res

    def _compute_name(self):
        for record in self:
            if record.template_name:
                record.name = record.template_name.name
            else:
                record.name = 'Deleted/Undefined'

    @api.onchange('template_name')
    def change_odoo_id(self):
        self.odoo_template_id = self.template_name.id


class ChannelProductMappings(models.Model):
    _name = "channel.product.mappings"
    _inherit = ['channel.mappings']

    store_product_id = fields.Char(
        string='Store Template ID',
        required=True)
    store_variant_id = fields.Char(
        string=' Store Varinat ID',
        required=True,
        default='No Variants')
    erp_product_id = fields.Integer(
        string='Odoo Variant ID',
        required=True)
    product_name = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True
    )
    odoo_template_id = fields.Many2one(
        related='product_name.product_tmpl_id',
        string='Odoo Template')
    default_code = fields.Char(
        string="Default code/SKU")
    barcode = fields.Char(
        string="Barcode/EAN/UPC or ISBN")
    _sql_constraints = [
        # ('channel_store_store_product_id_store_variant_id_uniq',
        #     'unique(channel_id, store_product_id,store_variant_id)',
        #     'Store product+ variants must be unique for channel product mapping!'),

    ]

    def _compute_name(self):
        for record in self:
            if record.product_name.name:
                record.name = record.product_name.name
            else:
                record.name = 'Deleted'

    @api.onchange('product_name')
    def change_odoo_id(self):
        self.erp_product_id = self.product_name.id
        self.odoo_template_id = self.product_name.product_tmpl_id.id
