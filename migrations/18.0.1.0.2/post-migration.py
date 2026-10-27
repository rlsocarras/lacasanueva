# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("LACASANUEVA: Comprobando existencia de la columna 'gestionar_stock_manual' en res_users")

    cr.execute("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'res_users'
          AND column_name = 'gestionar_stock_manual'
    """)

    if cr.fetchone():
        _logger.info("LACASANUEVA: La columna 'gestionar_stock_manual' ya existe. No se crea.")
        return

    _logger.info("LACASANUEVA: La columna no existe. Creándola...")
    cr.execute("""
        ALTER TABLE res_users
        ADD COLUMN gestionar_stock_manual BOOLEAN DEFAULT FALSE
    """)
    cr.execute("""
        UPDATE res_users
        SET gestionar_stock_manual = FALSE
        WHERE gestionar_stock_manual IS NULL
    """)
    _logger.info("LACASANUEVA: Columna 'gestionar_stock_manual' creada correctamente.")
