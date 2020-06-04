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
	def get_channel(self):
		res = super(MultiChannelSale, self).get_channel()
		res.append(('woocommerce', "WooCommerce"))
		return res


	url=fields.Char(string="Url", help='eg. http://xyz.com')
	consumer_key=fields.Char(
		string='Consumer Key',
		help='eg. ck_ccac94fc4362ba12a2045086ea9db285e8f02ac9',
		)
	secret_key = fields.Char(string='Secret Key',
		 help='eg. cs_a4c0092684bf08cf7a83606b44c82a6e0d8a4cae'
		 )
	pagination_info = fields.Char("Api Pagination")

	@api.multi
	def stripTime(self, date_str ):
		if not date_str:
			return False, False
		if not isinstance(date_str,str):
			date_str = str(date_str)
		date_str = date_str.split()
		_logger.info("======>%r",date_str[1])
		return date_str[0],date_str[1]

	@api.multi
	def get_woocommerce_import_date(self):
		date=''
		if 'name' in self._context:
			if self._context['name'] == 'product':
				date_str,time = self.stripTime(self.import_product_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			elif self._context['name'] == 'order':
				date_str,time = self.stripTime(self.import_order_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			elif self._context['name'] == 'customer':
				date_str,time = self.stripTime(self.import_customer_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			else:
				raise UserError(_('Context Empty'))
		date = date-timedelta(days=1)
		return str(date)+"T"+str(time)

	@api.multi
	def get_woocommerce_update_date(self):
		date=''
		if 'name' in self._context:
			if self._context['name'] == 'product':
				date_str,time = self.stripTime(self.update_product_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			elif self._context['name'] == 'order':
				date_str,time = self.stripTime(self.update_order_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			elif self._context['name'] == 'customer':
				date_str,time = self.stripTime(self.update_customer_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			elif self._context['name'] == 'category':
				date_str,time = self.stripTime(self.update_product_date)
				if not date_str:
					return False
				date=datetime.strptime(date_str,'%Y-%m-%d').date()
			else:
				raise UserError(_('Context Empty'))
		date = date-timedelta(days=1)
		date = str(date)
		return date +"T"+str(time)


	@api.multi
	def test_woocommerce_connection(self):
		message=""
		woocommerce = API(
			url 			=	self.url,
			consumer_key	=	self.consumer_key,
			consumer_secret	=	self.secret_key,
			wp_api			=	True,
			version			=	"wc/v2",
			timeout			=	30,
			query_string_auth=True,
			# verify_ssl		=	False,
		)
		try:
			woocommerce_api=woocommerce.get('system_status')
		except Exception as e:
			raise UserError(_("Error:"+str(e)))
		if  'message' in woocommerce_api.json():
			message = "Connection Error"+str(woocommerce_api.status_code)+" : "+str(woocommerce_api.text)
			raise UserError(_(message))
		else:
			self.state 	=	'validate'
			message		=	"Connection Successful!!"
		return self.display_message(message)

	@api.multi
	def get_woocommerce_connection(self):
		woocommerce = API(
			url 			=	self.url,
			consumer_key	=	self.consumer_key,
			consumer_secret	=	self.secret_key,
			wp_api			=	True,
			version			=	"wc/v2",
			timeout			=	30,
			query_string_auth=True,
			# verify_ssl		=	False,
		)
		try:
			woocommerce_api=woocommerce.get('system_status')
		except Exception as e:
			raise UserError(_("Error:"+str(e)))
		if  'message' in woocommerce_api.json():
			message = "Connection Error"+str(woocommerce_api.status_code)+" : "+str(woocommerce_api.text)
			raise UserError(_(message))
		else:
			return woocommerce

	# @api.multi
	# def woocommerce_export_api_config(self):
	# 	woocommerce = API(
	# 		url 			=	self.url,
	# 		consumer_key	=	self.consumer_key,
	# 		consumer_secret	=	self.secret_key,
	# 		wp_api			=	True,
	# 		version			=	"wc/v2",
	# 		timeout			=	30,
	# 		query_string_auth=True,
	# 		# verify_ssl		=	False,
	# 	)
	# 	try:
	# 		woocommerce_api=woocommerce.get('system_status')
	# 	except Exception as e:
	# 		raise UserError(_("Error:"+str(e)))
	# 	if  'message' in woocommerce_api.json():
	# 		message = "Connection Error"+str(woocommerce_api.status_code)+" : "+str(woocommerce_api.text)
	# 		raise UserError(_(message))
	# 	else:
	# 		return woocommerce

	@api.multi
	def update_woocommerce_quantity(self, woocommerce, quantity, product_map_rec):
		if woocommerce and product_map_rec:
			if product_map_rec.store_variant_id == 'No Variants':
				product_dict = woocommerce.get('products/'+str(product_map_rec.store_product_id)).json()
				if "bundle_layout" in product_dict:
					product_dict.pop("bundle_layout")
				if product_dict['stock_quantity'] is None:
					product_dict['stock_quantity'] = 0
				quantity = int(product_dict['stock_quantity']+quantity) #changes
				product_dict.update({
									'stock_quantity': quantity,
				})
				try:
					return_dict = woocommerce.put('products/'+str(product_map_rec.store_product_id),product_dict).json()
					if 'message' in return_dict:
						raise UserError(_("Can't update product stock , "+str(return_dict['message'])))
				except Exception as e:
					raise UserError(_("Can't update product stock, "+str(e)))
			else:
				variant_dict = woocommerce.get('products/'+str(product_map_rec.store_product_id)+"/variations/"+product_map_rec.store_variant_id).json()
				if variant_dict['stock_quantity'] is None:
    					variant_dict['stock_quantity'] = 0
				quantity = int(variant_dict['stock_quantity']+quantity)
				variant_dict.update({
									'stock_quantity': quantity,
				})
				try:
					return_dict = woocommerce.put('products/'+str(product_map_rec.store_product_id)+"/variations/"+product_map_rec.store_variant_id,variant_dict).json()
					if 'message' in return_dict:
						raise UserError(_("Can't update product stock , "+str(return_dict['message'])))
				except Exception as e:
					raise UserError(_("Can't update product stock, "+str(e)))
		return True

	@api.multi
	def woocommerce_post_do_transfer(self, stock_picking, mapping_ids, result):
		order_status = self.order_state_ids.filtered('odoo_ship_order')[0]
		status = order_status.channel_state
		woocommerce_order_id = mapping_ids.store_order_id
		wcapi = self.get_woocommerce_connection()
		data = wcapi.get('orders/'+woocommerce_order_id).json()
		data.update({'status':status})
		msg = wcapi.put('orders/'+woocommerce_order_id,data)

	@api.multi
	def woocommerce_post_confirm_paid(self, invoice, mapping_ids, result):
		order_status = self.order_state_ids.filtered(lambda state:state.odoo_set_invoice_state=='paid')[0]
		status = order_status.channel_state
		woocommerce_order_id = mapping_ids.store_order_id
		wcapi = self.get_woocommerce_connection()
		data = wcapi.get('orders/'+woocommerce_order_id).json()
		data.update({'status':status})
		msg = wcapi.put('orders/'+woocommerce_order_id,data)

############################CRON FUNCTIONS##################################################-
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@---Export--@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-
	# @api.model
	# def export_woocommerce_product_cron(self):
	# 	all_channel = self.env['multi.channel.sale'].search([('channel','=','woocommerce')])
	# 	for channel in all_channel:
	# 		if channel.sudo().woocommerce_is_export:
	# 			channel.sudo().export_woocommerce_product()
	# return True

	# @api.model
	# def export_woocommerce_category_cron(self):
	# 	all_channel = self.env['multi.channel.sale'].search([('channel','=','woocommerce')])
	# 	for channel in all_channel:
	# 		if channel.woocommerce_is_export:
	# 			channel.export_woocommerce_category()
	# 	return True

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@---Import--@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-
	@api.model
	def import_woocommerce_products_cron(self):
		all_channel = self.env['multi.channel.sale'].search([('channel','=','woocommerce')])
		for channel in all_channel:
			if channel.sudo().woocommerce_is_import:
				channel.sudo().import_all_woocommerce_products()
		return True

	@api.model
	def import_woocommerce_orders_cron(self):
		all_channel = self.env['multi.channel.sale'].search([('channel','=','woocommerce')])
		for channel in all_channel:
			if channel.woocommerce_is_import:
				try:
					channel.import_woocommerce_orders()
				except Exception as e:
					_logger.info("=====Order Evaluate Failed (WooCommerce)====(%r)====(%r)",channel,e)
					continue
		return True
	
	# @api.model
	# def import_woocommerce_orders_update_cron(self):
	# 	all_channel = self.env['multi.channel.sale'].search([('channel','=','woocommerce')])
	# 	for channel in all_channel:
	# 		if channel.woocommerce_is_import:
	# 			try:
	# 				channel.update_woocommerce_orders()
	# 			except Exception as e:
	# 				_logger.info("=====Order Update Failed (WooCommerce)====(%r)====(%r)",channel,e)
	# 				continue
	# 	return True


# class ProductFeed(models.Model):
# 	_inherit = "product.feed"

# 	@api.multi
# 	def import_product(self, channel_id):
# 		mapping_dict=super(ProductFeed, self).import_product(channel_id)
# 		mapping_id=mapping_dict.get('mapping_id')
# 		if mapping_id and channel_id.id in self.env['multi.channel.sale'].search([('channel','=','woocommerce')]):
# 			template_id=mapping_id.template_name
# 			template_id.type= template_id.name in ['shipping','voucher'] and 'service' or 'product'
# 			template_id.sale_ok = template_id.type in ['service'] and False or True
# 		return mapping_dict

class ProductTemplate(models.Model):
	_inherit = "product.template"

	@api.multi
	def write(self, vals):
		status = super(ProductTemplate, self).write(vals)
		for product_tmpl in self:
			if product_tmpl.channel_mapping_ids:
				for channel in product_tmpl.channel_mapping_ids:
					channel.need_sync = 'yes'
		return status

class ProductProduct(models.Model):
	_inherit = "product.product"
	@api.multi
	def write(self, vals):
		status = super(ProductProduct, self).write(vals)
		# product_tmpl_ids =self.mapped('product_tmpl_id.id')
		for product in self:
			template = product.product_tmpl_id
			if template.channel_mapping_ids:
				for channel in template.channel_mapping_ids:
					channel.need_sync = 'yes'
		return status


class ProductCategory(models.Model):
	_inherit = "product.category"

	@api.multi
	def write(self, vals):
		status = super(ProductCategory, self).write(vals)
		for product_categ in self:
			if product_categ.channel_mapping_ids:
				for channel in product_categ.channel_mapping_ids:
					channel.need_sync = 'yes'
		return status

class StockMove(models.Model):
	_inherit = 'stock.move'

	@api.multi
	def multichannel_sync_quantity(self, pick_details):
		channel_obj = self.env['multi.channel.sale']
		for channel in pick_details['channel_ids']:
			channel_rec = channel_obj.browse(channel)
			if channel_rec.channel == 'woocommerce' and channel_rec.auto_sync_stock:
				product_record = channel_rec.env['channel.product.mappings'].search([('erp_product_id','=',pick_details['product_id']),('channel_id.id','=',channel_rec.id)])
				if product_record:
					woocommerce = channel_rec.get_woocommerce_connection()
					if channel_rec.location_id.id != pick_details['source_loc_id']:
						channel_rec.update_woocommerce_quantity(woocommerce, pick_details['product_qty'], product_record)
					else:
						channel_rec.update_woocommerce_quantity(woocommerce,-(pick_details['product_qty']), product_record)
		return super(StockMove, self).multichannel_sync_quantity(pick_details)
