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
import re
remove_tag = re.compile(r'<[^>]+>')
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')
class MultiChannelSale(models.Model):
	_inherit = "multi.channel.sale"

	@api.multi
	def create_woocommerce_variants(self,woocommerce,product_id,variation_ids):
		variant_list = []
		attribute_list = []
		image = False
		for variant_id in variation_ids:
			variant = woocommerce.get('products/'+str(product_id)+"/variations/"+str(variant_id)).json()
			if variant['attributes']:
				attribute_list = []
				for attributes in variant['attributes']:
					attrib_name_id = self.env['channel.attribute.mappings'].search([('store_attribute_name','=',attributes['name']),('store_attribute_id','=', attributes['id']),('channel_id.id','=',self.id)])
					attrib_value_id = self.env['channel.attribute.value.mappings'].search([('store_attribute_value_name','=',attributes['option']),('channel_id.id','=',self.id),('attribute_value_name.attribute_id.id','=',attrib_name_id.attribute_name.id)])[0]
					attr = {}
					attr['name']			=	str(attributes['name'])
					attr['value']			=	str(attributes['option'])
					attr['attrib_name_id']	= attrib_name_id.store_attribute_id
					attr['attrib_value_id'] = attrib_value_id.store_attribute_value_id
					attribute_list.append(attr)
					if isinstance(variant['image'],list):
						image = variant['images'][0]['src']
					else:
						image = variant['image']['src']
			try:
				variant['price']=float(variant['price'])
			except:
				pass
			variant_dict = {
							'image_url'  		: image,
							'name_value' 		: attribute_list,
							'store_id'			: variant['id'],
							'default_code'  	: variant['sku'],
							'list_price'		: variant['price'],
							'qty_available' 	: variant['stock_quantity'],
							'weight'			: variant['weight'] or "",
							# 'weight_unit'		: "kg",
							'length'			: variant['dimensions']['length'] or "",
							'width'				: variant['dimensions']['width'] or "",
							'height'			: variant['dimensions']['height'] or "",
							# 'dimension_unit'	: variant['dimensions']['unit'] or "",
					}
			variant_list.append((0,0,variant_dict))
		return variant_list

	@api.multi
	def import_woocommerce_attribute(self, woocommerce=False):
		attribute_list = []
		odoo_attribute_id = 0
		if not woocommerce:
			woocommerce  =  self.get_woocommerce_connection()
		multi_channel = self.env['multi.channel.sale']
		i=1
		while(i):
			try:
				attribute_data = woocommerce.get('products/attributes?page='+str(i)).json()
			except Exception as e:
				raise UserError(_("Error : "+str(e)))
			if 'message' in attribute_data:
				raise UserError(_("Error : "+str(attribute_data['message'])))
			else:
				if attribute_data:
					i = i+1
					for attribute in attribute_data:
						attribute_map = self.env['channel.attribute.mappings'].search([('store_attribute_id','=',attribute['id']),('channel_id.id','=',self.id)])
						if not attribute_map:
							product_attributes_obj = self.env['product.attribute']
							attribute_search_record = product_attributes_obj.search(['|',('name','=',attribute['name']), '|',('name','=',attribute['name'].lower()),'|',('name','=',attribute['name'].title()),('name','=',attribute['name'].upper())])
							if not attribute_search_record:
								odoo_attribute_id = product_attributes_obj.create({'name':attribute['name']})
							else:
								odoo_attribute_id = attribute_search_record
							attribute_list.append({
												'id'	: attribute['id'],
												'value'	: odoo_attribute_id.id,
												})
							mapping_dict = {
										'channel_id'		: self.id,
										'store_attribute_id': attribute['id'],
										'store_attribute_name': attribute['name'],
										'odoo_attribute_id'	: odoo_attribute_id.id,
										'attribute_name'	: odoo_attribute_id.id,
							}
							obj = self.env['channel.attribute.mappings']
							self._create_mapping(obj, mapping_dict)
							self._cr.commit()
					else:
						i=0
			attr_term = self.import_woocommerce_attribute_terms(attribute_list,woocommerce)
			self._cr.commit()
			if attr_term:
				return woocommerce
			else :
				return False


	@api.multi
	def import_woocommerce_attribute_terms(self,attribute_list=False, woocommerce=False):
		if not woocommerce:
			woocommerce = self.get_woocommerce_connection()
		multi_channel = self.env['multi.channel.sale']
		odoo_attribute_value_id = 0
		for attribute in attribute_list:
			i=1
			while(i):
				try:
					attribute_term_data = woocommerce.get('products/attributes/'+str(attribute['id'])+'/terms?page='+str(i)).json()
				except Exception as e:
					raise UserError(_("Error : "+str(e)))
				if 'message' in attribute_term_data:
					raise UserError(_("Error : "+str(attribute_term_data['message'])))
				else :
					if attribute_term_data:
						i = i+1
						for term in attribute_term_data:
							term_map = self.env['channel.attribute.value.mappings'].search([('store_attribute_value_id','=',term['id']),('channel_id.id','=',self.id)])
							if not term_map:
								product_attributes_value_obj = self.env['product.attribute.value']
								attribute_value_search_record = product_attributes_value_obj.search([
																					('attribute_id','=',attribute['value']),
																					'|',('name','=',term['name']),
																					'|',('name','=',term['name'].lower()),
																					'|',('name','=',term['name'].title()),
																						('name','=',term['name'].upper())
																					])
								if not attribute_value_search_record:
									odoo_attribute_value_id = product_attributes_value_obj.create({'name':term['name'],'attribute_id':attribute['value']})
								else:
									odoo_attribute_value_id = attribute_value_search_record
								mapping_dict = {
											'channel_id'				: self.id,
											'store_attribute_value_id'	: term['id'],
											'store_attribute_value_name': term['name'],
											'odoo_attribute_value_id'	: odoo_attribute_value_id.id,
											'attribute_value_name'		: odoo_attribute_value_id.id,
											'ecom_store'				: 'woocommerce',
								}
								obj = self.env['channel.attribute.value.mappings']
								self._create_mapping(obj, mapping_dict)
								self._cr.commit()
					else:
						i=0
		return True

	@api.multi
	def import_woocommerce_products(self):
		woocommerce = False
		message = ''
		woo_instance = self.import_woocommerce_attribute()
		if not woo_instance:
			raise UserError("Failed To Create Attribute Values")
		else:
			woocommerce = woo_instance
		if not woocommerce:
			woocommerce = self.get_woocommerce_connection()
		self.import_woocommerce_categories()
		list_product = []		
		count = 0
		list_product = []
		product = ''
		product_tmpl = self.env['product.feed']
		date = self.with_context({'name':'product'}).get_woocommerce_import_date()
		if not date:
			raise UserError(_("Please set date in multi channel configuration"))
		try:
			i=1
			while(i):
				product_data = woocommerce.get('products?after='+date+'&page='+str(i)).json()
				if 'errors' in product_data:
					raise UserError(_("Error : "+str(product_data['errors'][0]['message'])))
				else :
					if product_data:
						i = i+1
						for product in product_data:
							variants = []
							if not self.env['channel.template.mappings'].search([('store_product_id','=',product['id']),('channel_id.id','=',self.id)]):
								categ = ""
								if product['type'] == 'variable':
									variants = self.create_woocommerce_variants(woocommerce,product['id'], product['variations'])
								count = count + 1
								for category in product['categories']:
									category_id = self.env['channel.category.mappings'].search([('store_category_id','=',category['id']),('channel_id.id','=',self.id)])
									if category_id:
										categ = categ+str(category_id.store_category_id)+","
								try:
									product['price']=float(product['price'])
								except:
									pass
								product_feed_dict = {'name'				: product['name'],
												'store_id'				: product['id'],
												'default_code' 			: product['sku'],
												'list_price'			: product['price'],
												'channel_id'			: self.id,
												'description_sale'		: remove_tag.sub('',product['description']),
												'qty_available' 		: product['stock_quantity'],
												'feed_variants' 		: variants,
												'image_url'				: product['images'][0]['src'],
												'extra_categ_ids'		: categ or '',
												#'ecom_store'			: 'woocommerce',
												}
								if not product['type'] == 'variable':
									product_feed_dict.update({
												'weight'				: product['weight'] or "",
												# 'weight_unit'			: 'kg',
												'length'				: product['dimensions']['length'] or "",
												'width'					: product['dimensions']['width'] or "",
												'height'				: product['dimensions']['height'] or "",
												# 'dimension_unit'		: product['dimensions']['unit'] or "",
									})
								if product['downloadable'] == True or product['virtual'] == True:
									product_feed_dict.update({'type':'service'})
								product_rec = product_tmpl.create(product_feed_dict)
								self._cr.commit()
								list_product.append(product_rec)
					else:
						i=0

			feed_res = dict(create_ids=list_product,update_ids=[])
			self.env['channel.operation'].post_feed_import_process(self,feed_res)
			self.import_product_date = str(datetime.now().date())
			message += str(count)+" Product(s) Imported!"
			return self.display_message(message)
		except Exception as e:
			raise UserError(_("Error : "+str(e)))

	
	@api.multi
	def import_all_woocommerce_products(self):
		woocommerce = False
		message = ''
		woo_instance = self.import_woocommerce_attribute()
		if not woo_instance:
			raise UserError("Failed To Create Attribute Values")
		else:
			woocommerce = woo_instance
		if not woocommerce:
			woocommerce = self.get_woocommerce_connection()
		self.import_woocommerce_categories()
		pagination_info = self.pagination_info
		limit = self.api_record_limit
		if not pagination_info:
			pagination_info = {}
		else:
			pagination_info = eval(pagination_info)
		
		list_product = []		
		count = 0
		# date = self.with_context({'name':'product'}).get_woocommerce_import_date()
		product_tmpl = self.env['product.feed']
		try:
			i=pagination_info.get("import_product_last_page",1)
			while(i):
				url = 'products?page='+str(i)
				if limit:
					url += '&per_page=%s'%(limit)
				i += 1 
				product_data = woocommerce.get(url).json()
				if 'errors' in product_data:
					raise UserError(_("Error : "+str(product_data['errors'][0]['message'])))
				else :
					if product_data:
						i = i+1
						for product in product_data:
							variants = []
							if not self.env['channel.template.mappings'].search([('store_product_id','=',product['id']),('channel_id.id','=',self.id)]):
								categ = ""
								if product['type'] == 'variable':
									variants = self.create_woocommerce_variants(woocommerce,product['id'], product['variations'])
								count = count + 1
								for category in product['categories']:
									category_id = self.env['category.feed'].search([('name','=',category),('channel_id.id','=',self.id)])
									if category_id:
										categ = categ+str(category_id.store_id)+","
								try:
									product['price']=float(product['price'])
								except:
									pass
								product_feed_dict = {'name'				: product['name'],
												'store_id'				: product['id'],
												'default_code' 			: product['sku'],
												'list_price'			: product['price'],
												'channel_id'			: self.id,
												'description_sale'		: remove_tag.sub('',product['description']),
												'qty_available' 		: product['stock_quantity'],
												'feed_variants' 		: variants,
												'image_url'				: product['images'][0]['src'],
												'extra_categ_ids'		: categ,
												# 'ecom_store'			: 'woocommerce',
												}
								if not product['type'] == 'variable':
									product_feed_dict.update({
												'weight'				: product['weight'] or "",
												# 'weight_unit'			: 'kg',
												'length'				: product['dimensions']['length'] or "",
												'width'					: product['dimensions']['width'] or "",
												'height'				: product['dimensions']['height'] or "",
												# 'dimension_unit'		: product['dimensions']['unit'] or "",
									})
								if product['downloadable'] == True or product['virtual'] == True:
									product_feed_dict.update({'type':'service'})
								product_rec = product_tmpl.create(product_feed_dict)
								list_product.append(product_rec)
								if limit:
									feed_res = dict(create_ids=list_product,update_ids=[])
									self.env['channel.operation'].post_feed_import_process(self,feed_res)
								pagination_info["import_product_last_page"] = i
								self.write({
									"pagination_info":pagination_info
								})
								self._cr.commit()

					else:
						i=0
						pagination_info["import_product_last_page"] = 1
						self.write({
							"pagination_info":pagination_info
						})
						self._cr.commit()
			# self.import_product_date = str(datetime.now().date())
			message += str(count)+" Product(s) Imported!"
			return self.display_message(message)
		except Exception as e:
			raise UserError(_("Error : "+str(e)))
			
	@api.multi
	def import_woocommerce_products_id(self, id):
		message = ''
		woocommerce = self.get_woocommerce_connection()
		list_product = []
		product = ''
		product_tmpl = self.env['product.feed']
		try:
			product = woocommerce.get('products/'+str(id)).json()
		except Exception as e:
			raise UserError(_("Error : "+str(e)))
		if 'message' in product:
			raise UserError(_("Error : "+str(product['message'])))
		else :
			variants = []
			if not self.env['channel.template.mappings'].search([('store_product_id','=',product['id']),('channel_id.id','=',self.id)]):
				categ = ""
				if product['type'] == 'variable':
					variants = self.create_woocommerce_variants(woocommerce,product['id'], product['variations'])
				for category in product['categories']:
					category_id = self.env['category.feed'].search([('name','=',category),('channel_id.id','=',self.id)])
					if category_id:
						categ = categ+str(category_id.store_id)+","
				try:
					product['price']=float(product['price'])
				except:
					pass
				product_feed_dict = {'name'				: product['name'],
								'store_id'				: product['id'],
								'default_code' 			: product['sku'],
								'list_price'			: product['price'],
								'channel_id'			: self.id,
								'description_sale'		: remove_tag.sub('',product['description']),
								'qty_available' 		: product['stock_quantity'],
								'feed_variants' 		: variants,
								'image_url'				: product['images'][0]['src'],
								'extra_categ_ids'		: categ,
								# 'ecom_store'			: 'woocommerce',
								}
				if product['downloadable'] == True or product['virtual'] == True:
					product_feed_dict['type'] = 'service'
				if not product['type'] == 'variable':
					product_feed_dict.update({
								'weight'				: product['weight'] or "",
								'length'				: product['dimensions']['length'] or "",
								'width'					: product['dimensions']['width'] or "",
								'height'				: product['dimensions']['height'] or "",
								# 'dimension_unit'		: product['dimensions']['unit'] or "",
					})
				product_rec = product_tmpl.create(product_feed_dict)
				self._cr.commit()
				list_product.append(product_rec)
			feed_res = dict(create_ids=list_product,update_ids=[])
			self.env['channel.operation'].post_feed_import_process(self,feed_res)
			return True