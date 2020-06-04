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
	def create_or_get_woocommerce_voucher(self, vouchers):
		voucher_rec = self.env['product.feed'].search([('name','=','voucher')])
		if not voucher_rec:
			voucher_rec = self.create_woocommerce_voucher()
		voucher_list = []
		for voucher in vouchers:
			voucher_line = {
							'line_name'		  		: "Voucher",
							'line_price_unit' 		: -(float(voucher['amount'])),
							'line_product_uom_qty'  : 1,
							'line_product_id'		: voucher_rec.store_id,
							'line_source'			: 'discount'
			}
			voucher_list.append((0,0,voucher_line))
		return voucher_list

	@api.multi
	def create_woocommerce_voucher(self):
		data = {
				'name'		:"voucher",
				'store_id'	:"wc",
				'channel_id':self.id,
				'type'		:'service'
		}
		product_rec = self.env['product.feed'].create(data)
		feed_res = dict(create_ids=[product_rec],update_ids=[])
		self.env['channel.operation'].post_feed_import_process(self,feed_res)
		return product_rec


	@api.multi
	def create_or_get_woocommerce_shipping(self,shipping_line):
		shipping_rec = self.env['product.feed'].search([('name','=','shipping')])
		if not shipping_rec:
			shipping_rec = self.create_woocommerce_shipping()
		shipping_list = []
		for shipping in shipping_line:
			if float(shipping['total'])>0:
				tax = self.get_woocommerce_taxes(shipping['taxes'])
				shipping_line = {
								'line_name'		  		: "Shipping",
								'line_price_unit' 		: float(shipping['total']),
								'line_product_uom_qty'  : 1,
								'line_product_id'		: shipping_rec.store_id,
								'line_taxes'			: tax,
								'line_source'			: 'delivery',
				}
				shipping_list.append((0,0,shipping_line))
		return shipping_list

	@api.multi
	def create_woocommerce_shipping(self):
		data = {
				'name'		:"shipping",
				'store_id'	:"sh",
				'channel_id':self.id,
				'type'		:'service'
		}
		product_rec = self.env['product.feed'].create(data)
		feed_res = dict(create_ids=[product_rec],update_ids=[])
		self.env['channel.operation'].post_feed_import_process(self,feed_res)
		return product_rec


	@api.multi
	def get_woocommerce_taxes(self,data):
		l = []
		if data:
			for taxes in data:
				if 'total' in taxes:
					if taxes['total']:
						if float(taxes['total'])>0:
							l.append({'id':taxes['id']})
		return l

	@api.multi
	def get_woocommerce_order_line(self, data):
		order_lines = []
		variant = 0
		for line in data:
			if not  self.env['channel.template.mappings'].search([('store_product_id','=',line['product_id']),('channel_id.id','=',self.id)]):
				self.import_woocommerce_products_id(line['product_id'])
			product_template_id = self.env['channel.product.mappings'].search([('store_variant_id','=',line['variation_id']),('channel_id.id','=',self.id)])
			if not product_template_id:
				product_template_id = self.env['channel.product.mappings'].search([('store_product_id','=',line['product_id']),('channel_id.id','=',self.id)])
			order_line_dict = {
					'line_name'				:line['name'],
					'line_price_unit'		:line['price'],
					'line_product_uom_qty'	:line['quantity'],
					'line_product_id'		:product_template_id.store_product_id,
					'line_variant_ids'		:product_template_id.store_variant_id,
					'line_taxes'			:self.get_woocommerce_taxes(line['taxes'])
			}
			order_lines.append((0,0,order_line_dict))
		return order_lines

	@api.multi
	def import_woocommerce_orders(self):
		self.import_woocommerce_attribute()
		self.import_woocommerce_categories()
		woocommerce = self.get_woocommerce_connection()
		message = ''
		self.woc_check_and_create_tax(woocommerce)
		list_order = []
		count = 0
		context = dict(self._context)
		order_feed_data = self.env['order.feed']
		date = self.with_context({'name':'order'}).get_woocommerce_import_date()
		if not date:
			raise UserError(_("Please set date in multi channel configuration"))
		try:
			i=1
			while(i):
				order_data = woocommerce.get('orders?page='+str(i)+'&after='+date).json()
				if 'errors' in order_data:
					raise UserError(_("Error : "+str(order_data['errors'][0]['message'])))
				else :
					if order_data:
						i=i+1
						for order in order_data:
							_logger.info("===============================>%r",order['id'])
							if not order_feed_data.search([('store_id','=',order['id']),('channel_id.id','=',self.id)]):
								count = count + 1
								if order['id']:
									woocommerce2 = woocommerce
									if woocommerce2:
										order_data = woocommerce2.get("orders/"+str(order['id'])).json()
										data = order_data['line_items']
										order_lines = self.get_woocommerce_order_line(data)
										if order['shipping_lines']:
											order_lines += self.create_or_get_woocommerce_shipping(order_data['shipping_lines'])
								customer ={}
								if order['customer_id']:
									customer = woocommerce.get('customers/'+str(order['customer_id'])).json()
								else:
									customer.update({'first_name':order['billing']['first_name'],'last_name':order['billing']['last_name'],'email':order['billing']['email'] })
								_logger.info("===================>%r",[order['billing'],order['shipping'],customer,order])
								method_title ='Delivery'
								if order['shipping_lines']:
									method_title = order['shipping_lines'][0]['method_title']
								order_dict={
											'store_id'		 : order['id'],
											'channel_id'	 : self.id,
											'partner_id'	 : order['customer_id'] or order['billing']['email'],
											'payment_method' : order['payment_method_title'],
											'line_type'		 : 'multi',
											'carrier_id'	 : method_title,
											'line_ids'		 : order_lines,
											'currency'		 : order['currency'],
											'customer_name'  : customer['first_name'] +" "+customer['last_name'],
											'customer_email' : customer['email'],
											'order_state'	 : order['status'],
											}
								if order['billing']:
									order_dict.update({
													'invoice_partner_id': order['billing']['email'],
													'invoice_name'	   	: order['billing']['first_name']+" "+order['billing']['last_name'],
													'invoice_email'    	: order['billing']['email'],
													'invoice_phone'    	: order['billing']['phone'],
													'invoice_street'   	: order['billing']['address_1'],
													'invoice_street2'  	: order['billing']['address_2'],
													'invoice_zip'	   	: order['billing']['postcode'],
													'invoice_city'	   	: order['billing']['city'],
													'invoice_state_id' 	: order['billing']['state'],
													'invoice_country_id': order['billing']['country'],
													})
								if order['shipping']:
									order_dict['same_shipping_billing'] = False
									order_dict.update({
													'shipping_partner_id'   :order['billing']['email'],
													'shipping_name'	   		:order['shipping']['first_name']+" "+order['billing']['last_name'],
													'shipping_street'   	:order['shipping']['address_1'],
													'shipping_street2'  	:order['shipping']['address_2'],
													'shipping_email'		:order['billing']['email'],
													'shipping_zip'	   		:order['shipping']['postcode'],
													'shipping_city'	   		:order['shipping']['city'],
													'shipping_state_id' 	:order['shipping']['state'],
													'shipping_country_id'	:order['shipping']['country'],
													})
								order_rec = order_feed_data.with_context(context).create(order_dict)
								self._cr.commit()
								list_order.append(order_rec)
					else:
						i=0
			context.update({'group_by':'state',
						})
			list_order.reverse()
			feed_res = dict(create_ids=list_order,update_ids=[])
			self.env['channel.operation'].with_context(context).post_feed_import_process(self,feed_res)
			self.import_order_date = str(datetime.now().date())
			message +=  str(count)+" Order(s) Imported!"
			return self.display_message(message)
		except Exception as e:
			raise UserError(_("Error : "+str(e)))

	@api.multi
	def import_all_woocommerce_orders(self):
		self.import_woocommerce_attribute()
		self.import_woocommerce_categories()
		woocommerce = self.get_woocommerce_connection()
		message = ''
		self.woc_check_and_create_tax(woocommerce)
		list_order = []
		count = 0
		context = dict(self._context)
		order_feed_data = self.env['order.feed']
		pagination_info = self.pagination_info
		limit = self.api_record_limit
		if not pagination_info:
			pagination_info = {}
		else:
			pagination_info = eval(pagination_info)
		try:
			i=pagination_info.get("import_order_last_page",1)			
			while(i):
				url = 'orders?page='+str(i)
				if limit:
					url += '&per_page=%s'%(limit)
				order_data = woocommerce.get(url).json()
				if 'errors' in order_data:
					raise UserError(_("Error : "+str(order_data['errors'][0]['message'])))
				else :
					if order_data:
						i=i+1
						for order in order_data:
							_logger.info("===============================>%r",order['id'])
							if not order_feed_data.search([('store_id','=',order['id']),('channel_id.id','=',self.id)]):
								count = count + 1
								if order['id']:
									woocommerce2 = woocommerce
									if woocommerce2:
										order_data = woocommerce2.get("orders/"+str(order['id'])).json()
										data = order_data['line_items']
										order_lines = self.get_woocommerce_order_line(data)
										if order['shipping_lines']:
											order_lines += self.create_or_get_woocommerce_shipping(order_data['shipping_lines'])
								customer ={}
								if order['customer_id']:
									customer = woocommerce.get('customers/'+str(order['customer_id'])).json()
								else:
									customer.update({'first_name':order['billing']['first_name'],'last_name':order['billing']['last_name'],'email':order['billing']['email'] })
								_logger.info("===================>%r",[order['billing'],order['shipping'],customer,order])
								method_title ='Delivery'
								if order['shipping_lines']:
									method_title = order['shipping_lines'][0]['method_title']
								order_dict={
											'store_id'		 : order['id'],
											'channel_id'	 : self.id,
											'partner_id'	 : order['customer_id'] or order['billing']['email'],
											'payment_method' : order['payment_method_title'],
											'line_type'		 : 'multi',
											'carrier_id'	 : method_title,
											'line_ids'		 : order_lines,
											'currency'		 : order['currency'],
											'customer_name'  : customer['first_name'] +" "+customer['last_name'],
											'customer_email' : customer['email'],
											'order_state'	 : order['status'],
											}
								if order['billing']:
									order_dict.update({
													'invoice_partner_id': order['billing']['email'],
													'invoice_name'	   	: order['billing']['first_name']+" "+order['billing']['last_name'],
													'invoice_email'    	: order['billing']['email'],
													'invoice_phone'    	: order['billing']['phone'],
													'invoice_street'   	: order['billing']['address_1'],
													'invoice_street2'  	: order['billing']['address_2'],
													'invoice_zip'	   	: order['billing']['postcode'],
													'invoice_city'	   	: order['billing']['city'],
													'invoice_state_id' 	: order['billing']['state'],
													'invoice_country_id': order['billing']['country'],
													})
								if order['shipping']:
									order_dict['same_shipping_billing'] = False
									order_dict.update({
													'shipping_partner_id'   :order['billing']['email'],
													'shipping_name'	   		:order['shipping']['first_name']+" "+order['billing']['last_name'],
													'shipping_street'   	:order['shipping']['address_1'],
													'shipping_street2'  	:order['shipping']['address_2'],
													'shipping_email'		:order['billing']['email'],
													'shipping_zip'	   		:order['shipping']['postcode'],
													'shipping_city'	   		:order['shipping']['city'],
													'shipping_state_id' 	:order['shipping']['state'],
													'shipping_country_id'	:order['shipping']['country'],
													})
								order_rec = order_feed_data.with_context(context).create(order_dict)
								self._cr.commit()
								list_order.append(order_rec)
								list_order.reverse()
								if limit:
									feed_res = dict(create_ids=list_order,update_ids=[])
									self.env['channel.operation'].post_feed_import_process(self,feed_res)
								pagination_info["import_order_last_page"] = i
								self.write({
									"pagination_info":pagination_info
								})
								self._cr.commit()
					else:
						i=0
						pagination_info["import_order_last_page"] = 1
						self.write({
							"pagination_info":pagination_info
						})
						self._cr.commit()
			context.update({'group_by':'state',
						})
			self.import_order_date = str(datetime.now().date())
			message +=  str(count)+" Order(s) Imported!"
			return self.display_message(message)
		except Exception as e:
			raise UserError(_("Error : "+str(e)))
