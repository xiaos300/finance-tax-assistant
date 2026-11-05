
CREATE TABLE harness.companies (
	company_id TEXT NOT NULL, 
	name TEXT NOT NULL, 
	short_name TEXT NOT NULL, 
	CONSTRAINT pk_companies PRIMARY KEY (company_id), 
	CONSTRAINT uq_companies_short_name UNIQUE (short_name)
)

;

CREATE TABLE harness.rules (
	rule_id TEXT NOT NULL, 
	version TEXT NOT NULL, 
	name TEXT NOT NULL, 
	topic TEXT NOT NULL, 
	effective_from DATE NOT NULL, 
	status TEXT NOT NULL, 
	body TEXT NOT NULL, 
	policy_json JSONB NOT NULL, 
	revision INTEGER DEFAULT '1' NOT NULL, 
	source_ref TEXT NOT NULL, 
	content_hash TEXT NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_rules PRIMARY KEY (rule_id, version), 
	CONSTRAINT ck_rules_policy_json_shape CHECK (jsonb_typeof(policy_json)='object'), 
	CONSTRAINT ck_rules_revision CHECK (revision>=1), 
	CONSTRAINT ck_rules_topic CHECK (topic IN ('amount','purpose','bank')), 
	CONSTRAINT ck_rules_status CHECK (status IN ('enabled','disabled'))
)

;

CREATE TABLE harness.seed_meta (
	dataset_id TEXT NOT NULL, 
	source_hashes_json JSONB NOT NULL, 
	normalized_hash TEXT NOT NULL, 
	schema_revision TEXT NOT NULL, 
	loaded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_seed_meta PRIMARY KEY (dataset_id), 
	CONSTRAINT ck_seed_meta_source_hashes_json_shape CHECK (jsonb_typeof(source_hashes_json)='object')
)

;

CREATE TABLE harness.users (
	user_id TEXT NOT NULL, 
	name TEXT NOT NULL, 
	memory_revision INTEGER DEFAULT '0' NOT NULL, 
	CONSTRAINT pk_users PRIMARY KEY (user_id), 
	CONSTRAINT ck_users_memory_revision CHECK (memory_revision>=0)
)

;

CREATE TABLE harness.bank_transactions (
	company_id TEXT NOT NULL, 
	transaction_id TEXT NOT NULL, 
	transaction_date DATE NOT NULL, 
	direction TEXT NOT NULL, 
	amount_cents BIGINT NOT NULL, 
	counterparty TEXT NOT NULL, 
	note TEXT, 
	CONSTRAINT pk_bank_transactions PRIMARY KEY (company_id, transaction_id), 
	CONSTRAINT fk_bank_transactions_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_bank_transactions_amount CHECK (amount_cents>0), 
	CONSTRAINT ck_bank_transactions_direction CHECK (direction IN ('income','expense'))
)

;

CREATE TABLE harness.invoices (
	company_id TEXT NOT NULL, 
	invoice_id TEXT NOT NULL, 
	invoice_date DATE NOT NULL, 
	seller TEXT NOT NULL, 
	item_name TEXT NOT NULL, 
	amount_cents BIGINT NOT NULL, 
	purpose TEXT, 
	note TEXT, 
	row_version INTEGER DEFAULT '1' NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_invoices PRIMARY KEY (company_id, invoice_id), 
	CONSTRAINT ck_invoices_row_version CHECK (row_version>=1), 
	CONSTRAINT fk_invoices_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_invoices_amount CHECK (amount_cents>=0)
)

;

CREATE TABLE harness.rule_companies (
	rule_id TEXT NOT NULL, 
	version TEXT NOT NULL, 
	company_id TEXT NOT NULL, 
	CONSTRAINT pk_rule_companies PRIMARY KEY (rule_id, version, company_id), 
	CONSTRAINT fk_rule_companies_rule_id_rules FOREIGN KEY(rule_id, version) REFERENCES harness.rules (rule_id, version) ON DELETE RESTRICT, 
	CONSTRAINT fk_rule_companies_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT
)

;

CREATE TABLE harness.user_company_permissions (
	user_id TEXT NOT NULL, 
	company_id TEXT NOT NULL, 
	can_read BOOLEAN NOT NULL, 
	can_write BOOLEAN NOT NULL, 
	CONSTRAINT pk_user_company_permissions PRIMARY KEY (user_id, company_id), 
	CONSTRAINT fk_user_company_permissions_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_user_company_permissions_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_user_company_permissions_write_requires_read CHECK (NOT can_write OR can_read)
)

;

CREATE TABLE harness.sessions (
	session_id TEXT NOT NULL, 
	user_id TEXT NOT NULL, 
	default_company_id TEXT, 
	result_focus_json JSONB, 
	row_version INTEGER DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_sessions PRIMARY KEY (session_id), 
	CONSTRAINT ck_sessions_row_version CHECK (row_version>=1), 
	CONSTRAINT fk_sessions_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_sessions_default_company_id_companies FOREIGN KEY(default_company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_sessions_user_id_user_company_permissions FOREIGN KEY(user_id, default_company_id) REFERENCES harness.user_company_permissions (user_id, company_id) ON DELETE RESTRICT
)

;

CREATE TABLE harness.turns (
	turn_id TEXT NOT NULL, 
	session_id TEXT NOT NULL, 
	request_hash TEXT NOT NULL, 
	status TEXT NOT NULL, 
	cancel_requested BOOLEAN DEFAULT 'false' NOT NULL, 
	session_version INTEGER NOT NULL, 
	scope_json JSONB, 
	scope_company_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	memory_revision INTEGER NOT NULL, 
	result_json JSONB, 
	error_code TEXT, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	CONSTRAINT pk_turns PRIMARY KEY (turn_id), 
	CONSTRAINT ck_turns_scope_company_ids_shape CHECK (jsonb_typeof(scope_company_ids)='array'), 
	CONSTRAINT fk_turns_session_id_sessions FOREIGN KEY(session_id) REFERENCES harness.sessions (session_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_turns_session_version CHECK (session_version>=1), 
	CONSTRAINT ck_turns_memory_revision CHECK (memory_revision>=0), 
	CONSTRAINT ck_turns_status CHECK (status IN ('running','completed','failed','interrupted','cancelled')), 
	CONSTRAINT ck_turns_finished CHECK ((status='running') = (finished_at IS NULL)), 
	CONSTRAINT ck_turns_result CHECK (status='running' OR result_json IS NOT NULL)
)

;

CREATE TABLE harness.evidence_events (
	event_id BIGINT GENERATED BY DEFAULT AS IDENTITY, 
	session_id TEXT, 
	turn_id TEXT, 
	user_id TEXT, 
	actor_label TEXT NOT NULL, 
	scope_company_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	kind TEXT NOT NULL, 
	correlation_id TEXT NOT NULL, 
	payload_json JSONB NOT NULL, 
	payload_hash TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_evidence_events PRIMARY KEY (event_id), 
	CONSTRAINT ck_evidence_events_scope_company_ids_shape CHECK (jsonb_typeof(scope_company_ids)='array'), 
	CONSTRAINT fk_evidence_events_session_id_sessions FOREIGN KEY(session_id) REFERENCES harness.sessions (session_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_evidence_events_turn_id_turns FOREIGN KEY(turn_id) REFERENCES harness.turns (turn_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_evidence_events_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT
)

;

CREATE TABLE harness.messages (
	message_id TEXT NOT NULL, 
	turn_id TEXT NOT NULL, 
	role TEXT NOT NULL, 
	content TEXT NOT NULL, 
	invoice_refs_json JSONB DEFAULT '[]'::jsonb NOT NULL, 
	memory_refs_json JSONB DEFAULT '[]'::jsonb NOT NULL, 
	scope_company_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_messages PRIMARY KEY (message_id), 
	CONSTRAINT ck_messages_invoice_refs_json_shape CHECK (jsonb_typeof(invoice_refs_json)='array'), 
	CONSTRAINT ck_messages_memory_refs_json_shape CHECK (jsonb_typeof(memory_refs_json)='array'), 
	CONSTRAINT ck_messages_scope_company_ids_shape CHECK (jsonb_typeof(scope_company_ids)='array'), 
	CONSTRAINT fk_messages_turn_id_turns FOREIGN KEY(turn_id) REFERENCES harness.turns (turn_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_messages_turn_id UNIQUE (turn_id, role), 
	CONSTRAINT ck_messages_role CHECK (role IN ('user','assistant')), 
	CONSTRAINT ck_messages_assistant_refs CHECK (role='user' OR invoice_refs_json='[]'::jsonb)
)

;

CREATE TABLE harness.preferences (
	preference_id TEXT NOT NULL, 
	user_id TEXT NOT NULL, 
	company_id TEXT NOT NULL, 
	preference_key TEXT NOT NULL, 
	content TEXT NOT NULL, 
	source_turn_id TEXT NOT NULL, 
	last_change_origin_json JSONB NOT NULL, 
	row_version INTEGER DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_preferences PRIMARY KEY (preference_id), 
	CONSTRAINT ck_preferences_last_change_origin_json_shape CHECK (jsonb_typeof(last_change_origin_json)='object'), 
	CONSTRAINT ck_preferences_row_version CHECK (row_version>=1), 
	CONSTRAINT fk_preferences_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_preferences_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_preferences_source_turn_id_turns FOREIGN KEY(source_turn_id) REFERENCES harness.turns (turn_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_preferences_user_id UNIQUE (user_id, company_id, preference_key)
)

;

CREATE TABLE harness.tasks (
	task_id TEXT NOT NULL, 
	user_id TEXT NOT NULL, 
	company_id TEXT NOT NULL, 
	goal TEXT NOT NULL, 
	business_month TEXT, 
	status TEXT NOT NULL, 
	progress_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
	row_version INTEGER DEFAULT '1' NOT NULL, 
	source_turn_id TEXT NOT NULL, 
	last_change_origin_json JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_tasks PRIMARY KEY (task_id), 
	CONSTRAINT ck_tasks_progress_json_shape CHECK (jsonb_typeof(progress_json)='object'), 
	CONSTRAINT ck_tasks_row_version CHECK (row_version>=1), 
	CONSTRAINT ck_tasks_last_change_origin_json_shape CHECK (jsonb_typeof(last_change_origin_json)='object'), 
	CONSTRAINT fk_tasks_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_tasks_company_id_companies FOREIGN KEY(company_id) REFERENCES harness.companies (company_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_tasks_source_turn_id_turns FOREIGN KEY(source_turn_id) REFERENCES harness.turns (turn_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_tasks_month CHECK (business_month IS NULL OR business_month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$' AND left(business_month,4)<>'0000'), 
	CONSTRAINT ck_tasks_status CHECK (status IN ('active','awaiting_input','verify_pending','completed','cancelled'))
)

;

CREATE TABLE harness.write_operations (
	operation_id TEXT NOT NULL, 
	turn_id TEXT NOT NULL, 
	user_id TEXT NOT NULL, 
	company_id TEXT NOT NULL, 
	invoice_id TEXT NOT NULL, 
	request_hash TEXT NOT NULL, 
	expected_row_version INTEGER NOT NULL, 
	authorization_json JSONB NOT NULL, 
	changes_json JSONB NOT NULL, 
	before_json JSONB NOT NULL, 
	after_json JSONB, 
	state TEXT NOT NULL, 
	error_code TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	committed_at TIMESTAMP WITH TIME ZONE, 
	verified_at TIMESTAMP WITH TIME ZONE, 
	CONSTRAINT pk_write_operations PRIMARY KEY (operation_id), 
	CONSTRAINT ck_write_operations_authorization_json_shape CHECK (jsonb_typeof(authorization_json)='object'), 
	CONSTRAINT ck_write_operations_changes_json_shape CHECK (jsonb_typeof(changes_json)='object'), 
	CONSTRAINT ck_write_operations_before_json_shape CHECK (jsonb_typeof(before_json)='object'), 
	CONSTRAINT fk_write_operations_turn_id_turns FOREIGN KEY(turn_id) REFERENCES harness.turns (turn_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_write_operations_user_id_users FOREIGN KEY(user_id) REFERENCES harness.users (user_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_write_operations_company_id_invoices FOREIGN KEY(company_id, invoice_id) REFERENCES harness.invoices (company_id, invoice_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_write_operations_turn_id UNIQUE (turn_id, company_id, invoice_id), 
	CONSTRAINT ck_write_operations_version CHECK (expected_row_version>=1), 
	CONSTRAINT ck_write_operations_state CHECK (state IN ('prepared','committed','verified','already_current','failed','verify_pending'))
)

;
CREATE INDEX ix_rules_topic_status_date ON harness.rules (topic, status, effective_from);
CREATE INDEX ix_bank_company_date_direction ON harness.bank_transactions (company_id, transaction_date, direction);
CREATE INDEX ix_invoices_company_date ON harness.invoices (company_id, invoice_date, invoice_id);
CREATE INDEX ix_rule_companies_company ON harness.rule_companies (company_id, rule_id, version);
CREATE INDEX ix_sessions_user_created ON harness.sessions (user_id, created_at, session_id);
CREATE INDEX ix_turns_session_started ON harness.turns (session_id, started_at, turn_id);
CREATE UNIQUE INDEX ux_turns_one_running ON harness.turns (session_id) WHERE status='running';
CREATE INDEX ix_evidence_session ON harness.evidence_events (session_id, event_id);
CREATE INDEX ix_evidence_turn ON harness.evidence_events (turn_id, event_id);
CREATE INDEX ix_evidence_user_created ON harness.evidence_events (user_id, created_at);
CREATE UNIQUE INDEX ux_preferences_one_default ON harness.preferences (user_id) WHERE preference_key='default_company';
CREATE INDEX ix_tasks_user_company_updated ON harness.tasks (user_id, company_id, updated_at);
CREATE UNIQUE INDEX ux_tasks_one_open ON harness.tasks (user_id, company_id) WHERE status IN ('active','awaiting_input','verify_pending');
CREATE INDEX ix_write_operations_invoice_created ON harness.write_operations (company_id, invoice_id, created_at);
CREATE INDEX ix_write_operations_user_created ON harness.write_operations (user_id, created_at);
