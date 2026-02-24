INSERT INTO sqltemplate (name, description, sql_text, phase, is_active)
VALUES
(
  'lot_defect_trend_last_2days',
  '최근 2일 LOT별 불량 건수/추세',
  '
  SELECT
    lot_id,
    defect_code,
    date_trunc(''hour'', event_time) AS hour_bucket,
    count(*) AS defect_count
  FROM production_events
  WHERE event_time >= now() - interval ''2 day''
    AND (:lot_id IS NULL OR lot_id = :lot_id)
  GROUP BY lot_id, defect_code, date_trunc(''hour'', event_time)
  ORDER BY hour_bucket DESC
  LIMIT 200;
  ',
  1,
  true
),
(
  'top_defects_by_line_period',
  '기간/라인별 Top 불량코드',
  '
  SELECT
    line_id,
    defect_code,
    count(*) AS cnt
  FROM production_events
  WHERE event_time >= :start_time
    AND event_time < :end_time
    AND (:line_id IS NULL OR line_id = :line_id)
  GROUP BY line_id, defect_code
  ORDER BY cnt DESC
  LIMIT 20;
  ',
  1,
  true
);