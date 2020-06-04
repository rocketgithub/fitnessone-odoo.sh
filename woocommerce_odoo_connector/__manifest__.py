# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Woocommerce Odoo Connector",
  "summary"              :  "Woocommerce Odoo Connector integrates Odoo with Woocommerce. Manage your Woocommerce store in Odoo. Handle Woocommerce orders in Odoo.",
  "category"             :  "Website",
  "version"              :  "1.0.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Woocommerce-Odoo-Connector.html",
  "description"          :  """Woocommerce Odoo Connector
Odoo Woocommerce connector
Odoo Woocommerce bridge
Woocommerce bridge
Odoo Woocommerce
Connect Woocommerce with Odoo
Manage Woocommerce in Odoo
Woocommerce Odoo data transfer
Woocommerce store in Odoo
Integrate Odoo with Woocommerce
Integrate Woocommerce with Odoo
Woocommerce order in Odoo
Ecommerce website to Odoo
E-commerce website to Odoo
Connect ecommerce website
Ecommerce connector
E-commerce connector""",
  "live_test_url"        :  "http://wpodoo.webkul.com/woocommerce_odoo_connector/",
  "depends"              :  ['odoo_multi_channel_sale'],
  "data"                 :  [
                             'views/woc_config_views.xml',
                             'data/import_cron.xml',
                             'views/inherited_woocommerce_dashboard_view.xml',
                             'wizard/import_update_wizard.xml',
                             'data/default_data.xml',
                             'security/ir.model.access.csv',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  100,
  "currency"             :  "EUR",
  "external_dependencies":  {'python': ['woocommerce']},
}