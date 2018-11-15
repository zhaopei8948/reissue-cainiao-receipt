@echo off
title "reissue cainiao receipt"
set FLASK_APP=reissue_cainiao_receipt.py
set FLASK_DEBUG=1
flask run --host=127.0.0.1 --port 5003