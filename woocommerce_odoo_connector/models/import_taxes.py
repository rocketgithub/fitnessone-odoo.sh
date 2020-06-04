#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,fields,models
from woocommerce import API
from odoo.tools.translate import _
from datetime import datetime,timedelta
from odoo.exceptions import UserError
import logging
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')
class MultiChannelSale(models.Model):
    _inherit = "multi.channel.sale"

    @api.multi
    def woc_check_and_create_tax(self,woocommerce):
        if woocommerce:
            i = 1
            while(i):
                try:
                    taxes = woocommerce.get("taxes?page="+str(i)).json()
                except Exception as e:
                    raise UserError(_("Error : "+str(e)))
                if 'message' in taxes:
                    raise UserError(_("Error : "+str(taxes['message'])))
                else :
                    if taxes:
                        i+=1
                        tax_obj = self.env['account.tax']
                        tax_map_obj= self.env['channel.account.mappings']
                        tax_list=[]
                        domain=[]
                        channel=str(self.channel)
                        for tax in taxes:
                            check = tax_map_obj.search([('store_id','=',int(tax['id'])),('channel_id.id','=',self.id)])
                            tax_srch = tax_obj.search([('name', '=',tax['name'])])
                            tax_rate = float(tax['rate'])
                            if not check:
                                if tax_srch:
                                    tax_map_vals={
                                                'channel_id'        : self.id,
                                                'tax_name'          : tax_srch.id,
                                                'store_tax_value_id': str(tax_srch.amount),
                                                'tax_type'          : tax_srch.amount_type,
                                                'include_in_price'  : tax_srch.price_include,
                                                'odoo_tax_id'       : tax_srch.id,
                                                'store_id'          : tax['id'],
                                                }
                                    self._create_mapping(tax_map_obj,tax_map_vals) 
                                else:
                                    tax_dict={
                                            'name'            : tax['name'],
                                            'amount_type'     : 'percent',
                                            'price_include'   : False,
                                            'amount'          : tax_rate,
                                            }
                                    tax_rec = tax_obj.create(tax_dict)
                                    tax_map_vals={
                                                'channel_id'        : self.id,
                                                'tax_name'          : tax_rec.id,
                                                'store_tax_value_id': str(tax_rec.amount),
                                                'tax_type'          : tax_rec.amount_type,
                                                'include_in_price'  : tax_rec.price_include,
                                                'odoo_tax_id'       : tax_rec.id,
                                                'store_id'          : tax['id'],
                                                }
                                    self._create_mapping(tax_map_obj,tax_map_vals)

                            else:
                                amount = check.tax_name.amount
                                name = check.tax_name.name
                                if (name!= tax['name'] or amount != tax_rate):
                                    check.tax_name.amount = tax_rate
                                    check.tax_name.name = tax['name']
                    else:
                        i = 0

        return True


class OrderFeed(models.Model):
    _inherit = "order.feed"

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
                    flag = 0
                    if "id" in tax:
                        domain=[('channel_id','=',channel_id.id),('store_id','=',str(tax['id']))]
                        tax_rec = channel_id._match_mapping(tax_mapping_obj,domain )
                        if tax_rec:
                            tax_list.append(tax_rec.tax_name.id)
                            flag=1
                    if 'rate' in tax:
                        if not tax['rate'] == 0.0 and not flag:
                            domain=[]
                            name=""
                            tax_type="percent"
                            inclusive=False
                            if 'name' in tax:
                                name = tax['name']
                            else:
                                name = str(channel)+"_"+str(channel_id.id)+"_"+str(float(tax['rate']))
                            if 'include_in_price' in tax:
                                inclusive=tax['include_in_price']
                                # domain += [('include_in_price','=',tax['include_in_price'])]
                            if 'type' in tax:
                                tax_type=tax['type']
                                domain += [('tax_type','=',tax['type'])]
                            domain += [('store_tax_value_id','=',(tax['rate']))]
                            tax_rec = channel_id._match_mapping(tax_mapping_obj, domain)
                            tax_rate = float(tax['rate'])
                            if tax_rec:
                                # tax_rec.tax_name.price_include = inclusive
                                tax_list.append(tax_rec.tax_name.id)
                            else:
                                tax_dict={
                                'name'            : name,
                                'amount_type'     : tax_type,
                                'price_include'   : inclusive,
                                'amount'          : tax_rate,
                                }
                                tax_id = tax_record.search([('name','=',tax_dict['name'])])
                                if not tax_id:
                                    tax_id=tax_record.create(tax_dict)
                                    tax_map_vals={
                                    'channel_id'      : channel_id.id,
                                    'tax_name'        : tax_id.id,
                                    'store_tax_value_id' : str(tax_id.amount),
                                    'tax_type'        : tax_id.amount_type,
                                    'include_in_price': tax_id.price_include,
                                    'odoo_tax_id'     : tax_id.id,
                                    }
                                    channel_id._create_mapping(tax_mapping_obj,tax_map_vals)
                                tax_list.append(tax_id.id)
                return [(6,0,tax_list)]
        return False