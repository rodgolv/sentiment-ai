CREATE SCHEMA IF NOT EXISTS reputacion_marca;

CREATE TABLE IF NOT EXISTS reputacion_marca.comentarios_analizados (
    id_mensaje STRING NOT NULL,
    timestamp_ingesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    texto_original STRING,
    sentimiento STRING,
    score_sentimiento FLOAT64,
    categoria STRING,
    resumen_gemini STRING,
    alerta_enviada BOOLEAN
);
