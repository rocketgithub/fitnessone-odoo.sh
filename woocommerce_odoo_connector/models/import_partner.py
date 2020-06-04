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
	def import_woocommerce_customers(self):
		message = ''
		list_customer = []
		count = 0
		woocommerce = self.get_woocommerce_connection()
		partner_feed_data = self.env['partner.feed']
		date = self.with_context({'name':'customer'}).get_woocommerce_import_date()
		if not date:
			return self.display_message("Please set date in multi channel configuration")
		try:
			partner_data = woocommerce.get('customers?after='+date).json()
		except Exception as e:
			raise UserError(_("Error : "+str(e)))
		if 'message' in partner_data:
			raise UserError(_("Error : "+str(partner_data['message'])))
		else :
			for partner in partner_data:
				if not partner_feed_data.search([('store_id','=',partner['id']),('channel_id.id','=',self.id)]):
					count = count +1
					partner_dict = {
								'name'		: partner['first_name'],
								'last_name'	: partner['last_name'],
								'channel_id': self.id,
								'email'		: partner['email'],
								'store_id'	: partner['id'],
					}
					partner_rec = partner_feed_data.create(partner_dict)
					self._cr.commit()
					list_customer.append(partner_rec)
			feed_res = dict(create_ids = list_customer,update_ids = [])
			self.env['channel.operation'].post_feed_import_process(self, feed_res)
			self.import_customer_date = str(datetime.now().date())
			message +=  str(count)+" Customer(s) Imported!"
			return self.display_message(message)


	@api.multi
	def import_all_woocommerce_customers(self):
		message = ''
		list_customer = []
		count = 0
		woocommerce = self.get_woocommerce_connection()
		partner_feed_data = self.env['partner.feed']
		try:
			i=1
			while(i):
				partner_data = woocommerce.get('customers?page='+str(i)).json()
				if 'message' in partner_data:
					raise UserError(_("Error : "+str(partner_data['message'])))
				else :
					if partner_data:
						i=i+1
						for partner in partner_data:
							if not partner_feed_data.search([('store_id','=',partner['id']),('channel_id.id','=',self.id)]):
								count = count +1
								partner_dict = {
											'name'		: partner['first_name'],
											'last_name'	: partner['last_name'],
											'channel_id': self.id,
											'email'		: partner['email'],
											'store_id'	: partner['id'],
								}
								partner_rec = partner_feed_data.create(partner_dict)
								self._cr.commit()
								list_customer.append(partner_rec)
					else:
						i=0
			feed_res = dict(create_ids = list_customer,update_ids = [])
			self.env['channel.operation'].post_feed_import_process(self, feed_res)
			# self.import_customer_date = str(datetime.now().date())
			message +=  str(count)+" Customer(s) Imported!"
			return self.display_message(message)
		except Exception as e:
			raise UserError(_("Error : "+str(e)))