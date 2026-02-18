# Self-Healing Systems Lab

A deterministic, local-first lab for demonstrating code and runtime self-healing.

## Commands

- `make setup` - create local venv and install dependencies
- `make test` - run the baseline test suite
- `make demo-code` - inject bug, fail tests, heal code, verify pass, write artifacts
- `make demo-runtime` - simulate unhealthy runtime, watchdog restart + rollback, write runtime artifact
- `make demo` - run both demos in sequence
