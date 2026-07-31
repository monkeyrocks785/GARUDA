"""017 - Intelligence Rules & Alert Engine

Revision ID: 017_rules_engine
Revises: 016_growth_engine
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa

revision = "017_rules_engine"
down_revision = "016_growth_engine"


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            rule_type VARCHAR(50) NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            priority VARCHAR(20) DEFAULT 'medium',
            project_id VARCHAR(36),
            mission_id VARCHAR(36),
            tags_json TEXT,
            created_by VARCHAR(100),
            last_evaluated_at DATETIME,
            evaluation_count INTEGER DEFAULT 0,
            alert_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rules_name ON rules (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rules_rule_type ON rules (rule_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rules_enabled ON rules (enabled)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rules_project_id ON rules (project_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS rule_conditions (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            rule_id VARCHAR(36) NOT NULL,
            group_index INTEGER DEFAULT 0,
            parent_group_id VARCHAR(36),
            condition_type VARCHAR(50) NOT NULL,
            field VARCHAR(255) NOT NULL,
            operator VARCHAR(50) NOT NULL,
            value_json TEXT,
            logical_operator VARCHAR(10),
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rule_conditions_rule_id ON rule_conditions (rule_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS rule_actions (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            rule_id VARCHAR(36) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            config_json TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_rule_actions_rule_id ON rule_actions (rule_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            rule_id VARCHAR(36),
            rule_name VARCHAR(255) NOT NULL,
            rule_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(36),
            entity_name VARCHAR(255),
            project_id VARCHAR(36),
            mission_id VARCHAR(36),
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'new',
            title VARCHAR(500) NOT NULL,
            description TEXT,
            detail_json TEXT,
            geometry_json TEXT,
            centroid_x FLOAT,
            centroid_y FLOAT,
            assigned_to VARCHAR(100),
            acknowledged_at DATETIME,
            resolved_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_rule_id ON alerts (rule_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_rule_type ON alerts (rule_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_entity_id ON alerts (entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_project_id ON alerts (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_priority ON alerts (priority)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts (status)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            alert_id VARCHAR(36) NOT NULL,
            action VARCHAR(50) NOT NULL,
            actor VARCHAR(100),
            notes TEXT,
            previous_status VARCHAR(20),
            new_status VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_history_alert_id ON alert_history (alert_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_history_action ON alert_history (action)")


def downgrade() -> None:
    op.drop_table("alert_history")
    op.drop_table("alerts")
    op.drop_table("rule_actions")
    op.drop_table("rule_conditions")
    op.drop_table("rules")
