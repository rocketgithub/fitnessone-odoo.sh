#-*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, ValidationError, Warning
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
import logging
_logger = logging.getLogger(__name__)

ShippingFields = [
    'name',
    'shipping_carrier',
    'description',
    'is_international',
    'description',
    'store_id',
]


class ShippingFeed(models.Model):
    _name = "shipping.feed"
    _inherit = ["wk.feed"]

    description = fields.Text(
        string='Description',
    )
    shipping_carrier = fields.Char(
        string='Shipping Carrier',
    )
    is_international = fields.Boolean('Is International')

    @api.model
    def get_shipping_fields(self):
        return ShippingFields

    @api.model
    def get_shiping_carrier(self, carrier_name,channel_id=None):
        carrier_obj = self.env['delivery.carrier']
        partner_id = self.env.user.company_id.partner_id.id
        exists = carrier_obj.search([('name', '=', carrier_name)])
        channel_id = channel_id or self.channel_id
        data = {
            'product_type': 'service',
            'name': carrier_name,
            'fixed_price':0,
            'product_id' :channel_id.delivery_product_id.id
        }
        if not exists:
            carrier_id = carrier_obj.create(data)
        else:
            carrier_id = exists
        return carrier_id

    def get_shiping_carrier_mapping(self, channel_id, shipping_service_id):
        mapping_id = channel_id.match_carrier_mappings(shipping_service_id)
        if mapping_id:
            return mapping_id
        else:
            carrier_id = self.get_shiping_carrier(shipping_service_id,channel_id)
            vals = dict(
                name=shipping_service_id,
                store_id=shipping_service_id
            )
            return self.create_shipping_mapping(channel_id, carrier_id.id, vals)

    @api.model
    def create_shipping_mapping(self, channel_id, carrier_id, vals):
        vals = dict(
            channel_id=channel_id.id,
            ecom_store=channel_id.channel,
            odoo_carrier_id=carrier_id,
            odoo_shipping_carrier=carrier_id,
            shipping_service=vals.get('name'),
            international_shipping=vals.get('international_shipping'),
            shipping_service_id=vals.get('store_id'),
        )
        return self.env['channel.shipping.mappings'].create(vals)

    @api.multi
    def import_item(self):
        self.ensure_one()
        message = ""
        mapping_id = None
        update_id = None
        create_id = None
        channel_domain = self.get_channel_domain()
        vals = EL(self.read(self.get_shipping_fields()))
        state = 'done'
        carrier_id = False
        shipping_carrier = vals.pop('shipping_carrier')
        map_domain = channel_domain + \
            [('shipping_service_id', '=', vals.get('store_id'))]
        match = self.env['channel.shipping.mappings'].search(
            map_domain, limit=1)
        if not vals.get('name'):
            message += "<br/>Shipping Method without name can't evaluated"
            state = 'error'
        if not vals.get('store_id'):
            message += "<br/>Shipping Method without store ID can't evaluated"
            state = 'error'
        if not shipping_carrier:
            message += "<br/>Shipping Method without shipping carrier can't evaluated"
            state = 'error'
        try:
            carrier_id = self.get_shiping_carrier(shipping_carrier).id
        except Exception as e:
            state = 'error'
            message += '<br/> Error in evaluating Shipping carrier %s' % (
                vals.get('name', ''))


        if state == 'done':
            if not match:
                mapping_id = self.create_shipping_mapping(
                    self.channel_id, carrier_id, vals)
                message += '<br/> Shipping carrier %s Successfully Evaluated' % (
                    vals.get('name', ''))
                create_id = mapping_id
            else:
                res = match.write(vals)
                mapping_id = match
                update_id = mapping_id
                if res:
                    message += 'Some Shipping carriers have been updated'

        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (self.message, message)
        return dict(
            mapping_id=mapping_id,
            message=message,
            update_id=update_id,
            create_id=create_id
        )

    @api.multi
    def import_items(self):
        mapping_ids = []
        message = ''
        update_ids = []
        create_ids = []
        sync_vals = dict(
            status ='error',
            action_on ='shipping',
            action_type ='import',
        )
        for record in self:
            res = record.import_item()
            message += res.get('message', '')
            mapping_id = res.get('mapping_id')
            update_id = res.get('update_id')
            if update_id:
                update_ids.append(update_id)
            create_id = res.get('create_id')
            if create_id:
                create_ids.append(create_id)
            if mapping_id:
                mapping_ids += [mapping_id.id]
                sync_vals['status'] = 'success'
                sync_vals['ecomstore_refrence'] = mapping_id.shipping_service_id
                sync_vals['odoo_id'] = mapping_id.odoo_shipping_carrier
            sync_vals['summary'] = message
            record.channel_id._create_sync(sync_vals)
        if self._context.get('get_mapping_ids'):
            return dict(
                update_ids=update_ids,
                create_ids=create_ids,
            )
        return self.env['multi.channel.sale'].display_message(message)
