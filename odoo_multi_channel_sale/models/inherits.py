# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import itertools
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
ProductIdType = [
    ('wk_upc', 'UPC'),
    ('wk_ean', 'EAN'),
    ('wk_isbn', 'ISBN'),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"
    wk_parent_default_code=fields.Char(
        string = "Parent Code"
    )
    length = fields.Float(
        string='Length',
    )
    width = fields.Float(
        string='Width',
    )
    height = fields.Float(
        string='Height',
    )
    dimensions_uom_id = fields.Many2one(
        'product.uom',
        'Unit of Measure',
        help="Default Unit of Measure used for dimension."
    )

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.template.mappings',
        inverse_name='template_name',
        copy=False
    )
    # extra_categ_ids = fields.Many2many(
        # 'product.category',
    # )

    channel_category_ids = fields.One2many(
        string = 'Extra Categories',
        comodel_name = 'extra.categories',
        inverse_name = 'product_id',
    )

    channel_ids = fields.Many2many(
        'multi.channel.sale',
        'product_tmp_channel_rel',
        'product_tmpl_id',
        'channel_id',
        string='Channel(s)'
    )
    wk_product_id_type = fields.Selection(
        selection=ProductIdType,
        string='Product ID Type',
        default='wk_upc',
    )

class ExtraCategories(models.Model):
    _name = 'extra.categories'

    @api.model
    def get_category_list(self):
        li = []
        category_ids_list = self.env['channel.category.mappings'].search([('channel_id', '=', self.instance_id.id)])
        if category_ids_list:
            for i in category_ids_list:
                li.append(i.odoo_category_id)
        return li

    @api.multi
    @api.depends('instance_id')
    def _compute_extra_categories_domain(self):
        for record in self:
            categ_list = record.get_category_list()
            record.extra_category_domain_ids = [(6,0,categ_list)]

    instance_id = fields.Many2one(
        comodel_name = 'multi.channel.sale',
        string = 'Instance',

    )

    extra_category_ids = fields.Many2many(
        comodel_name='product.category',
        string = 'Extra Categories',
        domain="[('id', 'in', extra_category_domain_ids[0][2])]",
    )

    product_id = fields.Many2one(
        comodel_name = 'product.template',
        string = 'Template',
    )
    extra_category_domain_ids = fields.Many2many(
        "product.category",
        'extra_categ_ref',
        'product_categ_ref',
        'table_ref',
        compute="_compute_extra_categories_domain",
        string="Category Domain",
    )
    category_id = fields.Many2one(
        comodel_name='product.category',
        string='Internal Category'
    )

    @api.onchange('instance_id')
    def change_domain(self):
        categ_list = self.get_category_list()
        domain = {'domain': {'extra_category_ids': [('id', 'in', categ_list)]}}
        return domain




class ProductCategory(models.Model):
    _inherit = "product.category"

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.category.mappings',
        inverse_name='category_name',
        copy=False
    )

    channel_category_ids = fields.One2many(
        string='Channel Categories',
        comodel_name='extra.categories',
        inverse_name='category_id',
        copy=False
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends('wk_extra_price')
    def _get_price_extra(self):
        for product in self:
            price_extra = 0.0
            for variant_id in product.attribute_value_ids:
                for price_id in variant_id.price_ids:
                    if price_id.product_tmpl_id.id == product.product_tmpl_id.id:
                        price_extra += price_id.price_extra
            product.price_extra = price_extra + product.wk_extra_price
            product.attr_price_extra = price_extra



    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.product.mappings',
        inverse_name='product_name',
        copy=False
    )

    wk_extra_price  = fields.Float(
        'Price Extra',
        digits = dp.get_precision('Product Price'),
    )

    price_extra  = fields.Float(
        string = 'Price Extra',
        compute = _get_price_extra,
        digits = dp.get_precision('Product Price'),
        help = "This shows the sum of all attribute price and additional price of variant (All Attribute Price+Additional Variant price)",

    )
    attr_price_extra  = fields.Float(
        string = 'Variant Extra Price',
        compute = _get_price_extra,
        digits = dp.get_precision('Product Price'),
    )

    @api.model
    def check_for_new_price(self, template_id, value_id, price_extra):
        context = dict(self._context or {})
        product_attribute_price = self.env['product.attribute.price']
        exists = product_attribute_price.search(
            [('product_tmpl_id', '=', template_id), ('value_id', '=', value_id)])
        if not exists:
            temp = {'product_tmpl_id': template_id,
                    'value_id': value_id, 'price_extra': price_extra}
            pal_id = product_attribute_price.create(temp)
            return True
        else:
            check = exists.write({'price_extra': price_extra})
            return True

    @api.model
    def get_product_attribute_id(self, attribute_id):
        product_attribute_id = 0
        context = dict(self._context or {})
        attribute_map_domain = [
            ('channel_id', '=', context.get('channel_id'))]
        store_attribute_id = ''
        map_env = self.env[
            'channel.attribute.mappings']
        if attribute_id.get('attrib_name_id'):
            store_attribute_id = attribute_id.get('attrib_name_id')
        else:
            store_attribute_id = attribute_id.get('name')
        attribute_mapping = map_env.search([('channel_id', '=', context.get(
            'channel_id')), ('store_attribute_id', '=', store_attribute_id)], limit=1)
        if not attribute_mapping:
            product_attribute = self.env['product.attribute'].search(
                [('name', '=', attribute_id.get('name'))])
            if not product_attribute:
                product_attribute_id = self.env['product.attribute'].create(
                    {'name': attribute_id.get('name')}).id
            else:
                product_attribute_id = product_attribute[0].id
            vals = {
                'store_attribute_id': store_attribute_id,
                'store_attribute_name': attribute_id.get('name'),
                'attribute_name': product_attribute_id,
                'odoo_attribute_id': product_attribute_id,
                'channel_id': context.get('channel_id'),
                'ecom_store': context.get('channel')
            }

            map_env.create(vals)
        else:
            product_attribute_id = attribute_mapping.odoo_attribute_id

        return product_attribute_id

    @api.model
    def get_product_attribute_value_id(self, attribute_id, product_attribute_id, template_id):
        product_attribute_value_id = 0
        context = dict(self._context or {})
        store_attribute_value_id = ''
        map_env = self.env[
            'channel.attribute.value.mappings']
        if attribute_id.get('attrib_value_id'):
            store_attribute_value_id = attribute_id.get('attrib_value_id')
        else:
            store_attribute_value_id = attribute_id.get('value')
        attribute_value_mapping = self.env[
            'channel.attribute.value.mappings'].search([('channel_id', '=', context.get('channel_id')), ('store_attribute_value_id', '=', store_attribute_value_id)], limit=1)

        if not attribute_value_mapping:
            product_attribute_value = self.env['product.attribute.value'].search([
                ('name', '=', attribute_id.get('value')),
                ('attribute_id', '=', product_attribute_id),
            ])
            if not product_attribute_value:
                context['active_id'] = template_id.id
                product_attribute_value_id = self.env['product.attribute.value'].with_context(context).create(
                    {'name': attribute_id.get('value'),
                     'attribute_id': product_attribute_id
                     }).id
            else:
                product_attribute_value_id = product_attribute_value[0].id
            map_env.create({
                'store_attribute_value_id': store_attribute_value_id,
                'store_attribute_value_name': attribute_id.get('value'),
                'attribute_value_name': product_attribute_value_id,
                'odoo_attribute_value_id': product_attribute_value_id,
                'channel_id': context.get('channel_id'),
                'ecom_store': context.get('channel')
            })
        else:
            product_attribute_value_id = attribute_value_mapping.odoo_attribute_value_id
        return product_attribute_value_id

    @api.multi
    def check_for_new_attrs(self, template_id, variant):
        context = dict(self._context or {})
        product_template = self.env['product.template']
        product_attribute_line = self.env['product.attribute.line']
        all_values = []
        attributes = variant.name_value
        for attribute_id in eval(attributes):
            product_attribute_id = self.get_product_attribute_id(attribute_id)
            exists = product_attribute_line.search(
                [('product_tmpl_id', '=', template_id.id),
                 ('attribute_id', '=', product_attribute_id)
                 ])
            if not exists:
                temp = {'product_tmpl_id': template_id.id,
                        'attribute_id': product_attribute_id}
                pal_id = product_attribute_line.create(temp)
            else:
                pal_id = exists[0]
            product_attribute_value_id = self.get_product_attribute_value_id(
                attribute_id, product_attribute_id, template_id)
            value_ids = pal_id.value_ids.ids
            check = product_attribute_value_id not in value_ids
            if product_attribute_value_id not in value_ids:
                pal_id.write({'value_ids': [[4, product_attribute_value_id]]})
            if product_attribute_value_id not in all_values:
                all_values.append(product_attribute_value_id)
            if attribute_id.get('price'):
                self.with_context(context).check_for_new_price(
                    template_id.id, product_attribute_value_id, attribute_id.get('price'))
        return [(6, 0, all_values)]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.order.mappings',
        inverse_name='order_name',
        copy=False
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.partner.mappings',
        inverse_name='odoo_partner',
        copy=False
    )


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    channel_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='channel.shipping.mappings',
        inverse_name='odoo_shipping_carrier',
        copy=False
    )


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_paid(self):
        self.wk_pre_confirm_paid()
        result = super(AccountInvoice, self).action_invoice_paid()
        self.wk_post_confirm_paid(result)
        return result

    def wk_get_invoice_order(self, invoice):
        data = map(
            lambda line_id:
            list(set(line_id.sale_line_ids.mapped('order_id'))),
            invoice.invoice_line_ids
        )
        return list(itertools.chain(*data))

    @api.multi
    def wk_pre_confirm_paid(self):
        for invoice in self:
            order_ids = self.wk_get_invoice_order(invoice)
            for order_id in order_ids:
                mapping_ids = order_id.channel_mapping_ids
                channel_id = mapping_ids.mapped('channel_id')
                channel_id = channel_id and channel_id[0] or channel_id
                if hasattr(channel_id, '%s_pre_confirm_paid' % channel_id.channel):
                    res = getattr(channel_id,
                                  '%s_pre_confirm_paid' % channel_id.channel)(invoice, mapping_ids)
        return True

    @api.multi
    def wk_post_confirm_paid(self, result):
        for invoice in self:
            order_ids = self.wk_get_invoice_order(invoice)
            for order_id in order_ids:
                mapping_ids = order_id.channel_mapping_ids
                channel_id = mapping_ids.mapped('channel_id')
                channel_id = channel_id and channel_id[0] or channel_id
                if hasattr(channel_id, '%s_post_confirm_paid' % channel_id.channel):
                    res = getattr(channel_id,
                                  '%s_post_confirm_paid' % channel_id.channel)(invoice, mapping_ids, result)
        return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        self.ensure_one()
        self.wk_pre_do_transfer()
        result = super(StockPicking, self).action_done()
        self.wk_post_do_transfer(result)
        return result

    @api.multi
    def wk_pre_do_transfer(self):
        order_id = self.sale_id
        if order_id:
            mapping_ids = order_id.channel_mapping_ids
            channel_id = mapping_ids.mapped('channel_id')
            channel_id = channel_id and channel_id[0] or channel_id
            if hasattr(channel_id, '%s_pre_do_transfer' % channel_id.channel):
                res = getattr(channel_id,
                              '%s_pre_do_transfer' % channel_id.channel)(self, mapping_ids)
        return True

    @api.multi
    def wk_post_do_transfer(self, result):
        order_id = self.sale_id
        if order_id:
            mapping_ids = order_id.channel_mapping_ids
            channel_id = mapping_ids.mapped('channel_id')
            channel_id = channel_id and channel_id[0] or channel_id
            if hasattr(channel_id, '%s_post_do_transfer' % channel_id.channel):
                res = getattr(channel_id,
                              '%s_post_do_transfer' % channel_id.channel)(self, mapping_ids, result)
        return True


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    @api.model
    def create(self, vals):
        context = self._context
        if context.get('odoo_multi_attribute') or context.get('install_mode'):
            domain = [('name', '=ilike', vals.get('name').strip(' '))]
            obj = self.search(domain, limit=1)
            if obj:
                return obj
        return super(ProductAttribute, self).create(vals)
