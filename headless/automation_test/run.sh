#!/usr/bin/env bash
cd "$(dirname "$0")"
DIR="$(pwd)"

python3 -m pytest -s -v "${DIR}"/automation_main.py --workspace /tmp/ --boot1=/home/ryan/Desktop/nspire_investigation/ti_nspire_cx_ii_bootfiles/injected_btrom.img\(1\).tns --flash=/home/ryan/Desktop/nspire_investigation/ti_nspire_cx_ii_bootfiles/nspire_cx_ii_flash --os=/home/ryan/Desktop/nspire_investigation/6.3/TI-NspireCXII-6.3.0.119.tco2 --firebird-headless=/home/ryan/Desktop/nspire_investigation/firebird_naievil/headless/firebird-headless