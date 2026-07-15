import logging
import structlog


def start_log():
	structlog.configure(
		processors=[
			structlog.processors.AddLoggerName(),
			structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
			structlog.processors.JSONRenderer(),
		],
		context_class=dict,
		logger_factory=structlog.stdlib.LoggerFactory(),
		cache_logger_on_first_use=True,
	)
	return structlog.get_logger()