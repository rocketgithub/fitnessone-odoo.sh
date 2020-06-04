#-*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import copy
from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, ValidationError  ,Warning
from odoo.addons.odoo_multi_channel_sale.tools import parse_float, extract_list as EL
import logging
_logger = logging.getLogger(__name__)
Fields = [
    'name',
    'store_id',
    'store_source',
]
PartnerFields = Fields + [
    'email',
    'phone',
    'mobile',
    'website',
    'last_name',
    'street',
    'street2',
    'city',
    'zip',
    'state_id',
    'state_name',
    'country_id',
    'type',
    'parent_id'
]
OrderFields = Fields + [
    'partner_id',
    'order_state',
    'carrier_id',

    'date_invoice',
    # 'min_date',
    'date_order',
    'confirmation_date',

    'line_ids',
    'line_name',
    'line_price_unit',
    'line_product_id',
    'line_product_default_code',
    'line_product_barcode',
    'line_variant_ids',
    'line_source',
    'line_product_uom_qty',
    'line_taxes',
]

LineType = [
    ('single', 'Single Order Line'),
    ('multi', 'Multi Order Line')
]
LineSource = [
    ('product','Product'),
    ('delivery','Delivery'),
    ('discount','Discount'),
]
PartnerType = [
    ('contact','Contact'),
    ('invoice','Invoice'),
    ('delivery','Delivery'),
]

class PartnerFeed(models.Model):
    _name = "partner.feed"
    _inherit = ["wk.feed"]
    email = fields.Char(
        string='Email'
    )
    phone = fields.Char(
        string='Phone'
    )
    mobile = fields.Char(
        string='Mobile'
    )
    website = fields.Char(
        string='Website URL'
    )
    last_name = fields.Char(
        string='Last Name'
    )
    street = fields.Char(
        string='Street'
    )
    street2 = fields.Char(
        string='street2'
    )

    city = fields.Char(
        string='City'
    )
    zip = fields.Char(
        string='Zip'
    )
    state_name = fields.Char(
        string='State Name'
    )
    state_id = fields.Char(
        string='State Code'
    )
    country_id = fields.Char(
        string='Country Code'
    )
    type = fields.Selection(
        selection = PartnerType,
        default='contact',
        required=1
    )
    parent_id = fields.Char(
        string='Store Parent ID'
    )

    def import_partner(self,channel_id):

        message = ""
        state = 'done'
        update_id = None
        create_id=None
        self.ensure_one()
        vals = EL(self.read(PartnerFields))
        _type =vals.get('type')
        store_id = vals.pop('store_id')
        vals.pop('website_message_ids','')
        vals.pop('message_follower_ids','')
        match = channel_id.match_partner_mappings(store_id,_type)
        name = vals.pop('name')
        if not name:
            message+="<br/>Partner without name can't evaluated."
            state = 'error'
        if not store_id:
            message+="<br/>Partner without store id can't evaluated."
            state = 'error'
        parent_store_id = vals['parent_id']
        if parent_store_id:
            partner_res = self.get_partner_id(parent_store_id,channel_id=channel_id)
            message += partner_res.get('message')
            partner_id = partner_res.get('partner_id')
            if partner_id:
                vals['parent_id'] =partner_id.id
            else:
                state = 'error'
        if state == 'done':
            country_id = vals.pop('country_id')
            if country_id:
                country_id = channel_id.get_country_id(country_id)
                if country_id:
                    vals['country_id'] = country_id.id
            state_id = vals.pop('state_id')
            state_name = vals.pop('state_name')

            if (state_id or state_name) and country_id:
                state_id = channel_id.get_state_id(state_id,country_id,state_name)
                if state_id:
                    vals['state_id'] = state_id.id
            last_name = vals.pop('last_name','')
            if last_name:
                vals['name'] = "%s %s" % (name, last_name)
            else:
                vals['name'] =name
        if match:
            if  state =='done' :
                try:
                    match.odoo_partner.write(vals)
                    message +='<br/> Partner %s successfully updated'%(name)
                except Exception as e:
                    message += '<br/>%s' % (e)
                    state = 'error'
                update_id = match

            elif state =='error':
                message+='Error while partner updated.'

        else:
            if state == 'done':
                try:
                    erp_id = self.env['res.partner'].create(vals)
                    create_id =  channel_id.create_partner_mapping(erp_id, store_id,_type)
                    message += '<br/>Partner %s successfully evaluated.'%(name)
                except Exception as e:
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
        update_ids=[]
        create_ids=[]
        message = ''

        for record in self:
            channel_id = record.channel_id
            sync_vals = dict(
            status ='error',
            action_on ='customer',
            action_type ='import',
            )
            res = record.import_partner(channel_id)
            msz= res.get('message', '')
            message+=msz
            update_id = res.get('update_id')
            if update_id:update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:create_ids.append(create_id)
            mapping_id = update_id or create_id
            if mapping_id:
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] = mapping_id.store_customer_id
                sync_vals['odoo_id'] = mapping_id.odoo_partner_id
            sync_vals['summary'] = msz
            record.channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
             return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        message = self.get_feed_result(feed_type='Partner')
        return self.env['multi.channel.sale'].display_message(message)

    @api.model
    def cron_import_partner(self):
        domain = [
            ('state','!=','done')
        ]
        for record in self.search(domain):
            record.import_partner(record.channel_id)
        return True


class OrderLineFeed(models.Model):
    _name = "order.line.feed"
    line_name = fields.Char(
        string='Product Name',
    )

    line_product_uom_qty = fields.Char(
        string='Quantity',
    )
    line_price_unit = fields.Char(
        string='Price',
    )
    line_product_id = fields.Char(
        string='Product ID',
    )
    line_product_default_code = fields.Char(
        string='Default Code',
    )
    line_product_barcode = fields.Char(
        string='Barcode',
    )
    line_source = fields.Selection(
        selection = LineSource,
        default='product',
        required=True
    )
    order_feed_id = fields.Many2one(
        string='Order Feed ID',
        comodel_name='order.feed'
    )
    line_taxes = fields.Text(string="Taxes")
    line_variant_ids = fields.Char(
        string='Variant ID',
        default='No Variants',
        help="""Attribute should  place in comma separated like color:red,color:blue,size:8,size:10"""
    )


class OrderFeed(models.Model):
    _name = "order.feed"
    _description = "Order Feed"
    _inherit = [
        "wk.feed",
        "order.line.feed",

    ]

    partner_id = fields.Char(
        string='Store Customer ID',
    )
    order_state = fields.Char(
        string = 'Order State'
    )
    date_order = fields.Char(
        string = 'Order Date'
    )
    confirmation_date = fields.Char(
        string = 'Confirmation Date'
    )
    date_invoice = fields.Char(
        string = 'Invoice Date'
    )
    # min_date = fields.Char(
    #     string = 'Confirmation State'
    # )
    carrier_id = fields.Char(
        string='Delivery Method',
        help = 'Delivery Method Name',
    )
    line_type = fields.Selection(
        selection=LineType,
        default='single',
        string='Line Type',
    )
    line_ids = fields.One2many(
        string='Line Ids',
        comodel_name='order.line.feed',
        inverse_name='order_feed_id'
    )
    payment_method = fields.Char(
        string='Payment Method',
        help = 'Payment Method Name',
    )
    currency = fields.Char(
        string='Currency Name',
    )
    customer_is_guest = fields.Boolean(
        string = 'Customer Is Guest',
    )
    customer_name=fields.Char(
        string='Customer Name'
    )
    customer_phone=fields.Char(
        string='Customer Phone'
    )
    customer_mobile=fields.Char(
        string='Customer Mobile'
    )
    customer_last_name=fields.Char(
        string='Customer Last Name'
    )
    customer_email = fields.Char(
        string='Customer Email'
    )

    same_shipping_billing = fields.Boolean(
        string = 'Shipping Address Same As Billing',
        default=True
    )
    shipping_partner_id = fields.Char(
        string='Shipping Partner ID'
    )
    shipping_name = fields.Char(
        string='Name'
    )
    shipping_last_name=fields.Char(
        string='Last Name'
    )
    shipping_email = fields.Char(
        string='Email'
    )
    shipping_phone = fields.Char(
        string='Phone'
    )
    shipping_mobile = fields.Char(
        string='Mobile'
    )

    shipping_street = fields.Char(
        string='Street'
    )
    shipping_street2 = fields.Char(
        string='street2'
    )

    shipping_city = fields.Char(
        string='City'
    )
    shipping_zip = fields.Char(
        string='Zip Code'
    )
    shipping_state_name = fields.Char(
        string='State Name'
    )
    shipping_state_id = fields.Char(
        string='State Code'
    )
    shipping_country_id = fields.Char(
        string='Country Code'
    )
    invoice_partner_id = fields.Char(
        string='Invoice Partner ID'
    )
    invoice_name = fields.Char(
        string='Name'
    )
    invoice_last_name=fields.Char(
        string='Last Name'
    )
    invoice_email = fields.Char(
            string='Email'
    )
    invoice_phone = fields.Char(
            string='Phone'
    )
    invoice_mobile = fields.Char(
            string='Mobile'
    )

    invoice_street = fields.Char(
            string='Street'
    )
    invoice_street2 = fields.Char(
            string='street2'
    )
    invoice_city = fields.Char(
            string='City'
    )
    invoice_zip = fields.Char(
            string='Zip Code'
    )
    invoice_state_name = fields.Char(
            string='State Name'
    )
    invoice_state_id = fields.Char(
            string='State Code'
    )
    invoice_country_id = fields.Char(
            string='Country Code'
    )

    @api.model
    def _get_order_line_vals(self, vals,carrier_id,channel_id):
        message = ''
        status=True
        lines = []
        line_ids = vals.pop('line_ids')
        line_name = vals.pop('line_name')
        line_price_unit = vals.pop('line_price_unit')
        if line_price_unit:line_price_unit = parse_float(line_price_unit)
        line_product_id = vals.pop('line_product_id')
        line_variant_ids = vals.pop('line_variant_ids')
        line_product_uom_qty = vals.pop('line_product_uom_qty')
        line_product_default_code = vals.pop('line_product_default_code')
        line_source = vals.pop('line_source')
        line_product_barcode = vals.pop('line_product_barcode')
        line_taxes = vals.pop('line_taxes')
        if line_ids:
            for line_id in self.env['order.line.feed'].browse(line_ids):
                line_price_unit = line_id.line_price_unit
                if line_price_unit:line_price_unit = parse_float(line_price_unit)
                if line_id.line_source =='delivery':
                    product_id = carrier_id.product_id
                elif line_id.line_source =='discount':
                    if not channel_id.discount_product_id:
                        product_id  =channel_id.create_product('discount')
                        channel_id.discount_product_id = product_id.id
                    product_id = channel_id.discount_product_id
                    line_price_unit = -line_price_unit
                elif line_id.line_source =='product':
                    product_res = self.get_product_id(
                        line_id.line_product_id,
                        line_id.line_variant_ids or 'No Variants',
                        channel_id,
                        line_id.line_product_default_code,
                        line_id.line_product_barcode,

                    )
                    product_id = product_res.get('product_id')
                    if product_res.get('message'):
                        _logger.error("OrderLineError1 %r"%product_res)
                        message += product_res.get('message')
                if product_id:
                    product_uom_id = product_id.uom_id.id
                    line = dict(
                        name=line_id.line_name,
                        price_unit=line_price_unit,
                        product_id=product_id.id,
                        product_uom_qty=line_id.line_product_uom_qty,
                        is_delivery = line_id.line_source =='delivery',
                        product_uom=product_uom_id,
                    )
                    line['tax_id'] = self.get_taxes_ids(line_id.line_taxes,channel_id)
                    ####ADD TAX
                    lines += [(0, 0, line)]
                else:
                    status=False
        else:
            product_res = self.get_product_id(
                line_product_id,
                line_variant_ids or 'No Variants',
                channel_id,
                line_product_default_code,
                line_product_barcode,

            )
            product_id = product_res.get('product_id')
            if product_res.get('message'):
                _logger.error("OrderLineError2 %r"%product_res)
                message += product_res.get('message')
            if product_id:
                if line_product_uom_qty:line_product_uom_qty = parse_float(line_product_uom_qty) or 1
                line = dict(
                    name=line_name or '',
                    price_unit=(line_price_unit),
                    product_id=product_id.id,
                    is_delivery = line_source =='delivery',
                    product_uom_qty=(line_product_uom_qty),
                    product_uom=product_id.uom_id.id ,
                )
                line['tax_id'] = self.get_taxes_ids(line_taxes,channel_id)
                ####ADD TAX
                lines += [(0, 0, line)]
            else:
                status=False
        return dict(
            message=message,
            order_line=lines,
            status =status

        )

    @api.multi
    def  get_taxes_ids(self, line_taxes,channel_id):
        if line_taxes:
            line_taxes=eval(line_taxes)
            if line_taxes:
                tax_record=self.env['account.tax']
                tax_mapping_obj= self.env['channel.account.mappings']
                tax_list=[]
                domain=[]
                channel=str(self.channel)
                for tax in line_taxes:
                    name=""
                    tax_type="percent"
                    inclusive=False
                    if tax.get('name'):
                        name = tax['name']
                    else:
                        name = channel+"_"+str(channel_id.id)+"_"+str(float(tax['rate']))
                    if tax.get('include_in_price'):
                        inclusive=tax['include_in_price']
                        # domain += [('include_in_price','=',tax['include_in_price'])]
                    if tax.get('tax_type'):
                        tax_type=tax['tax_type']
                        domain += [('tax_type','=',tax['tax_type'])]
                    domain += [('store_tax_value_id','=',(tax['rate']))]
                    tax_rec = channel_id._match_mapping(tax_mapping_obj, domain)
                    if tax_rec:
                        # tax_rec.tax_name.price_include = inclusive
                        tax_list.append(tax_rec.tax_name.id)
                    else:
                        tax_dict={
                          'name'            : name,
                          'amount_type'     : tax_type,
                          'price_include'   : inclusive,
                          'amount'          : float(tax['rate']),
                        }
                        tax_id = tax_record.search([('name','=',tax_dict['name'])])
                        if not tax_id:
                            tax_id=tax_record.create(tax_dict)
                        tax_map_vals={
                          'channel_id'      : channel_id.id,
                          'tax_name'        : tax_id.id,
                          'store_tax_value_id' : tax_id.amount,
                          'tax_type'        : tax_id.amount_type,
                          'include_in_price': tax_id.price_include,
                          'odoo_tax_id'     : tax_id.id,
                        }
                        channel_id._create_mapping(tax_mapping_obj,tax_map_vals)
                        tax_list.append(tax_id.id)
                return [(6,0,tax_list)]
        return False
    @api.model
    def get_order_date_info(self,channel_id,vals):
        date_order = None
        confirmation_date = None
        date_invoice = None
        date_order_res =  channel_id.om_format_date_time(vals.pop('date_order'))
        if date_order_res.get('om_date_time'):
            date_order = date_order_res.get('om_date_time')

        confirmation_date_res =  channel_id.om_format_date_time(vals.pop('confirmation_date'))
        if confirmation_date_res.get('om_date_time'):
            confirmation_date = confirmation_date_res.get('om_date_time')

        date_invoice_res =  channel_id.om_format_date(vals.pop('date_invoice'))
        if date_invoice_res.get('om_date'):
            date_invoice = date_invoice_res.get('om_date')
        return dict(
            date_order = date_order,
            confirmation_date = confirmation_date,
            date_invoice = date_invoice,
        )

    @api.model
    def get_order_fields(self):
        return copy.deepcopy(OrderFields)

    @api.multi
    def import_order(self,channel_id):
        message = ""
        update_id=None
        create_id=None
        self.ensure_one()
        vals = EL(self.read(self.get_order_fields()))
        store_id = vals.pop('store_id')

        store_source = vals.pop('store_source')
        match = channel_id.match_order_mappings(store_id)
        state = 'done'
        store_partner_id = vals.pop('partner_id')


        date_info = self.get_order_date_info(channel_id,vals)
        if date_info.get('date_order'):
            vals['date_order']=date_info.get('date_order')
        if date_info.get('confirmation_date'):
            vals['confirmation_date']= date_info.get('confirmation_date')
        date_invoice =  date_info.get('date_invoice')

        if store_partner_id:
            res_partner = self.get_order_partner_id(store_partner_id,channel_id)
            message += res_partner.get('message', '')
            partner_id = res_partner.get('partner_id')
            partner_invoice_id = res_partner.get('partner_invoice_id')
            partner_shipping_id = res_partner.get('partner_shipping_id')
            if partner_id and partner_invoice_id and partner_shipping_id:
                vals['partner_id'] = partner_id.id
                vals['partner_invoice_id'] = partner_invoice_id.id
                vals['partner_shipping_id'] = partner_shipping_id.id
            else:
                message += '<br/>Partner, Invoice, Shipping Address must present.'
                state = 'error'
                _logger.error('#OrderError1 %r'%message)
        else:
            message += '<br/>No partner in sale order data.'
            state = 'error'
            _logger.error('#OrderError2 %r'%message)


        if state=='done':
            carrier_id = vals.pop('carrier_id','')

            if carrier_id:
                carrier_res = self.get_carrier_id(carrier_id,channel_id=channel_id)
                message += carrier_res.get('message')
                carrier_id = carrier_res.get('carrier_id')
                if carrier_id:
                    vals['carrier_id'] = carrier_id.id
            order_line_res = self._get_order_line_vals(vals,carrier_id,channel_id)
            message += order_line_res.get('message', '')
            if not order_line_res.get('status'):
                state = 'error'
                _logger.error('#OrderError3 %r'%order_line_res)
            else:
                order_line = order_line_res.get('order_line')
                if len(order_line):
                    vals['order_line'] = order_line
                    state = 'done'
        currency=self.currency

        if state=='done' and currency:
            currency_id = channel_id.get_currency_id(currency)
            if not currency_id:
                message += '<br/> Currency %s no active in Odoo'%(currency)
                state = 'error'
                _logger.error('#OrderError4 %r'%message)
            else:
                pricelist_id = channel_id.match_create_pricelist_id(currency_id)
                vals['pricelist_id']=pricelist_id.id

        vals.pop('name')
        vals.pop('id')
        vals.pop('website_message_ids','')
        vals.pop('message_follower_ids','')
        vals['team_id'] = channel_id.crm_team_id.id
        vals['warehouse_id'] = channel_id.warehouse_id.id


        if match and match.order_name:
            if  state =='done' :
                try:

                    order_state = vals.pop('order_state')
                    if match.order_name.state=='draft':
                        match.order_name.write(dict(order_line=[(5,0)]))
                        match.order_name.write(vals)
                        message +='<br/> Order %s successfully updated'%(vals.get('name',''))
                    else:
                        message+='Only order state can be update as order not in draft state.'
                    message += self.env['multi.channel.skeleton']._SetOdooOrderState(match.order_name, channel_id,
                            order_state, self.payment_method,date_invoice=date_invoice)
                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError5  %r'%message)
                    state = 'error'
                update_id = match
            elif state =='error':
                message+='<br/>Error while order update.'
        else:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    erp_id = self.env['sale.order'].create(vals)
                    message += self.env['multi.channel.skeleton']._SetOdooOrderState(erp_id, channel_id,  order_state, self.payment_method,date_invoice=date_invoice)
                    message  += '<br/> Order %s successfully evaluated'%(self.store_id)
                    create_id =  channel_id.create_order_mapping(erp_id, store_id,store_source)

                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError6 %r'%message)
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
        update_ids=[]
        create_ids=[]
        message=''
        for record in self:
            channel_id = record.channel_id
            sync_vals = dict(
            status ='error',
            action_on ='order',
            action_type ='import',
            )
            res = record.import_order(channel_id)
            msz= res.get('message', '')
            message+=msz
            update_id = res.get('update_id')
            if update_id:update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:create_ids.append(create_id)
            mapping_id = update_id or create_id
            if mapping_id:
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] = mapping_id.store_order_id
                sync_vals['odoo_id'] = mapping_id.odoo_order_id
            sync_vals['summary'] = msz
            channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
             return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        message =  self.get_feed_result(feed_type='Sale Order')
        return self.env['multi.channel.sale'].display_message(message)

    @api.model
    def cron_import_order(self):
        domain = [
            ('state','!=','done')
        ]
        for record in self.search(domain):
            record.import_order(record.channel_id)
        return True
