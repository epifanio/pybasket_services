#!/bin/sh
if [ -z "${PREFIX}" ]; then
    PREFIX_PARAM="";
else
    PREFIX_PARAM="--prefix ${PREFIX}";
fi
# ${LOG_LEVEL}
#bokeh serve --port ${PORT} --address 0.0.0.0 --allow-websocket-origin ${ORIGIN} ${PREFIX_PARAM} --log-level debug /pybasket_ui

# bokeh serve --port ${PORT} --address 0.0.0.0 --allow-websocket-origin '*' ${PREFIX_PARAM} --log-level debug /pybasket_ui /SIE /GISPY /TS-Plot

bokeh serve --port ${PORT} --address 0.0.0.0 --allow-websocket-origin ${ORIGIN} ${PREFIX_PARAM} --log-level debug /pybasket_ui /SIE /GISPY /TS-Plot
