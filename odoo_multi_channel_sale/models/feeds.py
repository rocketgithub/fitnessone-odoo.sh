#-*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import copy
from collections import Counter
from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, ValidationError, Warning
from odoo.addons.odoo_multi_channel_sale.tools import parse_float,extract_list as EL
import logging
_logger = logging.getLogger(__name__)
State = [
    ('draft', 'Draft'),
    ('update', 'Update'),
    ('done', 'Done'),
    ('cancel', 'Cancel'),
    ('error', 'Error'),
]
Fields = [
    'name',
    'store_id',
    # 'store_source',
]
CategoryFields = Fields + [
    'parent_id',
    'description'
]
ProductFields = Fields + [
    'extra_categ_ids',
    'list_price',
    'image_url',
    'image',
    'default_code',
    'barcode',
    'type',
    'wk_product_id_type',
    'description_sale',
    'description_purchase',
    'standard_price',
    'sale_delay',
    'qty_available',
    'weight',
    'feed_variants',
    'weight_unit',
    'length',
    'width',
    'height',
    'dimensions_unit',
    'hs_code'
]


class WkFeed(models.Model):
    _name = "wk.feed"
    sequence = fields.Char(
        string='Sequence',
    )
    active = fields.Boolean(
        string='Active',
        default=1
    )
    name = fields.Char(
        string='Name',
    )
    __last_update = fields.Datetime(
        string='Last Modified on'
    )
    state = fields.Selection(
        selection=State,
        string='Update Required',
        default='draft',
        copy=False,
    )
    channel_id = fields.Many2one(
        'multi.channel.sale',
        string='Instance',
        domain=[('state', '=', 'validate')]
    )
    channel = fields.Selection(
        related='channel_id.channel',
        string="Channel",
    )
    store_id = fields.Char(
        string='Store ID',
    )
    store_source = fields.Char(
        string='Store Source',
    )
    message = fields.Html(
        string='Message',
        copy=False,
    )


    @api.model
    def get_product_fields(self):
        return copy.deepcopy(ProductFields)

    @api.model
    def get_category_fields(self):
        return copy.deepcopy(CategoryFields)

    @api.multi
    def open_mapping_view(self):
        self.ensure_one()
        res_model = self._context.get('mapping_model')
        store_field = self._context.get('store_field')
        duplicity_domain = []
        channel_id = self.channel_id
        duplicity_config=self.env['multi.channel.sale.config'].get_values()
        domain = [
            ('channel_id', '=', channel_id.id),
        ]
        if res_model in ['channel.product.mappings','channel.template.mappings'] and  duplicity_config.get('avoid_duplicity'):
            avoid_duplicity_using = duplicity_config.get('avoid_duplicity_using')
            barcode = self.barcode
            default_code = self.default_code
            domain+=['|',(store_field, '=', self.store_id)]
            if default_code and barcode:
                domain += ['|',
                ('barcode', '=', barcode),
                ('default_code', '=',default_code)
                ]
            elif default_code:
                domain += [('default_code', '=', default_code)]
            else:
                domain += [('barcode', '=', barcode)]
        else:
            domain+=[(store_field, '=', self.store_id)]
        mapping_ids = self.env[res_model].search(domain).ids
        return {
            'name': ('Mapping'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': res_model,
            'view_id': False,
            'domain': [('id', 'in', mapping_ids)],
            'target': 'current',
        }

    @api.multi
    def set_feed_state(self, state='done'):
        self.state = state
        return True

    @api.multi
    def get_feed_result(self, feed_type):
        message = ""
        tot = len(self)
        if tot == 1:
            if self.state == 'done':
                message += "{_type} feed sucessfully evaluated .".format(
                    _type=feed_type
                )
            else:
                message += "{_type} feed failed to evaluate .".format(
                    _type=feed_type
                )
        else:
            done_feeds = self.filtered(lambda feed: feed.state == 'done')
            error_feed = tot - len(done_feeds)
            if not error_feed:
                message += "All ({done}) {_type} feed sucessfully evaluated .".format(
                    done=len(done_feeds), _type=feed_type
                )
            else:
                message += "<br/>{error} {_type} feed failed to evaluate".format(
                    error=error_feed, _type=feed_type
                )
                if len(done_feeds):
                    message += "<br/>{done} {_type} feed sucessfully evaluated".format(
                        done=len(done_feeds), _type=feed_type
                    )
        return message

    @api.model
    def get_channel_domain(self):
        return [('channel_id', '=', self.channel_id.id)]

    @api.model
    def get_categ_id(self, store_categ_id,channel_id):

        message = ''
        categ_id = None
        match = channel_id.match_category_mappings(store_categ_id)
        if match:
            categ_id = match.odoo_category_id
        else:
            feed = channel_id.match_category_feeds(store_categ_id)
            if feed:
                res = feed.import_category(channel_id)
                message += res.get('message', '')
                mapping_id = res.get('update_id') or res.get('create_id')
                if mapping_id:
                    categ_id = mapping_id.odoo_category_id
            else:
                message += '<br/>Category Feed Error: No mapping as well category feed found for %s .' % (
                    store_categ_id)
        return dict(
            categ_id=categ_id,
            message=message
        )

    @api.model
    def get_extra_categ_ids(self, store_categ_ids,channel_id):
        message = ''
        categ_ids = []
        for store_categ_id in store_categ_ids.strip(',').split(','):
            res = self.get_categ_id(store_categ_id,channel_id)
            message += res.get('message', '')
            categ_id = res.get('categ_id')
            if categ_id:
                categ_ids += [categ_id]
        return dict(
            categ_ids=categ_ids,
            message=message
        )

    @api.model
    def get_order_partner_id(self, store_partner_id,channel_id):
        partner_obj = self.env['res.partner']
        message = ''
        partner_id = None
        partner_invoice_id = None
        partner_shipping_id = None
        context = dict(self._context)
        context['no_mapping'] = self.customer_is_guest
        partner_id = self.with_context(context).create_partner_contact_id(
                partner_id,channel_id,store_partner_id)
        partner_invoice_id = self.with_context(context).create_partner_invoice_id(
            partner_id,channel_id,self.invoice_partner_id)
        if self.same_shipping_billing:
            partner_shipping_id = partner_invoice_id
        else:
            partner_shipping_id = self.with_context(context).create_partner_shipping_id(
                partner_id,channel_id,partner_shipping_id)
        return dict(
            partner_id=partner_id,
            partner_shipping_id=partner_shipping_id,
            partner_invoice_id=partner_invoice_id,
            message=message
        )

    @api.model
    def get_partner_id(self, store_partner_id, _type='contact',channel_id=None):
        partner_obj = self.env['res.partner']
        message = ''
        partner_id = None
        match = channel_id.match_partner_mappings(store_partner_id, _type)
        if match:
            partner_id = match.odoo_partner
        else:
            feed = channel_id.match_partner_feeds(store_partner_id, _type)
            if feed:
                res = feed.import_partner(channel_id)
                message += res.get('message', '')
                mapping_id = res.get('update_id') or res.get('create_id')
                if mapping_id:
                    partner_id = mapping_id.odoo_partner
            else:
                message += '<br/>Partner Feed Error: No mapping as well partner feed found for %s.' % (
                    store_partner_id)

        return dict(
            partner_id=partner_id,
            message=message
        )

    @api.model
    def get_product_id(self, store_product_id, line_variant_ids, channel_id ,default_code=None,barcode = None):
        message = ''
        domain = []
        if default_code:
            domain += [
                ('default_code','=',default_code),
            ]
        if barcode:
            domain += [
                ('barcode','=',barcode),
            ]
        product_id = None
        match = channel_id.match_product_mappings(
            store_product_id, line_variant_ids,domain=domain)
        if match:
            product_id = match.product_name
        else:
            feed = channel_id.match_product_feeds(store_product_id ,domain = domain)
            product_variant_feeds = channel_id.match_product_variant_feeds(store_product_id,domain=domain)
            if feed:
                res = feed.import_product(channel_id)
                message += res.get('message', '')
                mapping_id = res.get('update_id') or res.get('create_id')

                match = channel_id.match_product_mappings(
                    store_product_id, line_variant_ids,domain=domain)
                if match:
                    product_id = match.product_name
            elif product_variant_feeds and product_variant_feeds.feed_templ_id:
                res = product_variant_feeds.feed_templ_id.import_product(channel_id)
                message += res.get('message', '')
                match = channel_id.match_product_mappings(
                     line_variant_ids=store_product_id)
                if match:
                    product_id = match.product_name
            else:
                message += '<br/>Product Feed Error: For product id (%s) sku (%s) no mapping as well feed found.' % (
                    store_product_id,default_code)
        return dict(
            product_id=product_id,
            message=message
        )

    @api.model
    def get_carrier_id(self, carrier_id, service_id=None,channel_id=None):
        message = ''
        res_id = None
        shipping_service_name = service_id and service_id or carrier_id
        match = channel_id.match_carrier_mappings(shipping_service_name)
        if match:
            res_id = match.odoo_shipping_carrier
        else:
            res_id = channel_id.create_carrier_mapping(
                carrier_id, service_id)
        return dict(
            carrier_id=res_id,
            message=message
        )

    def get_partner_invoice_vals(self,partner_id,channel_id):
        name = self.invoice_name
        if self.invoice_last_name:
            name = '%s %s' % (name, self.invoice_last_name)
        vals = dict(
            type='invoice',
            name=self.invoice_name,
            street=self.invoice_street,
            street2=self.invoice_street2,
            city=self.invoice_city,
            zip=self.invoice_zip,
            email=self.invoice_email,
            phone=self.invoice_phone,
            mobile=self.invoice_mobile,
            parent_id=partner_id.id,
            customer=False,
        )
        country_id = self.invoice_country_id and channel_id.get_country_id(
            self.invoice_country_id)
        if country_id:
            vals['country_id'] = country_id.id
        state_id = (self.invoice_state_id or self.invoice_state_name) and country_id and channel_id.get_state_id(
            self.invoice_state_id, country_id, self.invoice_state_name
        )
        if state_id:
            vals['state_id'] = state_id.id
        return vals

    @api.model
    def create_partner_invoice_id(self, partner_id,channel_id,invoice_partner_id=None):
        partner_obj = self.env['res.partner']
        vals = self.get_partner_invoice_vals(partner_id,channel_id)
        match = None
        if invoice_partner_id:
            match = channel_id.match_partner_mappings(
                invoice_partner_id, 'invoice')
        if match:
            match.odoo_partner.write(vals)
            erp_id = match.odoo_partner
        else:
            erp_id = partner_obj.create(vals)
            if (not self._context.get('no_mapping') and invoice_partner_id):
                channel_id.create_partner_mapping(erp_id, invoice_partner_id, 'invoice')
        return erp_id

    def get_partner_shipping_vals(self,partner_id,channel_id):

        name = self.shipping_name
        if self.shipping_last_name:
            name = '%s %s' % (name, self.shipping_last_name)
        vals = dict(
            type='delivery',
            name=self.shipping_name,
            street=self.shipping_street,
            street2=self.shipping_street2,
            city=self.shipping_city,
            zip=self.shipping_zip,
            email=self.shipping_email,
            phone=self.shipping_phone,
            mobile=self.shipping_mobile,
            parent_id=partner_id.id,
            customer=False,
        )
        country_id = self.shipping_country_id and channel_id.get_country_id(
            self.shipping_country_id)
        if country_id:
            vals['country_id'] = country_id.id
        state_id = (self.shipping_state_id or self.shipping_state_name) and country_id and channel_id.get_state_id(
            self.shipping_state_id, country_id, self.shipping_state_name
        )
        if state_id:
            vals['state_id'] = state_id.id
        return vals

    @api.model
    def create_partner_shipping_id(self, partner_id,channel_id,shipping_partner_id=None):
        partner_obj = self.env['res.partner']
        match=None
        vals = self.get_partner_shipping_vals(partner_id,channel_id)
        if shipping_partner_id:
            match = channel_id.match_partner_mappings(
                shipping_partner_id, 'delivery')
        if match:
            match.odoo_partner.write(vals)
            erp_id = match.odoo_partner
        else:
            erp_id = partner_obj.create(vals)
            if (not self._context.get('no_mapping') and shipping_partner_id):
                channel_id.create_partner_mapping(erp_id, shipping_partner_id, 'delivery')
        return erp_id

    def get_partner_contact_vals(self,partner_id,channel_id):
        _type = 'contact'
        name = self.customer_name
        if self.customer_last_name:
            name = '%s %s' % (name, self.customer_last_name)
        vals = dict(
            type=_type,
            customer=1,
            name=self.customer_name,
            email=self.customer_email,
            phone=self.customer_phone,
            mobile=self.customer_mobile,
        )
        return vals

    @api.model
    def create_partner_contact_id(self, partner_id,channel_id,store_partner_id=None):
        partner_obj = self.env['res.partner']
        vals = self.get_partner_contact_vals(partner_id,channel_id)
        match  = None
        if store_partner_id:
            match = channel_id.match_partner_mappings(
                store_partner_id, 'contact')
        if match:
            match.odoo_partner.write(vals)
            erp_id = match.odoo_partner
        else:
            erp_id = partner_obj.create(vals)
            if (not self._context.get('no_mapping') and store_partner_id):
                channel_id.create_partner_mapping(erp_id, store_partner_id, 'contact')
        return erp_id


class CategoryFeed(models.Model):
    _name = "category.feed"
    # _description = "Category Feed"
    # _rec_name='sequence'
    _inherit = ["wk.feed"]

    description = fields.Text(
        string='Description',
    )
    parent_id = fields.Char(
        string='Store Parent ID',
    )
    leaf_category = fields.Boolean(
        string='Leaf Category'
    )

    @api.model
    def get_channel_specific_categ_vals(self,channel_id,vals):
        if hasattr(self,'get_%s_specific_categ_vals'%channel_id.channel):
            vals = getattr(self,'get_%s_specific_categ_vals'%channel_id.channel)(channel_id,vals)
        return vals

    @api.multi
    def import_category(self,channel_id):
        message = ""
        update_id = None
        create_id = None
        self.ensure_one()

        vals = EL(self.read(self.get_category_fields()))
        vals = self.get_channel_specific_categ_vals(channel_id,vals)
        store_id = vals.pop('store_id')
        match = channel_id.match_category_mappings(store_id)
        state = 'done'
        if not vals.get('name'):
            message += "<br/>Category without name can't evaluated"
            state = 'error'
        if not store_id:
            message += "<br/>Category without store ID can't evaluated"
            state = 'error'
        parent_id = vals.pop('parent_id')
        if parent_id:
            res = self.get_categ_id(parent_id,channel_id)

            res_parent_id = res.get('categ_id')
            if res_parent_id:
                vals['parent_id'] = res_parent_id
            else:
                _logger.error('#CategError1 %r'%res)
                state = 'error'
        vals.pop('description', None)
        vals.pop('website_message_ids','')
        vals.pop('message_follower_ids','')

        if match:
            if state == 'done':
                update_id = match
                try:
                    match.category_name.write(vals)
                    message += '<br/> Category %s successfully updated' % (
                        vals.get('name', ''))
                except Exception as e:
                    _logger.error('#CategError2 %r', e)
                    message += '<br/>%s' % (e)
                    state = 'error'
            elif state == 'error':
                message += '<br/>Error while category update.'

        else:
            if state == 'done':
                try:
                    erp_id = self.env['product.category'].create(vals)
                    create_id = channel_id.create_category_mapping(
                        erp_id, store_id, self.leaf_category
                    )
                    message += '<br/> Category %s Successfully Evaluate' % (
                        vals.get('name', ''))
                except Exception as e:
                    _logger.error('#CategError3 %r', e)
                    message += '<br/>%s' % (e)
                    state = 'error'

        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (self.message, message)
        return dict(
            create_id=create_id,
            update_id=update_id,
            message=message
        )

    @api.multi
    def import_items(self):
        update_ids = []
        create_ids = []
        message = ''

        for record in self:
            sync_vals = dict(
                status='error',
                action_on='category',
                action_type='import',
            )
            channel_id = record.channel_id
            res = record.import_category(channel_id)
            msz = res.get('message', '')
            message += msz
            update_id = res.get('update_id')
            if update_id:
                update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:
                create_ids.append(create_id)
            mapping_id = update_id or create_id
            if mapping_id:
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] = mapping_id.store_category_id
                sync_vals['odoo_id'] = mapping_id.odoo_category_id
            sync_vals['summary'] = msz
            channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
            return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        message = self.get_feed_result(feed_type='Category')
        return self.env['multi.channel.sale'].display_message(message)

    @api.model
    def cron_import_category(self):
        domain = [
            ('state', '!=', 'done')
        ]
        for record in self.search(domain):
            record.import_category(record.channel_id)
        return True


class ProductVaraintFeed(models.Model):
    _name = 'product.variant.feed'
    _inherit = ["wk.feed"]
    name_value = fields.Text(
        string='Name Value list',
        help="Format of the name value list should be like this :-> [{'name': 'Memory', 'value': '16 GB'}, {'name': 'Color', 'value': 'White'}, {'name': 'Wi-Fi', 'value': '2.4 GHz'}]",
    )
    type = fields.Char(
        string='Product Type',
        default = 'product'
    )
    # categ_id = fields.Char(
    #     string='Store Category ID',
    # )
    extra_categ_ids = fields.Text(
        string='Extra Category ID(s)',
        help="Format of the  should be like this :-> C1,C2,C3",
    )
    list_price = fields.Char(
        string='List Price',
    )
    default_code = fields.Char(
        string='Default Code/SKU',
    )
    barcode = fields.Char(
        string='Barcode/Ean13/UPC or ISBN',
    )
    description_sale = fields.Text(
        string='Sale Description',
    )
    description_purchase = fields.Text(
        string='Purchase Description',
    )
    standard_price = fields.Char(
        string='Standard Price',
    )
    sale_delay = fields.Char(
        string='Sale Delay',
    )
    qty_available = fields.Char(
        string='Qty',
    )
    weight = fields.Char(
        string='Weight',
    )
    weight_unit = fields.Char(
        string='Weight Unit',
    )
    length = fields.Char(
        string='Length',
    )
    width = fields.Char(
        string='Width',
    )
    height = fields.Char(
        string='Height',
    )
    dimensions_unit = fields.Char(
        string='Dimensions Unit Name',
    )
    feed_templ_id = fields.Many2one(
        comodel_name='product.feed',
        string='Template ID',
        ondelete='cascade',
    )
    wk_product_id_type = fields.Char(
        string='Product ID Type'
    )
    image = fields.Binary(
        string='Image'
    )
    image_url = fields.Char(
        string='Image Url')
    hs_code = fields.Char(
        string='HS Code')

class ProductFeed(models.Model):
    _name = "product.feed"
    _inherit = ["product.variant.feed"]

    need_sync = fields.Selection(
        (('yes', 'Yes'), ('no', 'No')),
        string='Update Required',
        default='no',
        required=True
    )
    feed_variants = fields.One2many(
        string='Varinats',
        comodel_name='product.variant.feed',
        inverse_name='feed_templ_id'
    )

    def match_attribute(self, attribute):
        attribute_id = self.env['product.attribute'].search(
            [('name', '=', attribute)])
        if attribute_id:
            return attribute_id
        return self.env['product.attribute'].create({'name': attribute})

    def match_attribute_value(self, value, attribute_id):
        value = value.strip("'").strip("'")
        domain = [('name', '=', str(value)),
                  ('attribute_id', '=', attribute_id)]
        value_id = self.env['product.attribute.value'].search(domain)
        if value_id:
            return value_id
        return self.env['product.attribute.value'].create({'name': value, 'attribute_id': attribute_id})

    @api.model
    def create_attribute_string(self, name_values):
        attstring = ''
        message = ''
        try:
            for name_value in eval(name_values):
                attstring += name_value['value'] + ","
        except Exception as e:
            _logger.error('-----Exception--------------%r', e)
            message += '<br/>%s' % (e)
        attstring = attstring.rstrip(',')
        return dict(
            attstring=attstring,
            message=message
        )

    def update_product_variants(self, variant_ids, template_id, store_id, location_id,channel_id):
        attribute_line_obj = self.env['product.attribute.line']
        prod_env = self.env['product.product']
        message = ''
        context = dict(self._context or {})
        context.update({'channel_id': channel_id.id})
        context.update({'channel': channel_id.channel})

        variant_objs = self.env['product.variant.feed'].browse(variant_ids)
        for variant in variant_objs:
            attr_string_res = self.create_attribute_string(variant.name_value)
            attr_string = attr_string_res.get('attstring')
            message += attr_string_res.get('message')
            if variant.store_id:
                variant_store_id = variant.store_id
            else:
                variant_store_id = attr_string
            exists = channel_id.match_product_mappings(
                store_id, variant_store_id, default_code=variant.default_code, barcode=variant.barcode)
            if not exists:
                self.with_context(context)._create_product_line(
                    variant, template_id, store_id, location_id,channel_id)
            else:
                attribute_value_ids = prod_env.with_context(context).check_for_new_attrs(
                    template_id, variant)
                if variant.list_price:
                    exists.product_name.wk_extra_price = parse_float(
                        variant.list_price) - parse_float(template_id.list_price)

                    price =parse_float(variant.list_price) #- template_id.list_price
                    self.wk_change_product_price(
                        product_id = exists.product_name,
                        price = price,
                        channel_id = channel_id
                    )
                if context.get('wk_qty_update',True) and  variant.qty_available and eval(variant.qty_available) > 0:
                    res = self.wk_change_product_qty(
                        exists.product_name, variant.qty_available, location_id)
        return message

    def get_variant_extra_values(self, template_id, variant,channel_id):
        vals = {}
        state = 'done'
        if variant.image:
            vals.update({'image': variant.image})
        else:
            image_url = variant.image_url
            if image_url and (image_url not in ['false','False',False]):
                image_res = channel_id.read_website_image_url(image_url)
                if image_res:vals['image'] = image_res
        if variant.description_sale:
            vals['description_sale'] = variant.description_sale
        weight_unit = variant.weight_unit
        if weight_unit:
            uom_id = channel_id.get_uom_id(name=weight_unit).id
            if uom_id:
                vals['uom_id'] = uom_id
                vals['uom_po_id'] = uom_id

        dimensions_unit = variant.dimensions_unit
        if dimensions_unit:
            vals['dimensions_uom_id'] = channel_id.get_uom_id(
                name=dimensions_unit).id
        if not variant.wk_product_id_type:
            vals['wk_product_id_type'] = 'wk_upc'
        else:
            vals['wk_product_id_type'] = variant.wk_product_id_type
        if variant.description_sale:
            vals['description_sale'] = variant.description_sale
        if variant.description_purchase:
            vals['description_purchase'] = variant.description_purchase
        if variant.list_price and template_id:
            vals['wk_extra_price'] = parse_float(variant.list_price) - parse_float(template_id.list_price)
        if variant.default_code:
            vals['default_code'] = variant.default_code
        if variant.default_code:
            vals['barcode'] = variant.barcode
        return {'vals': vals, 'state': state}

    def _create_product_line(self, variant, template_id, store_id, location_id,channel_id):
        prod_env = self.env['product.product']
        context = dict(self._context or {})
        context.update({'channel_id': channel_id.id})
        context.update({'channel': channel_id.channel})

        message = ''
        variant_id = variant.store_id or 'No Variants'
        exists = channel_id.match_product_mappings(
            store_id, variant_id, default_code=variant.default_code, barcode=variant.barcode)
        if not exists:
            vals = {
                'name': template_id.name,
                'description': template_id.description,
                'description_sale': template_id.description_sale,
                'type': template_id.type,
                'categ_id': template_id.categ_id.id,
                'uom_id': template_id.uom_id.id,
                'uom_po_id': template_id.uom_po_id.id,
                'product_tmpl_id': template_id.id,
                'default_code':variant.default_code,
                'barcode':variant.barcode,
            }
            attribute_value_ids = prod_env.with_context(context).check_for_new_attrs(
                template_id, variant)
            vals.update({'attribute_value_ids': attribute_value_ids})
            res = self.get_variant_extra_values(template_id, variant,channel_id)
            state = res['state']
            vals.update(res['vals'])
            product_exists_odoo = channel_id.match_odoo_product(vals)
            if not product_exists_odoo:
                product_id = prod_env.with_context(context).create(vals)
                vals.pop('message_follower_ids','')
                status = True
                if variant.list_price and eval(variant.list_price):
                    price =parse_float(variant.list_price) #- template_id.list_price
                    self.wk_change_product_price(
                        product_id = product_id,
                        price = price,
                        channel_id = channel_id
                    )
                if variant.qty_available and eval(variant.qty_available) > 0:
                    self.wk_change_product_qty(
                        product_id, variant.qty_available, location_id)
                #FIX EXTRA FIELDS
                mapping_id = self.channel_id.create_product_mapping(
                    template_id, product_id, store_id, variant_id,
                    vals = dict(default_code = vals.get('default_code'),barcode=vals.get('barcode'))
                )
            else:
                product_exists_odoo.write(vals)
                product_id = product_exists_odoo
                mapping_id = channel_id.create_product_mapping(
                    product_id.product_tmpl_id, product_id, store_id, variant_id,
                    vals = dict(default_code=variant.default_code, barcode=variant.barcode)
                )
        else:
            mapping_id = exists
        return message

    def _create_product_lines(self, variant_ids, template_id, store_id, location_id,channel_id):
        attribute_line_obj = self.env['product.attribute.line']
        message = ''
        for variant_id in self.env['product.variant.feed'].browse(variant_ids):
            message += self._create_product_line(
                variant_id, template_id, store_id, location_id,channel_id)
        return message
    @api.model
    def wk_change_product_price(self, product_id, price, channel_id):

        pricelist_item = channel_id.pricelist_name.item_ids.filtered(
            lambda pitem:pitem.product_id.id == product_id.id
            and pitem.applied_on=='0_product_variant'
        )
        if pricelist_item:
            pricelist_item = pricelist_item[0]
            pricelist_item.write(dict(fixed_price=price))
        else:
            pricelist_item = self.env['product.pricelist.item'].create({
                'pricelist_id':channel_id.pricelist_name.id,
                'applied_on':'0_product_variant',
                'product_id': product_id.id,
                'fixed_price': (price),
            })

    @api.model
    def wk_change_product_qty(self, product_id, qty_available, location_id):
        if qty_available and product_id.type=='product':
            location_id = location_id and location_id or self.env.ref(
                'stock.stock_location_stock')
            inventory_wizard = self.env['stock.change.product.qty'].create({
                'product_id': product_id.id,
                'new_quantity': (qty_available),
                'location_id': location_id.id,
            })
            inventory_wizard.change_product_qty()

    def check_attribute_value(self,variant_ids):
        state, message= 'done',''

        for variant in variant_ids:
            name_values = eval(variant.name_value)
            cnt = Counter()
            for name_value in name_values:
                cnt[name_value.get('name')]+=1
            multi_occur = filter(lambda i:i[1]!=1,cnt.items())
            for multi_oc in multi_occur:
                state = 'error'
                items = map(lambda item:'%s(%s times)'%(item[0],item[1]),multi_occur)
                message += 'Attributes  are duplicate \n %r'%(','.join(items))
                return dict(message=message,state=state)
        return dict(message=message,state=state)

    @api.multi
    def import_product(self,channel_id):
        self.ensure_one()
        message = ""
        create_id = None
        update_id = None
        context = dict(self._context)
        context.update({
            'pricelist':channel_id.pricelist_name.id,
            'lang':channel_id.language_id.code,
        })
        vals = EL(self.read(self.get_product_fields()))
        store_id = vals.pop('store_id')

        state = 'done'
        if not vals.get('name'):
            message += "<br/>Product without name can't evaluated"
            state = 'error'
        if not store_id:
            message += "<br/>Product without store ID can't evaluated"
            state = 'error'
        categ_id = channel_id.default_category_id.id
        if categ_id:
            vals['categ_id'] = categ_id
        weight_unit = vals.pop('weight_unit')
        if weight_unit:
            uom_id = channel_id.get_uom_id(name=weight_unit).id
            if uom_id:
                vals['uom_id'] = uom_id
                vals['uom_po_id'] = uom_id

        dimensions_unit = vals.pop('dimensions_unit')
        if dimensions_unit:
            vals['dimensions_uom_id'] = channel_id.get_uom_id(
                name=dimensions_unit).id
        if not vals.pop('wk_product_id_type'):
            vals['wk_product_id_type'] = 'wk_upc'
        variant_lines = vals.pop('feed_variants')
        feed_variants = self.feed_variants
        if variant_lines:
            check_attr = self.check_attribute_value(feed_variants)
            state = check_attr.get('state')
            message+=check_attr.get('message')
        qty_available = vals.pop('qty_available')
        list_price = vals.pop('list_price')
        list_price = list_price and parse_float(list_price) or 0
        image_url = vals.pop('image_url')
        location_id = channel_id.location_id
        if not vals.get('image') and image_url and (image_url not in ['false','False',False]):
            image_res = channel_id.read_website_image_url(image_url)
            if image_res:vals['image'] = image_res
        match = channel_id.match_template_mappings(store_id, **vals)
        template_exists_odoo = channel_id.match_odoo_template(
            vals ,variant_lines=feed_variants)
        vals.pop('website_message_ids','')
        vals.pop('message_follower_ids','')

        if state == 'done':
            if match:
                extra_categ_ids = vals.pop('extra_categ_ids')
                if not template_exists_odoo:
                    template_id = match.template_name
                    template_id.with_context(context).write(vals)
                else:
                    template_exists_odoo.with_context(context).write(vals)
                    template_id = template_exists_odoo
                match.write({'default_code':vals.get('default_code'),'barcode':vals.get('barcode')})
                extra_categ = self.env['extra.categories'].search([('instance_id','=',channel_id.id), ('product_id','=', template_id.id)])
                if extra_categ_ids:
                    res = self.get_extra_categ_ids(extra_categ_ids,channel_id)
                    message += res.get('message', '')
                    categ_ids = res.get('categ_ids')
                    if categ_ids:
                        # code for instance wise category ids
                        data = {
                        'extra_category_ids' : [(6, 0, categ_ids)],
                        'instance_id' : channel_id.id,
                        'category_id':categ_id,
                        }
                        extra_categ = extra_categ.with_context(context).write(data)
                    else:
                        state = 'error'
                if len(variant_lines):
                    context['wk_qty_update']=False
                    res = self.with_context(context).update_product_variants(
                        variant_lines, template_id, store_id, location_id,channel_id)
                    if res:
                        message += res
                        state = 'error'
                else:
                    for variant_id in template_id.product_variant_ids:
                        variant_vals = variant_id.read(['default_code','barcode'])[0]
                        self.wk_change_product_price(
                            product_id=variant_id,
                            price = list_price,
                            channel_id = channel_id
                        )
                        # if qty_available and eval(qty_available) > 0:
                        #     self.wk_change_product_qty(
                        #         variant_id, qty_available, location_id)
                        match_product = channel_id.match_product_mappings(
                            store_id, 'No Variants', default_code=variant_vals.get('default_code'), barcode=variant_vals.get('barcode'))
                        if not match_product:
                            channel_id.create_product_mapping(
                                template_id, variant_id, store_id, 'No Variants',
                                 {'default_code': variant_vals.get('default_code'),
                                        'barcode':variant_vals.get('barcode')})
                update_id = match

            else:
                template_id = None
                try:
                    vals['taxes_id'] = None
                    vals['supplier_taxes_id'] = None
                    if not template_exists_odoo:
                        if variant_lines:
                            context['create_product_product']=1
                        extra_categ_ids = vals.pop('extra_categ_ids')
                        if extra_categ_ids:
                            res = self.get_extra_categ_ids(extra_categ_ids,channel_id)
                            message += res.get('message', '')
                            categ_ids = res.get('categ_ids')
                            if categ_ids:
                                # code for instance wise category ids
                                data = {
                                'extra_category_ids' : [(6, 0, categ_ids)],
                                'instance_id' : channel_id.id,
                                'category_id':categ_id,
                                }
                                extra_categ = self.env['extra.categories'].with_context(context).create(data)
                                vals['channel_category_ids'] = [(6, 0, [extra_categ.id])]
                            else:
                                state = 'error'
                        template_id = self.env['product.template'].with_context(context).create(vals)
                    else:
                        # template_exists_odoo.with_context(context).write(vals)
                        template_id = template_exists_odoo
                        extra_categ_ids = vals.pop('extra_categ_ids')
                        if extra_categ_ids:
                            res = self.get_extra_categ_ids(extra_categ_ids,channel_id)
                            message += res.get('message', '')
                            categ_ids = res.get('categ_ids')
                            if categ_ids:
                                # code for instance wise category ids
                                data = {
                                'extra_category_ids' : [(6, 0, categ_ids)],
                                'instance_id' : channel_id.id,
                                'category_id':categ_id,
                                }
                                template_id.channel_category_ids = [(0, 0, data)]
                            else:
                                state = 'error'

                    if len(variant_lines):
                        res = self._create_product_lines(
                            variant_lines, template_id, store_id, location_id,channel_id)
                        if res:
                            res += message
                            state = 'error'

                    else:
                        for variant_id in template_id.product_variant_ids:
                            variant_vals = variant_id.read(['default_code','barcode'])[0]
                            self.wk_change_product_price(
                                product_id =variant_id,
                                price = list_price,
                                channel_id = channel_id
                            )
                            if qty_available and eval(qty_available) > 0:
                                self.wk_change_product_qty(
                                    variant_id, qty_available, location_id)
                            match = channel_id.match_product_mappings(
                                store_id, 'No Variants', default_code=variant_vals.get('default_code'), barcode=variant_vals.get('barcode'))
                            if not match:
                                channel_id.create_product_mapping(
                                    template_id, variant_id, store_id, 'No Variants',
                                     {'default_code': variant_vals.get('default_code'),
                                            'barcode':variant_vals.get('barcode')})
                except Exception as e:
                    _logger.error('----------Exception------------%r', e)
                    message += '<br/>Error in variants %s' % (e)
                    state = 'error'
                if state == 'done':
                    template_id = template_id and template_id or template_exists_odoo
                    if template_id:
                        create_id = channel_id.create_template_mapping(
                            template_id, store_id,
                             {'default_code': vals.get('default_code'), 'barcode': vals.get('barcode')})

                elif template_id:
                    template_id.unlink()
            if state == 'done':
                message += '<br/> Product %s Successfully Evaluate' % (
                    vals.get('name', ''))
        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (self.message, message)
        return dict(
            update_id=update_id,
            create_id=create_id,
            message=message
        )

    @api.multi
    def import_items(self):
        update_ids = []
        create_ids = []

        message = ''

        for record in self:
            sync_vals = dict(
                status='error',
                action_on='template',
                action_type='import',
            )
            channel_id=record.channel_id
            res = record.import_product(channel_id)
            msz = res.get('message', '')
            message += msz
            update_id = res.get('update_id')
            if update_id:
                update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:
                create_ids.append(create_id)
            mapping_id = update_id or create_id
            if mapping_id:
                mapping_vals= mapping_id.read(['store_product_id','odoo_template_id'])[0]
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] =mapping_vals.get('store_product_id')
                sync_vals['odoo_id'] = mapping_vals.get('odoo_template_id')
            sync_vals['summary'] = msz
            record.channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
            return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        message = self.get_feed_result(feed_type='Product')
        return self.env['multi.channel.sale'].display_message(message)

    @api.model
    def cron_import_product(self):
        domain = [
            ('state', '!=', 'done')
        ]
        for record in self.search(domain):
            record.import_product(record.channel_id)
        return True
