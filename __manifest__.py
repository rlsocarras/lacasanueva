{
    'name': 'La Casa Nueva',
    'version': '18.0.1.0.1',
    'category': 'Inventory/Inventory',
    'summary': 'Modificar stock manualmente en productos para usuarios asociados',
    'description': """
        Módulo La Casa Nueva para Odoo 18
        =================================
        Este módulo permite:
        - Modificar el stock de productos manualmente
        - Sincronizar stock con la plantilla del sitio web
        - Restringir operación solo a usuarios asociados
        - Actualización directa desde la ficha del producto
    """,
    'author': 'La Casa Nueva',
    'website': 'https://www.lacasanueva.com',
    'depends': [
        'base',
        'mail',
        'stock',
        'product',
        'website_sale',
        'website_sale_stock',
        'purchase',
        'account',
        
    ],
    'data': [
        'security/la_casa_nueva_security.xml',  
        'security/ir.model.access.csv',
        #dashboard
        'views/finance_balance_views.xml',
        'views/res_users_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/website_templates.xml',
        'wizard/import_manual_stock_wizard_views.xml',
        'views/manual_stock_import_log_views.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'lacasanueva/static/src/js/finance_balance.js',
            'lacasanueva/static/src/xml/finance_balance.xml',
            'lacasanueva/static/src/css/manual_stock.css',
        ],
    },
    'demo': [],
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'

}