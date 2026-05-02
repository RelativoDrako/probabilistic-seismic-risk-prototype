PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS region_features_new (
    feature_row_id TEXT PRIMARY KEY,
    feature_generation_id TEXT NOT NULL,
    feature_set_version TEXT NOT NULL,
    region_code TEXT NOT NULL,
    window_start_utc TEXT NOT NULL,
    window_end_utc TEXT NOT NULL,
    event_count INTEGER,
    max_magnitude REAL,
    mean_magnitude REAL,
    mean_depth_km REAL,
    days_since_last_event REAL,
    target_label REAL,
    created_at_utc TEXT,
    UNIQUE (
        feature_generation_id,
        region_code,
        window_start_utc,
        window_end_utc
    )
);

INSERT INTO region_features_new (
    feature_row_id,
    feature_generation_id,
    feature_set_version,
    region_code,
    window_start_utc,
    window_end_utc,
    event_count,
    max_magnitude,
    mean_magnitude,
    mean_depth_km,
    days_since_last_event,
    target_label,
    created_at_utc
)
SELECT
    feature_row_id,
    feature_generation_id,
    feature_set_version,
    region_code,
    window_start_utc,
    window_end_utc,
    event_count,
    max_magnitude,
    mean_magnitude,
    mean_depth_km,
    days_since_last_event,
    target_label,
    created_at_utc
FROM region_features;

DROP TABLE region_features;

ALTER TABLE region_features_new RENAME TO region_features;

COMMIT;

PRAGMA foreign_keys=ON;
