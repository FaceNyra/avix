# Contributing

1. Fork the repository and create a feature branch.
2. Install dependencies: `make install`.
3. Run quality checks: `make lint`, `make mypy`, `make test`.
4. Keep business logic in `application/` and out of Telegram handlers.
5. Add tests for new use cases.
6. Update README for user-facing changes.

## Adding a new use case

1. Define DTO in `application/dto/`.
2. Add repository methods to interfaces if needed.
3. Implement use case in `application/services/`.
4. Wire it through `bootstrap.Container`.
5. Expose via bot router or FastAPI endpoint.
6. Add unit tests.

## Adding a new subscription plan

1. Seed or create plan via admin API.
2. Update limits in `shared/plans.py` if it is a built-in plan.
3. Add payment payload validation if needed.
4. Document plan limits in README.
