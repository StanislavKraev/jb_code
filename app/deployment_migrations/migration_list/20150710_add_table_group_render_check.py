# -*- coding: utf-8 -*-
from fw.db.sql_base import db as sqldb


def forward(config, logger):
    logger.debug(u"Add table group_render_check")

    sqldb.session.close()
    sqldb.engine.execute(u"""CREATE TABLE group_render_check (
		id SERIAL NOT NULL,
		batch_id VARCHAR,
		event_data JSONB,
		doc_id_list VARCHAR[],
		created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
		check_completed BOOLEAN NOT NULL,
		PRIMARY KEY (id),
		FOREIGN KEY(batch_id) REFERENCES doc_batch (id)
	)""")


def rollback(config, logger):
    sqldb.session.close()
    sqldb.engine.execute("DROP table group_render_check;")

