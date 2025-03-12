poetry run python3 scripts/crawler/notice.py \
  --interval 30 \
  --delay 1 \
  --department "ALL" \
  --last-year 2020 \
  --rows 100

poetry run python3 scripts/crawler/notice.py \
  --interval 30 \
  --delay 1 \
  --department "정보컴퓨터공학부" \
  --last-year 2024 \
  --rows 100 \
  --reset \
  --parse-attachment
