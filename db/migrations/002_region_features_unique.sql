PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

-- Crear nueva tabla con la nueva columna region_id
CREATE TABLE region_features_new (
    feature_row_id TEXT PRIMARY KEY,
    feature_generation_id TEXT NOT NULL,
    region_id TEXT NOT NULL,
    window_start_utc TEXT NOT NULL,
    window_end_utc TEXT NOT NULL,
    event_count INTEGER,
    avg_magnitude REAL,
    max_magnitude REAL,
    energy_sum REAL,
    created_at_utc TEXT NOT NULL,
    UNIQUE (
        feature_generation_id,
        region_id,
        window_start_utc,
        window_end_utc
    )
);

-- Migrar datos (asignando un valor por defecto a region_id)
INSERT INTO region_features_new (
    feature_row_id,
    feature_generation_id,
    region_id,
    window_start_utc,
    window_end_utc,
    event_count,
    avg_magnitude,
    max_magnitude,
    energy_sum,
    created_at_utc
)
SELECT
    feature_row_id,
    feature_generation_id,
    'default_region',
    window_start_utc,
    window_end_utc,
    event_count,
    avg_magnitude,
    max_magnitude,
    energy_sum,
    created_at_utc
FROM region_features;

-- Eliminar tabla vieja
DROP TABLE region_features;

-- Renombrar nueva tabla
ALTER TABLE region_features_new RENAME TO region_features;

COMMIT;

PRAGMA foreign_keys=ON;