#!/bin/sh
set -e
exec streamlit run /app/src/tradex/dashboard/app.py --server.address=0.0.0.0 --server.port=8501
