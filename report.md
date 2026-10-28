# Harness report - salvatore-camila

Automated score: **70.0 / 70.0**

| Req | Title | Status | Points |
|---|---|---|---|
| R1 | Flight search latency | passed | 4.0/4 |
| R2 | No overselling under concurrency | passed | 10.0/10 |
| R3 | Reservation retrieval | passed | 3.0/3 |
| R4 | EMR job produces curated Parquet | passed | 8.0/8 |
| R5 | Glue Catalog tables per contract | passed | 6.0/6 |
| R6 | Athena correctness and partition pruning | passed | 8.0/8 |
| R7 | Analytics endpoint backed by Athena | passed | 8.0/8 |
| R8 | Customer flow in browser | passed | 6.0/6 |
| R9 | Manager panel matches endpoint | passed | 4.0/4 |
| R10 | No leftover EMR / bounded EMR hours | passed | 5.0/5 |
| R11 | Simple low-cost architecture | passed | 4.0/4 |
| R12 | Cost projection | passed | 4.0/4 |

## R1 Flight search latency - passed
- passed: `test_search_p95` 
- evidence: 100 requests, concurrency 20: p50=0.228s p95=0.317s

## R2 No overselling under concurrency - passed
- passed: `test_last_seat_exactly_one` 
- passed: `test_k_seats_exactly_k` 
- evidence: round 1: 201=1 409=49 other=0
- evidence: round 2: 201=1 409=49 other=0
- evidence: round 3: 201=1 409=49 other=0
- evidence: round 4: 201=1 409=49 other=0
- evidence: round 5: 201=1 409=49 other=0
- evidence: K=3 round 1: 201=3
- evidence: K=3 round 2: 201=3
- evidence: K=3 round 3: 201=3
- evidence: K=3 round 4: 201=3
- evidence: K=3 round 5: 201=3

## R3 Reservation retrieval - passed
- passed: `test_get_reservation` 
- passed: `test_unknown_reservation_404` 

## R4 EMR job produces curated Parquet - passed
- passed: `test_emr_run_completed` 
- passed: `test_parquet_written_by_emr` 
- passed: `test_cleaning_row_count_and_revenue` 
- evidence: 2 COMPLETED EMR step/job runs found
- evidence: 24/24 parquet files were written inside a COMPLETED EMR run window
- evidence: curated rows: expected 2017079, got 2017079

## R5 Glue Catalog tables per contract - passed
- passed: `test_detail_table_contract` 
- passed: `test_detail_partitions_registered` 
- passed: `test_metrics_table_contract` 

## R6 Athena correctness and partition pruning - passed
- passed: `test_top10_routes` 
- passed: `test_partition_pruning_scan` 
- evidence: top-10 routes and occupancies match the oracle within tolerance
- evidence: one-month query scanned 277952 B; limit 1367691 B (avg partition 683845 B)

## R7 Analytics endpoint backed by Athena - passed
- passed: `test_endpoint_matches_oracle_and_uses_athena` 
- passed: `test_endpoint_unknown_is_404` 
- evidence: SMR-ADZ 2024-05: ok in 1.36s
- evidence: BAQ-CUC 2023-07: ok in 1.47s
- evidence: SMR-ADZ 2023-01: ok in 1.25s
- evidence: BAQ-PSO 2023-05: ok in 1.21s
- evidence: BGA-BOG 2024-11: ok in 1.24s
- evidence: 10 Athena queries submitted during the probes

## R8 Customer flow in browser - passed
- passed: `test_search_reserve_confirm` 
- evidence: UI created reservation 9e295f7999944f748e742d44233d54ce for a flight; backend returns it

## R9 Manager panel matches endpoint - passed
- passed: `test_manager_panel_equals_endpoint` 
- evidence: PEI-CLO 2023-03: panel=0.8359 endpoint=0.8359 truth=0.8359

## R10 No leftover EMR / bounded EMR hours - passed
- passed: `test_no_running_emr` 
- passed: `test_emr_hours_cap` 
- evidence: active clusters=[] started serverless apps=0
- evidence: normalized instance hours used: 40.0 (cap 150)

## R11 Simple low-cost architecture - passed
- passed: `test_instance_classes` 
- passed: `test_no_nat_and_service_count` 
- evidence: billable services in use: ['Athena', 'EC2', 'EMR', 'Glue', 'Lambda', 'RDS', 'S3']
- WARNING: could not inspect: ['CloudFront'] (not counted)

## R12 Cost projection - passed
- passed: `test_projection_file` 
- passed: `test_projection_consistent_with_live` 
- evidence: declared total 34.48 USD/month; limit 50.00 (min of 1.5x reference 60.0 and budget 50.0)
- evidence: cost estimated from live resources: 40.47 {'RDS': 24.09, 'EC2': 15.18, 'EMR': 1.2, 'Athena': 0.0, 'S3': 0.0}
