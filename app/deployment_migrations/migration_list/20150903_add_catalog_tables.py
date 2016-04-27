# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Create new models")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS okved_catalog (
    id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    departments JSONB,
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS okvad (
    id VARCHAR NOT NULL,
    caption VARCHAR NOT NULL,
    okved VARCHAR NOT NULL,
    nalog VARCHAR NOT NULL,
    parent VARCHAR,
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_okvad_okved;""")
    sqldb.engine.execute(u"""CREATE UNIQUE INDEX ix_okvad_okved ON okvad (okved);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS geo_ranges (
    start BIGINT NOT NULL,
    "end" BIGINT NOT NULL,
    cid SERIAL NOT NULL,
    PRIMARY KEY (cid),
    UNIQUE (cid)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS geo_cities (
    name VARCHAR NOT NULL,
    cid SERIAL NOT NULL,
    region VARCHAR NOT NULL,
    lat VARCHAR NOT NULL,
    lng VARCHAR NOT NULL,
    PRIMARY KEY (cid),
    UNIQUE (cid)
);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS notarius (
    id VARCHAR NOT NULL, 
    surname VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    patronymic VARCHAR, 
    schedule JSONB NOT NULL, 
    schedule_caption VARCHAR, 
    title VARCHAR, 
    address JSONB, 
    region VARCHAR NOT NULL, 
    metro_station VARCHAR, 
    PRIMARY KEY (id)
);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS notarius_booking (
    id VARCHAR NOT NULL, 
    batch_id VARCHAR, 
    owner_id INTEGER, 
    notarius_id VARCHAR, 
    dt TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    address VARCHAR NOT NULL, 
    _discarded BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id), 
    FOREIGN KEY(owner_id) REFERENCES authuser (id), 
    FOREIGN KEY(notarius_id) REFERENCES notarius (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_notarius_booking_owner_id;""")
    sqldb.engine.execute(u"CREATE INDEX ix_notarius_booking_owner_id ON notarius_booking (owner_id);")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_notarius_booking_notarius_id;""")
    sqldb.engine.execute(u"CREATE INDEX ix_notarius_booking_notarius_id ON notarius_booking (notarius_id);")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS yurist_batch_check (
    id VARCHAR NOT NULL, 
    batch_id VARCHAR, 
    status VARCHAR NOT NULL, 
    create_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    typos_correction BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id)
);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS yurist_check_files (
    "check_id" VARCHAR NOT NULL,
    files_id VARCHAR NOT NULL,
    PRIMARY KEY ("check_id", files_id),
    FOREIGN KEY("check_id") REFERENCES yurist_batch_check (id),
    FOREIGN KEY(files_id) REFERENCES files (id)
);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS ifns_catalog (
    id VARCHAR NOT NULL, 
    updated TIMESTAMP WITHOUT TIME ZONE, 
    code INTEGER NOT NULL, 
    comment VARCHAR, 
    tel TEXT[],
    name VARCHAR, 
    rof JSONB, 
    rou JSONB, 
    plat JSONB, 
    address VARCHAR, 
    region VARCHAR, 
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_ifns_catalog_code;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_ifns_catalog_code ON ifns_catalog (code);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_ifns_catalog_region;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_ifns_catalog_region ON ifns_catalog (region);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS ifns_booking (
    id VARCHAR NOT NULL, 
    batch_id VARCHAR, 
    code VARCHAR NOT NULL, 
    date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    service VARCHAR NOT NULL, 
    _discarded BOOLEAN, 
    phone VARCHAR, 
    "window" VARCHAR, 
    address VARCHAR, 
    service_id INTEGER NOT NULL, 
    ifns VARCHAR, 
    how_to_get VARCHAR, 
    reg_info JSONB, 
    PRIMARY KEY (id), 
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_ifns_booking_code;""")
    sqldb.engine.execute(u"CREATE INDEX ix_ifns_booking_code ON ifns_booking (code);")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS stamp_partners (
    id VARCHAR NOT NULL, 
    region TEXT[],
    enabled BOOLEAN, 
    sort_index INTEGER NOT NULL, 
    link VARCHAR, 
    banner VARCHAR NOT NULL, 
    title VARCHAR NOT NULL, 
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS bank_partners (
    id VARCHAR NOT NULL, 
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    link VARCHAR, 
    title VARCHAR NOT NULL, 
    banner VARCHAR NOT NULL, 
    enabled BOOLEAN, 
    sort_index INTEGER NOT NULL, 
    region TEXT[],
    city TEXT[],
    conditions TEXT[],
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS accountant_partners (
    id VARCHAR NOT NULL, 
    type VARCHAR NOT NULL, 
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    link VARCHAR, 
    title VARCHAR NOT NULL, 
    banner VARCHAR NOT NULL, 
    enabled BOOLEAN, 
    sort_index INTEGER NOT NULL, 
    region TEXT[],
    city TEXT[],
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS bank_partners_service (
    id VARCHAR NOT NULL, 
    type VARCHAR NOT NULL, 
    fields JSONB, 
    email VARCHAR, 
    template_name VARCHAR, 
    config JSONB, 
    bank_partner_id VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_partner_id) REFERENCES bank_partners (id)
);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS bank_partners_request (
    id SERIAL NOT NULL, 
    bank_partner_id VARCHAR NOT NULL, 
    batch_id VARCHAR NOT NULL, 
    bank_partner_caption VARCHAR, 
    sent_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    status VARCHAR NOT NULL, 
    bank_contact_phone_general_manager VARCHAR, 
    bank_contact_phone VARCHAR, 
    send_private_data BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_partner_id) REFERENCES bank_partners (id), 
    FOREIGN KEY(batch_id) REFERENCES doc_batch (id)
);""")
    
    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS payment_subscription (
    id SERIAL NOT NULL, 
    pay_info JSONB NOT NULL, 
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    end_dt TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    type VARCHAR NOT NULL, 
    user_id INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES authuser (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_payment_subscription_user_id;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_payment_subscription_user_id ON payment_subscription (user_id);""")

    sqldb.engine.execute(u"""CREATE TABLE IF NOT EXISTS yad_requests (
    id SERIAL NOT NULL, 
    ip VARCHAR NOT NULL, 
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    request_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    md5 VARCHAR NOT NULL, 
    shop_id BIGINT NOT NULL,
    shop_article_id BIGINT NOT NULL,
    invoice_id BIGINT NOT NULL,
    order_number VARCHAR NOT NULL, 
    customer_number VARCHAR NOT NULL, 
    order_created_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    order_sum_amount DECIMAL NOT NULL, 
    order_sum_currency_paycash VARCHAR NOT NULL, 
    order_sum_bank_paycash VARCHAR NOT NULL, 
    shop_sum_amount DECIMAL NOT NULL, 
    shop_sum_currency_paycash VARCHAR NOT NULL, 
    shop_sum_bank_paycash VARCHAR NOT NULL, 
    payment_payer_code VARCHAR NOT NULL, 
    payment_type VARCHAR NOT NULL, 
    action VARCHAR NOT NULL, 
    payment_datetime TIMESTAMP WITHOUT TIME ZONE, 
    cps_user_country_code VARCHAR, 
    PRIMARY KEY (id)
);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_yad_requests_order_number;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_yad_requests_order_number ON yad_requests (order_number);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_yad_requests_invoice_id;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_yad_requests_invoice_id ON yad_requests (invoice_id);""")

    sqldb.engine.execute(u"""DROP INDEX IF EXISTS ix_yad_requests_customer_number;""")
    sqldb.engine.execute(u"""CREATE INDEX ix_yad_requests_customer_number ON yad_requests (customer_number);""")


def rollback(config, logger):
    pass
