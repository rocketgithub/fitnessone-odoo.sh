#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,fields,models
from odoo.tools.translate import _
from datetime import datetime,timedelta
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
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
	def update_woocommerce_customers(self):
		update_rec = []
		count = 0
		woocommerce = self.get_woocommerce_connection()
		partner_feed_data = self.env['partner.feed']
		records = self.env['channel.partner.mappings'].search([('type','=','contact'),('channel_id.id','=',self.id)])
		id_string = []
		idstr =''
		i=0
		for record in records:
			idstr+=str(record.store_customer_id)+','
			i +=1
			if i==10:
				id_string.append(idstr)
				i=0
				idstr=''
		if idstr not in id_string:
			id_string.append(idstr)
		for id_str in id_string:
			try:
				partner_data = woocommerce.get('customers?include='+id_str).json()
			except Exception as e:
				raise UserError(_("Error : "+str(e)))
			if 'message' in partner_data:
				raise UserError(_("Error : "+str(partner_data['message'])))
			else :
				for partner in partner_data:
					update_record = self.env['partner.feed'].search([('store_id','=',partner['id']),('type','=','contact'),('channel_id.id','=',self.id)])
					if update_record:
						count += 1
						update_record.state = 'update'
						partner_dict = {
									'name'		: partner['first_name'],
									'last_name'	: partner['last_name'],
									'channel_id': self.id,
									'email'		: partner['email'],
									'store_id'	: partner['id']
						}
						update_record.write(partner_dict)
						update_rec.append(update_record)
					else:
						count = count +1
						partner_dict = {
									'name'		: partner['first_name'],
									'last_name'	: partner['last_name'],
									'channel_id': self.id,
									'email'		: partner['email'],
									'store_id'	: partner['id'],
						}
						partner_rec = partner_feed_data.create(partner_dict)
						partner_rec.state = 'update'
						self._cr.commit()
						update_rec.append(partner_rec)
		feed_res = dict(create_ids=[],update_ids=update_rec)
		self.env['channel.operation'].post_feed_import_process(self,feed_res)
		self.update_product_date = str(datetime.now().date())
		message = str(count)+" Customers(s) Updated!   "
		return self.display_message(message)
